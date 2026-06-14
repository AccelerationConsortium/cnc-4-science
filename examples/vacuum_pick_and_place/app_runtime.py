"""Bootstrap helpers shared by the CLI protocol and the web app.

Loads configs, builds the CNC machine + deck + gripper + GameSession from
``tools/cnc_config.yaml`` and ``tools/vacuum_config.yaml``. Keeps wiring code
out of the protocol/web layers so each is a thin entry point.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from cnc_machine_core import CNC_Machine, Deck

from game_session import GameSession
from tools.vacuum_gripper import VacuumGripper

DEMO_ROOT = Path(__file__).resolve().parent
TOOLS_DIR = DEMO_ROOT / "tools"
CNC_CONFIG_PATH = TOOLS_DIR / "cnc_config.yaml"
VACUUM_CONFIG_PATH = TOOLS_DIR / "vacuum_config.yaml"
PRESET_PATH = DEMO_ROOT / "presets" / "ttt_preset.yaml"
STATE_OUTPUT = DEMO_ROOT / "output" / "deck_state.yaml"
LABWARE_DIR = DEMO_ROOT / "custom_labware"
STORAGE_LABWARE = LABWARE_DIR / "storage_15_tuberack_100ul.json"
GAMEBOARD_LABWARE = LABWARE_DIR / "gameboard_15_tuberack_100ul.json"


def load_configs():
    with open(CNC_CONFIG_PATH, "r", encoding="utf-8") as f:
        cnc_cfg = yaml.safe_load(f)
    with open(VACUUM_CONFIG_PATH, "r", encoding="utf-8") as f:
        vac_cfg = yaml.safe_load(f)
    return cnc_cfg, vac_cfg


def build_session():
    """Open the CNC, home it, load labware, create the gripper, return a GameSession.

    Returns ``(session, cnc, gripper)`` so the caller can close them on exit.
    """
    cnc_cfg, vac_cfg = load_configs()

    virtual = cnc_cfg.get("virtual", False)
    move_speed = cnc_cfg.get("move_speed", 2500)
    z = cnc_cfg["z_heights"]
    slots = cnc_cfg["deck"]["slots"]
    deck_def = cnc_cfg["deck"].get("definition")
    travel = cnc_cfg.get("travel")  # None -> straight-line moves

    cnc = CNC_Machine.from_config(CNC_CONFIG_PATH)
    cnc.connect()
    if not virtual:
        cnc.home()

    deck = Deck(deck_def) if deck_def else Deck()
    deck.load_labware(slots["storage"], str(STORAGE_LABWARE))
    deck.load_labware(slots["gameboard"], str(GAMEBOARD_LABWARE))

    gripper = VacuumGripper(
        cnc=cnc,
        virtual=virtual,
        vacuum_rpm=vac_cfg.get("vacuum_rpm", 2500),
        grip_delay_s=vac_cfg.get("grip_delay_s", 0.5),
        place_delay_s=vac_cfg.get("place_delay_s", 3.5),
        offset=vac_cfg.get("offset", {"x": 0.0, "y": 0.0, "z": 0.0}),
    )
    gripper.connect()

    session = GameSession(
        cnc=cnc,
        gripper=gripper,
        deck=deck,
        slot_storage=slots["storage"],
        slot_board=slots["gameboard"],
        z_pick=z["pick"],
        z_place=z["place"],
        move_speed=move_speed,
        preset_path=PRESET_PATH,
        state_output=STATE_OUTPUT,
        virtual=virtual,
        travel=travel,
    )
    return session, cnc, gripper


def shutdown(cnc, gripper, *, virtual: bool, move_speed: int = 2500):
    """Park the gantry and close serial. Safe to call from any code path."""
    try:
        gripper.close()
    finally:
        if not virtual:
            try:
                cnc.move_to_point_safe(0, 0, 0, speed=move_speed)
            except Exception:
                pass
        cnc.close()
