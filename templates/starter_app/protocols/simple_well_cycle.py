"""Simple well-cycling protocol with gripper toggle.

Iterates through wells in one or more slots, moving the toolhead to each
well at a safe hover height. Toggles the vacuum gripper on/off every other
well to verify gripper control alongside deck validation.

Usage:
    python protocols/simple_well_cycle.py
"""

import json
import logging
from pathlib import Path

from cnc_machine_core import CNC_Machine
from cnc_machine_core import Deck

# --- Configuration (edit these for your setup) ---

COM_PORT = "COM6"
VIRTUAL = True  # set False when running on real hardware
MOVE_SPEED = 1500
HOVER_Z = -5.0  # safe Z height to hover above wells

# Paths — adjust to match your project layout
BASE_PATH = Path(__file__).resolve().parent.parent
LABWARE_DIR = BASE_PATH.parent / "labware"  # core labware directory
TOOLS_PATH = BASE_PATH / "tools" / "tool_definitions.json"

# Map slots to labware files (edit for your deck)
LABWARE_BY_SLOT = {
    "1": LABWARE_DIR / "vialtrayholder_25_tuberack_1000ul.json",
}


def load_tool_config(tool_id):
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for tool in data["tools"]:
        if tool["toolId"] == tool_id:
            return tool
    raise KeyError(f"Tool '{tool_id}' not found in {TOOLS_PATH}")


def run():
    deck = Deck()
    labware_by_slot = {}
    for slot_id, path in LABWARE_BY_SLOT.items():
        labware_by_slot[slot_id] = deck.load_labware(slot_id, str(path))

    gripper_config = load_tool_config("vacuum_gripper")
    gripper_offset = gripper_config.get("offset", {"x": 0, "y": 0, "z": 0})
    spindle_speed = gripper_config.get("spindle_speed_rpm", 1000)

    cnc = CNC_Machine(
        com=COM_PORT,
        virtual=VIRTUAL,
        log_level=logging.INFO,
    )
    cnc.connect()
    cnc.home()

    slots = list(LABWARE_BY_SLOT.keys())
    print(f"Cycling wells in slots: {slots}")
    print(f"Hover Z: {HOVER_Z}, Speed: {MOVE_SPEED}")
    print(f"Gripper offset: x={gripper_offset['x']}, y={gripper_offset['y']}")
    if VIRTUAL:
        print("(virtual mode — no real motion)")
    print("Press Enter to advance, 'q' to quit.\n")

    vacuum_on = False

    try:
        for slot_id in slots:
            plate = labware_by_slot[slot_id]
            wells = plate.wells()
            print(f"--- Slot {slot_id}: {len(wells)} wells ---")

            for i, well in enumerate(wells):
                x, y, _ = well.position(offset=gripper_offset)

                # Toggle gripper every other well
                if i % 2 == 0:
                    cnc.follow_gcode_path(f"M3 S{spindle_speed}\n")
                    vacuum_on = True
                    state = "ON"
                else:
                    cnc.follow_gcode_path("M5\n")
                    vacuum_on = False
                    state = "OFF"

                print(f"  [{slot_id}/{well.name}] X{x:.2f} Y{y:.2f} Z{HOVER_Z}  gripper {state}")
                cnc.move_to_point_safe(x, y, HOVER_Z, speed=MOVE_SPEED)

                cmd = input("  (Enter=next, q=quit) ").strip().lower()
                if cmd in {"q", "quit"}:
                    print("Stopping early.")
                    return

    except KeyboardInterrupt:
        print("\nAborted.")
    finally:
        if vacuum_on:
            cnc.follow_gcode_path("M5\n")
        cnc.home()
        cnc.close()
        print("Done.")


run()
