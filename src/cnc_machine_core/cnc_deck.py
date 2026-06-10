"""Standard deck and labware utilities for CNC gantry systems.

Provides Well, Labware, and Deck objects for coordinate resolution.
Works with Opentrons-format labware JSON definitions.

Usage:
    from cnc_machine_core import Deck

    deck = Deck()                                    # default 4-slot deck
    deck = Deck("cnc_1_slot_deck")                   # built-in by name
    deck = Deck("path/to/custom_deck.json")          # custom path
    plate = deck.load_labware("1", "labware/my_labware.json")
    x, y, z = plate["A1"].position()                 # absolute CNC coordinates
    x, y, z = plate["A1"].position(offset={"x": 6.75, "y": -4.0})

    # Or use raw coordinates without any deck/labware:
    cnc.move_to_point_safe(100, 50, -10)
"""

import json
import os

_DECK_DIR = os.path.join(os.path.dirname(__file__), "deck")
DEFAULT_DECK = "cnc_4_slot_deck"


def _resolve_deck_path(deck_definition):
    """Resolve a deck argument to a JSON file path.

    Accepts: None (default deck), a built-in deck name (e.g. "cnc_4_slot_deck"),
    or a path to a custom JSON file.
    """
    if deck_definition is None:
        return os.path.join(_DECK_DIR, f"{DEFAULT_DECK}.json")
    if os.path.sep in deck_definition or deck_definition.endswith(".json"):
        return deck_definition
    return os.path.join(_DECK_DIR, f"{deck_definition}.json")


class Well:
    """A single well with absolute CNC coordinates."""

    def __init__(self, name, x, y, z, depth=0, diameter=0):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.depth = depth
        self.diameter = diameter

    def position(self, offset=None):
        """Return (x, y, z) absolute coordinates, with optional offset applied.

        Args:
            offset: Optional dict with x/y/z keys to add (e.g. tool offset).
        """
        x, y, z = self.x, self.y, self.z
        if offset:
            x += offset.get("x", 0)
            y += offset.get("y", 0)
            z += offset.get("z", 0)
        return x, y, z

    def __repr__(self):
        return f"Well({self.name}, x={self.x:.2f}, y={self.y:.2f}, z={self.z:.2f})"


class Labware:
    """A labware loaded onto a deck slot. Provides well access by name."""

    def __init__(self, definition, slot_position):
        self._definition = definition
        self._slot_position = slot_position
        corner = definition.get("cornerOffsetFromSlot", {"x": 0, "y": 0, "z": 0})
        self._wells = {}
        for well_name, well_data in definition.get("wells", {}).items():
            abs_x = slot_position[0] + corner["x"] + well_data["x"]
            abs_y = slot_position[1] + corner["y"] + well_data["y"]
            abs_z = slot_position[2] + corner["z"] + well_data["z"]
            self._wells[well_name] = Well(
                name=well_name,
                x=abs_x,
                y=abs_y,
                z=abs_z,
                depth=well_data.get("depth", 0),
                diameter=well_data.get("diameter", 0),
            )

    @property
    def name(self):
        return self._definition.get("metadata", {}).get("displayName", "unknown")

    @property
    def ordering(self):
        """Return the raw ordering array: [[col1_wells], [col2_wells], ...]."""
        return self._definition.get("ordering", [])

    def wells(self):
        """Return wells in ordering (column-major), or alphabetical if no ordering."""
        ordering = self._definition.get("ordering", [])
        if ordering:
            return [self._wells[name] for col in ordering for name in col if name in self._wells]
        return [self._wells[k] for k in sorted(self._wells)]

    def wells_by_name(self):
        """Return dict of well_name -> Well."""
        return dict(self._wells)

    def well_names(self):
        """Return ordered list of well name strings."""
        return [w.name for w in self.wells()]

    def __getitem__(self, well_name):
        """Access a well by name: labware["A1"]."""
        if well_name not in self._wells:
            raise KeyError(f"Well '{well_name}' not found in {self.name}")
        return self._wells[well_name]

    def __repr__(self):
        return f"Labware({self.name}, {len(self._wells)} wells)"


class Deck:
    """Standard CNC deck with slot-based labware management."""

    def __init__(self, deck_definition=None):
        path = _resolve_deck_path(deck_definition)
        with open(path, "r", encoding="utf-8") as f:
            self._deck = json.load(f)
        self._labware = {}  # slot_id (str) -> Labware

    def get_slot(self, slot_id):
        """Return the slot dict for a given slot ID."""
        for slot in self._deck["locations"]["slots"]:
            if slot["id"] == str(slot_id):
                return slot
        raise KeyError(f"Slot '{slot_id}' not found in deck definition")

    def list_slots(self):
        """Return list of all slot IDs."""
        return [s["id"] for s in self._deck["locations"]["slots"]]

    def load_labware(self, slot_id, labware_path):
        """Load an Opentrons-format labware JSON onto a deck slot.

        Returns a Labware object with wells resolved to absolute coordinates.
        """
        slot = self.get_slot(slot_id)
        with open(labware_path, "r", encoding="utf-8") as f:
            definition = json.load(f)
        labware = Labware(definition, slot["position"])
        self._labware[str(slot_id)] = labware
        return labware

    def load_labware_definition(self, slot_id, definition):
        """Load labware from a dict (e.g. from opentrons-shared-data).

        Returns a Labware object with wells resolved to absolute coordinates.
        """
        slot = self.get_slot(slot_id)
        labware = Labware(definition, slot["position"])
        self._labware[str(slot_id)] = labware
        return labware

    def get_labware(self, slot_id):
        """Return the Labware for a slot, or None."""
        return self._labware.get(str(slot_id))

    # --- Convenience methods (delegate to Labware) ---

    def list_wells(self, slot_id):
        """Return ordered list of well names for labware in a slot."""
        labware = self._labware.get(str(slot_id))
        if not labware:
            raise ValueError(f"No labware loaded in slot {slot_id}")
        return labware.well_names()

    def get_well_position(self, slot_id, well_name, tool_offset=None):
        """Resolve a well to absolute CNC coordinates.

        Returns (x, y, z) tuple. Convenience wrapper around Labware/Well API.
        """
        labware = self._labware.get(str(slot_id))
        if not labware:
            raise ValueError(f"No labware loaded in slot {slot_id}")
        return labware[well_name].position(offset=tool_offset)
