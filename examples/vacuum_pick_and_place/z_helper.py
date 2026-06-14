"""Interactive Z-height calibration helper for the vacuum pick-and-place demo.

Reads CNC connection + deck layout from ``tools/cnc_config.yaml`` and the
vacuum tool's XY offset from ``tools/vacuum_config.yaml``. Loads the demo's
own custom labware (storage + gameboard) into the deck slots declared in
``cnc_config.yaml``, then jogs Z so you can calibrate the ``pick`` height
(over storage) and the ``place`` height (over the gameboard).

Save with ``s`` — values are written to ``output/z_calibration.yaml``. Copy
them into ``tools/cnc_config.yaml`` under ``z_heights:`` once you're happy.

Controls:
    Enter      step DOWN by current increment
    u          step UP by current increment
    1 / 2 / 3  switch to coarse (2 mm) / medium (0.5 mm) / fine (0.1 mm)
    s          save current Z to calibration file
    q          quit

Usage:
    cd examples/vacuum_pick_and_place
    python z_helper.py
"""

import logging
from pathlib import Path

import yaml
from cnc_machine_core import CNC_Machine, Deck

from app_runtime import (
    CNC_CONFIG_PATH,
    DEMO_ROOT,
    GAMEBOARD_LABWARE,
    STORAGE_LABWARE,
    VACUUM_CONFIG_PATH,
    load_configs,
)

STEP_COARSE = 2.0
STEP_MEDIUM = 0.5
STEP_FINE = 0.1

CALIBRATION_FILE = DEMO_ROOT / "output" / "z_calibration.yaml"

# Slot role -> labware definition path. Matches build_session() in app_runtime.
ROLE_LABWARE = {
    "storage": STORAGE_LABWARE,
    "gameboard": GAMEBOARD_LABWARE,
}


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
    cnc_cfg, vac_cfg = load_configs()
    slots = cnc_cfg["deck"]["slots"]                  # {"storage": "1", "gameboard": "2"}
    deck_def = cnc_cfg["deck"].get("definition")
    tool_offset = vac_cfg.get("offset", {"x": 0.0, "y": 0.0, "z": 0.0})
    tool_label = vac_cfg.get("toolId", "vacuum_gripper")

    # Load labware into the slots from cnc_config.yaml.
    deck = Deck(deck_def) if deck_def else Deck()
    labware_by_role = {}
    for role, lw_path in ROLE_LABWARE.items():
        slot_id = slots[role]
        deck.load_labware(slot_id, str(lw_path))
        labware_by_role[role] = (slot_id, deck.get_labware(slot_id), lw_path.stem)

    calibration = load_calibration()
    print("=== Vacuum Pick-and-Place Z Helper ===")
    print(f"Tool: {tool_label}  offset=(x={tool_offset['x']:+.2f}, y={tool_offset['y']:+.2f})")
    print(f"Deck slots: {slots}\n")
    if calibration:
        print("Existing calibrations:")
        for key, val in calibration.items():
            print(f"  {key}: Z={val}")
        print()

    # Role selection (pick over storage, place over gameboard).
    print("Calibration target:")
    print("  1: storage   (calibrate `pick` Z)")
    print("  2: gameboard (calibrate `place` Z)")
    role_choice = input("Choose (1/2): ").strip()
    role = {"1": "storage", "2": "gameboard"}.get(role_choice)
    if role is None:
        print("Invalid choice.")
        return

    slot_id, plate, labware_name = labware_by_role[role]
    well_names = plate.well_names()
    print(f"\nSlot {slot_id} ({labware_name}) wells: "
          f"{', '.join(well_names[:10])}{'...' if len(well_names) > 10 else ''}")
    well_name = input("Well name (e.g. A1): ").strip().upper()
    if well_name not in well_names:
        print(f"Well '{well_name}' not found")
        return

    initial_z_str = input("Initial Z (default -5.0): ").strip()
    initial_z = float(initial_z_str) if initial_z_str else -5.0

    x, y, _ = plate[well_name].position(offset=tool_offset)
    print(f"\nTarget: Slot {slot_id} {well_name} + {tool_label} -> X{x:.2f} Y{y:.2f}")

    cnc = CNC_Machine.from_config(CNC_CONFIG_PATH, log_level=logging.INFO)
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
                action = "pick" if role == "storage" else "place"
                cal_key = f"{labware_name}__{tool_label}__{action}"
                calibration[cal_key] = round(current_z, 2)
                save_calibration(calibration)
                print(f"  Saved: {cal_key} = {current_z:.2f}  -> {CALIBRATION_FILE}")
                print(f"  Copy into tools/cnc_config.yaml: z_heights.{action}: {current_z:.2f}")
                continue
            elif cmd == "u":
                current_z = round(current_z + step, 2)
            elif cmd == "":
                current_z = round(current_z - step, 2)
            else:
                print("  Unknown command")
                continue

            current_z = max(current_z, cnc.Z_LOW_BOUND)
            current_z = min(current_z, cnc.Z_HIGH_BOUND)
            cnc.move_to_point(z=current_z, speed=500)
            print(f"  -> Z={current_z:.2f}")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        cnc.close()
        print("Done.")


run()
