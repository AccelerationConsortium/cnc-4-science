"""Interactive Z-height calibration helper.

Moves XY to a chosen slot/well, then lets you step Z up/down at
three granularities to find the correct working height for each tool
and labware combination.

Controls:
    Enter       step DOWN by current increment
    u           step UP by current increment
    1 / 2 / 3  switch to coarse (2mm) / medium (0.5mm) / fine (0.1mm)
    s           save current Z to calibration file
    q           quit

Usage:
    python z_helper.py
"""

import json
import logging
import yaml
from pathlib import Path

from cnc_machine_core import CNC_Machine
from cnc_machine_core import Deck
from opentrons_shared_data.labware import load_definition

# --- Configuration ---

COM_PORT = "COM4"
VIRTUAL = False  # set False for real hardware

STEP_COARSE = 2.0
STEP_MEDIUM = 0.5
STEP_FINE = 0.1

# Paths — everything is colocated with this script (flat layout)
BASE_PATH = Path(__file__).resolve().parent
TOOLS_PATH = BASE_PATH / "tool_definitions.json"
CALIBRATION_FILE = BASE_PATH / "output" / "z_calibration.yaml"
TIPRACK_PATH = BASE_PATH / "custom_labware" / "sartorius_24_tiprack_5000ul.json"

# Map slots to labware (must match protocol.py)
# Slot 1: corning_24_wellplate_3.4ml_flat (dilution target)
# Slot 2: sartorius_24_tiprack_5000ul (5000µL tips)
# Slot 3: opentrons_tough_4_reservoir_72ml (stock + diluent)
# Slot 4: sartorius_24_tiprack_5000ul (tip waste)

# Define labware slots - use load_definition for Opentrons standard labware
LABWARE_DEFINITIONS = {
    "1": ("corning_24_wellplate_3.4ml_flat", None),  # Opentrons standard, version 1
    "2": (None, str(TIPRACK_PATH)),  # Custom labware file
    "3": ("opentrons_tough_4_reservoir_72ml", None),  # Opentrons standard, version 1
    "4": (None, str(TIPRACK_PATH)),  # Custom labware file
}


def load_tools():
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {t["toolId"]: t["offset"] for t in data["tools"]}


def load_calibration():
    if CALIBRATION_FILE.exists():
        with CALIBRATION_FILE.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_calibration(data):
    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CALIBRATION_FILE.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)


def run():
    deck = Deck()
    labware_by_slot = {}

    # Load labware based on definitions
    for slot_id, (opentrons_name, custom_path) in LABWARE_DEFINITIONS.items():
        if opentrons_name:
            # Load Opentrons standard labware
            deck.load_labware_definition(
                slot_id, load_definition(opentrons_name, version=1)
            )
        elif custom_path:
            # Load custom labware
            deck.load_labware(slot_id, custom_path)
        labware_by_slot[slot_id] = deck.get_labware(slot_id)

    tools = load_tools()
    calibration = load_calibration()

    print("=== Z Calibration Helper ===")
    if calibration:
        print("Existing calibrations:")
        for key, val in calibration.items():
            print(f"  {key}: Z={val}")
    print()

    # Tool selection
    tool_names = list(tools.keys())
    print("Available tools:")
    print("  0: none (spindle center)")
    for i, name in enumerate(tool_names, 1):
        off = tools[name]
        print(f"  {i}: {name} (x={off['x']:+.2f} y={off['y']:+.2f})")
    tool_choice = input("Tool number: ").strip()
    if tool_choice == "0" or tool_choice == "":
        tool_id = None
        tool_offset = {"x": 0, "y": 0, "z": 0}
    else:
        idx = int(tool_choice) - 1
        tool_id = tool_names[idx]
        tool_offset = tools[tool_id]
    tool_label = tool_id or "no_tool"
    print(f"Using: {tool_label}\n")

    # Slot and well selection
    available = list(LABWARE_DEFINITIONS.keys())
    slot_id = input(f"Slot ID ({', '.join(available)}): ").strip()
    if slot_id not in available:
        print(f"Invalid slot '{slot_id}'")
        return

    plate = labware_by_slot[slot_id]
    well_names = plate.well_names()
    print(f"Wells: {', '.join(well_names[:10])}{'...' if len(well_names) > 10 else ''}")
    well_name = input("Well name (e.g. A1): ").strip().upper()
    if well_name not in well_names:
        print(f"Well '{well_name}' not found")
        return

    initial_z_str = input("Initial Z (default -5.0): ").strip()
    initial_z = float(initial_z_str) if initial_z_str else -5.0

    x, y, _ = plate[well_name].position(offset=tool_offset)
    print(f"\nTarget: Slot {slot_id} {well_name} + {tool_label} -> X{x:.2f} Y{y:.2f}")

    cnc = CNC_Machine(
        com=COM_PORT,
        virtual=VIRTUAL,
        log_level=logging.INFO,
    )
    cnc.connect()
    cnc.home()

    current_z = initial_z
    step = STEP_COARSE
    step_label = "coarse"

    cnc.move_to_point_safe(x, y, current_z, speed=1500, gtype="G0")
    print(f"\nAt X{x:.2f} Y{y:.2f} Z{current_z:.2f}")
    print("Controls: Enter=down, u=up, 1=coarse, 2=medium, 3=fine, s=save, q=quit")

    try:
        while True:
            cmd = input(f"[{step_label} {step}mm] Z={current_z:.2f} > ").strip().lower()

            if cmd == "q":
                break
            elif cmd == "1":
                step, step_label = STEP_COARSE, "coarse"
                continue
            elif cmd == "2":
                step, step_label = STEP_MEDIUM, "medium"
                continue
            elif cmd == "3":
                step, step_label = STEP_FINE, "fine"
                continue
            elif cmd == "s":
                # Get labware name for calibration key
                opentrons_name, custom_path = LABWARE_DEFINITIONS[slot_id]
                if opentrons_name:
                    labware_name = opentrons_name
                else:
                    labware_name = Path(custom_path).stem
                cal_key = f"{labware_name}__{tool_label}"
                calibration[cal_key] = round(current_z, 2)
                save_calibration(calibration)
                print(f"  Saved: {cal_key} = {current_z:.2f}")
                continue
            elif cmd == "u":
                current_z = round(current_z + step, 2)
            elif cmd == "":
                current_z = round(current_z - step, 2)
            else:
                print("  Unknown command")
                continue

            current_z = max(current_z, -35.0)
            current_z = min(current_z, 0.0)
            cnc.move_to_point(z=current_z, speed=500)
            print(f"  -> Z={current_z:.2f}")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        cnc.close()
        print("Done.")


run()
