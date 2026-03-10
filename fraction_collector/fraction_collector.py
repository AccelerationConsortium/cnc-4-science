import json
import os

from fraction_collector.tools.vial_capper import VialCapper
from fraction_collector.tools.vacuum_gripper import VacuumGripper

TOOL_CLASSES = {
    "vial_capper": VialCapper,
    "vacuum_gripper": VacuumGripper,
}

try:
    from fraction_collector.tools.drop_counter import DropCounter

    TOOL_CLASSES["drop_counter"] = DropCounter
except ImportError:
    pass

DECK_DEF_PATH = os.path.join(
    os.path.dirname(__file__), "deck", "cnc_deck_definition.json"
)


class FractionCollector:
    """Orchestrates a CNC gantry with a deck, labware, and swappable tools.

    Coordinate resolution:
        absolute_pos = deck_slot_position + labware_well_position + tool_offset

    The deck has 4 slots (2x2). Each slot can hold one Opentrons-format
    labware definition. Tools are registered with x/y/z offsets from the
    toolhead datum.
    """

    def __init__(self, cnc_machine, deck_definition=None):
        """
        Args:
            cnc_machine: A CNC_Machine instance (from cnc_machine.py).
            deck_definition: Path to deck JSON. Defaults to built-in 4-slot deck.
        """
        self.cnc = cnc_machine
        self.deck = self._load_deck(deck_definition or DECK_DEF_PATH)
        self.slot_labware = {}  # slot_id -> labware dict
        self.tools = {}  # tool_id -> tool instance

    def _load_deck(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def get_slot(self, slot_id):
        """Return the slot dict for a given slot ID."""
        for slot in self.deck["locations"]["slots"]:
            if slot["id"] == str(slot_id):
                return slot
        raise KeyError(f"Slot '{slot_id}' not found in deck definition")

    # --- Labware ---

    def load_labware(self, slot_id, labware_path):
        """Load an Opentrons-format labware JSON onto a deck slot.

        Args:
            slot_id: Deck slot ("1"-"4").
            labware_path: Path to labware JSON file.

        Returns:
            The loaded labware dict.
        """
        self.get_slot(slot_id)  # validate slot exists
        with open(labware_path, "r") as f:
            labware = json.load(f)
        self.slot_labware[str(slot_id)] = labware
        return labware

    def get_well_position(self, slot_id, well_name, tool_id=None):
        """Resolve a well to absolute CNC coordinates.

        Args:
            slot_id: Deck slot ID.
            well_name: Well name (e.g., "A1", "B3").
            tool_id: Optional tool ID to apply tool offset.

        Returns:
            (x, y, z) tuple in absolute CNC coordinates.
        """
        slot = self.get_slot(slot_id)
        slot_pos = slot["position"]

        labware = self.slot_labware.get(str(slot_id))
        if not labware:
            raise ValueError(f"No labware loaded in slot {slot_id}")

        well = labware["wells"].get(well_name)
        if not well:
            raise KeyError(f"Well '{well_name}' not found in labware")

        corner_offset = labware.get("cornerOffsetFromSlot", {"x": 0, "y": 0, "z": 0})

        x = slot_pos[0] + corner_offset["x"] + well["x"]
        y = slot_pos[1] + corner_offset["y"] + well["y"]
        z = slot_pos[2] + corner_offset["z"] + well["z"]

        if tool_id and tool_id in self.tools:
            tool = self.tools[tool_id]
            x += tool.offset["x"]
            y += tool.offset["y"]
            z += tool.offset["z"]

        return x, y, z

    def list_wells(self, slot_id):
        """Return ordered list of well names for labware in a slot."""
        labware = self.slot_labware.get(str(slot_id))
        if not labware:
            raise ValueError(f"No labware loaded in slot {slot_id}")
        ordering = labware.get("ordering", [])
        return [well for col in ordering for well in col]

    # --- Tools ---

    def load_tool(self, tool_config):
        """Register a tool from a config dict.

        Args:
            tool_config: Dict with toolId, offset, controlInterface, parameters, etc.
                         Must match an entry in TOOL_CLASSES.

        Returns:
            The instantiated tool object.
        """
        tool_id = tool_config["toolId"]
        cls = TOOL_CLASSES.get(tool_id)
        if not cls:
            raise ValueError(
                f"Unknown tool type '{tool_id}'. Available: {list(TOOL_CLASSES.keys())}"
            )
        tool = cls(self.cnc, tool_config)
        self.tools[tool_id] = tool
        return tool

    def load_tools_from_json(self, path):
        """Load all tools from a tool_definitions.json file."""
        with open(path, "r") as f:
            data = json.load(f)
        for tool_config in data["tools"]:
            self.load_tool(tool_config)

    def get_tool(self, tool_id):
        """Return a registered tool by ID."""
        if tool_id not in self.tools:
            raise KeyError(
                f"Tool '{tool_id}' not loaded. Available: {list(self.tools.keys())}"
            )
        return self.tools[tool_id]

    # --- Movement ---

    def move_to_well(self, slot_id, well_name, tool_id=None, safe=True, speed=2500):
        """Move the CNC to a specific well position.

        Args:
            slot_id: Deck slot ID.
            well_name: Well name (e.g., "A1").
            tool_id: Optional tool ID to apply offset.
            safe: If True, retract Z before moving XY.
            speed: Movement speed mm/min.
        """
        x, y, z = self.get_well_position(slot_id, well_name, tool_id=tool_id)
        if safe:
            self.cnc.move_to_point_safe(x, y, z, speed=speed)
        else:
            self.cnc.move_to_point(x, y, z, speed=speed)
