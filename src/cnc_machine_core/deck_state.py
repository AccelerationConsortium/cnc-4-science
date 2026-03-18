"""YAML-backed well status tracker for CNC deck slots.

Tracks per-well status strings across all deck slots. Statuses are
application-defined — the tracker itself is generic.

Usage:
    from deck_state import DeckState

    ds = DeckState()
    ds.init_wells_from_labware("1", plate)          # from Labware or raw dict
    ds.init_from_preset({"1": {"A1": "empty"}})     # from preset dict
    ds.set_status("1", "A1", "sample")              # update (auto-saves)
    loc = ds.find_next(["1", "2"], "empty")          # find first match
"""

import yaml
from pathlib import Path


class DeckState:
    """YAML-backed well status tracker for all deck slots."""

    def __init__(self, state_file=None):
        self.state_file = Path(state_file) if state_file else None
        self.slots = {}  # {slot_id: {well_name: status}}

    # --- Persistence ---

    def save(self, path=None):
        path = Path(path) if path else self.state_file
        if path is None:
            raise ValueError("No path specified for save")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(self.slots, f, default_flow_style=False)
        self.state_file = path

    def load(self, path=None):
        path = Path(path) if path else self.state_file
        if path is None:
            raise ValueError("No path specified for load")
        with path.open("r", encoding="utf-8") as f:
            self.slots = yaml.safe_load(f) or {}
        self.state_file = path

    @classmethod
    def from_file(cls, path):
        ds = cls(state_file=path)
        ds.load()
        return ds

    # --- Preset configuration ---

    def init_from_preset(self, preset):
        """Populate state from a preset dict.

        Args:
            preset: Dict mapping slot_id -> list of (well_name, status) or
                    slot_id -> {well_name: status}.
        """
        for slot_id, wells in preset.items():
            slot_key = str(slot_id)
            if slot_key not in self.slots:
                self.slots[slot_key] = {}
            if isinstance(wells, dict):
                for well, status in wells.items():
                    self.slots[slot_key][well] = status
            else:
                for well, status in wells:
                    self.slots[slot_key][well] = status

    def init_wells_from_labware(self, slot_id, labware_data,
                                default_status="empty"):
        """Initialize all wells in a slot from labware ordering.

        Args:
            labware_data: Either a raw labware dict (with "ordering" key)
                or a cnc_deck.Labware object (with .well_names() method).
        """
        slot_key = str(slot_id)
        if slot_key not in self.slots:
            self.slots[slot_key] = {}
        if hasattr(labware_data, "well_names"):
            well_list = labware_data.well_names()
        else:
            ordering = labware_data.get("ordering", [])
            well_list = [well for col in ordering for well in col]
        for well in well_list:
            if well not in self.slots[slot_key]:
                self.slots[slot_key][well] = default_status

    # --- Accessors ---

    def set_status(self, slot_id, well_name, status):
        slot_key = str(slot_id)
        if slot_key not in self.slots:
            self.slots[slot_key] = {}
        self.slots[slot_key][well_name] = status
        if self.state_file:
            self.save()

    def get_status(self, slot_id, well_name):
        return self.slots.get(str(slot_id), {}).get(well_name, "empty")

    def find_next(self, slot_ids, status, ordering_map=None):
        """Find the first well matching status across given slots.

        Iterates column-first using labware ordering if provided,
        otherwise dict insertion order.

        Args:
            slot_ids: List of slot IDs to search.
            status: Target well status to match.
            ordering_map: Optional dict mapping slot_id to
                labware ordering lists.

        Returns:
            (slot_id, well_name) or None.
        """
        for sid in slot_ids:
            slot_key = str(sid)
            wells = self.slots.get(slot_key, {})
            if ordering_map and slot_key in ordering_map:
                ordered = [
                    w for col in ordering_map[slot_key] for w in col
                ]
            else:
                ordered = list(wells.keys())
            for well in ordered:
                if wells.get(well) == status:
                    return (slot_key, well)
        return None

    def count(self, slot_ids, status):
        """Count wells with a given status across slots."""
        total = 0
        for sid in slot_ids:
            wells = self.slots.get(str(sid), {})
            total += sum(1 for s in wells.values() if s == status)
        return total

    def summary(self):
        """Print a compact summary of all slot states."""
        for slot_id in sorted(self.slots):
            wells = self.slots[slot_id]
            counts = {}
            for status in wells.values():
                counts[status] = counts.get(status, 0) + 1
            parts = [f"{s}={n}" for s, n in sorted(counts.items())]
            print(f"  Slot {slot_id}: {', '.join(parts)}")
