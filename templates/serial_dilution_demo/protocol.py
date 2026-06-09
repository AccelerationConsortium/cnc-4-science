"""1:2 serial dilution across a 24-well plate.

Deck layout:
    Slot 1 (front-left) : corning_24_wellplate_3.4ml_flat   – dilution target
    Slot 2 (front-right): custom_tiprack_5000ul             – 5000µL tips
    Slot 3 (back-left)  : opentrons_tough_4_reservoir_72ml  – A1 red stock, A2 diluent
    Slot 4 (back-right) : custom_tiprack_5000ul             – tip waste

Workflow:
    Phase 1 — Prefill:
        Pick up tip, prefill 23 wells (A1 reserved for stock) with 1.5mL diluent
        from reservoir A2, then discard tip.
    Phase 2 — Dilution:
        Pick up new tip, transfer stock from reservoir A1 to plate A1, then run
        1:2 serial dilution column-by-column (A1→B1→C1→D1→A2→…→D6) with mixing
        between each step. Discard tip at end.
"""

import json
import logging
import sys
from pathlib import Path

import yaml
from cnc_machine_core import CNC_Machine, Deck, DeckState
from opentrons_shared_data.labware import load_definition

# Make sibling `tools/` package importable when run as `python protocol.py`
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.sartorius_pipette import SartoriusPipette  # noqa: E402

# --- Configuration ---

COM_PORT_CNC = "COM4"
COM_PORT_PIPETTE = "COM3"
VIRTUAL = False
MOVE_SPEED = 1500

# Calibrated Z heights (CNC absolute coordinates)
Z_HOVER = 0.0  # safe travel height above all labware
Z_TIP_PICKUP = -35.0  # press down to engage tip on pipette
Z_WASTE_EJECT = Z_TIP_PICKUP + 10.0  # height above waste bin for tip ejection
Z_RESERVOIR = -35.0  # depth into reservoir for aspiration
Z_PLATE_ASPIRATE = -35.0  # depth into 24-well plate for aspiration
Z_PLATE_DISPENSE = -35.0  # just above plate well for dispensing
TIP_PATH_Y_OFFSET = 15.0  # mm Y offset for yxy orthogonal tip moves

# Volumes (µL)
PREFILL_VOLUME = 1250  # 1.25mL diluent prefilled into wells 2..24
STOCK_VOLUME = PREFILL_VOLUME * 2  # initial stock load into plate A1
DILUTION_VOLUME = 1250  # transferred between wells for 1:2 dilution
MIX_VOLUME = 1250  # aspirate/dispense volume during mixing
MIX_CYCLES = 3

# Paths — everything is colocated with this script (flat layout)
BASE_PATH = Path(__file__).resolve().parent
CUSTOM_LABWARE_DIR = BASE_PATH / "custom_labware"
TOOLS_PATH = BASE_PATH / "tool_definitions.json"
PRESET_PATH = BASE_PATH / "deck_preset.yaml"
STATE_OUTPUT = BASE_PATH / "output" / "deck_state.yaml"

TIPRACK_PATH = CUSTOM_LABWARE_DIR / "sartorius_24_tiprack_5000ul.json"

# Slot assignments
SLOT_PLATE = "1"
SLOT_TIPS = "2"
SLOT_RESERVOIR = "3"
SLOT_WASTE = "4"

# Reservoir well assignments
RES_STOCK_WELL = "A1"
RES_DILUENT_WELL = "A2"


# ---------------------------------------------------------------- helpers


def load_tool_config(tool_id):
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for tool in data["tools"]:
        if tool["toolId"] == tool_id:
            return tool
    raise KeyError(f"Tool '{tool_id}' not found in {TOOLS_PATH}")


def _xy(deck, slot, well, offset):
    """Return (x, y) for a well with pipette tool offset applied."""
    x, y, _ = deck.get_labware(slot)[well].position(offset=offset)
    return x, y


def _tip_y_waypoint(cnc, y_target):
    """Return bounded Y waypoint so yxy ends with a 15 mm downward Y move."""
    y_wp = y_target + TIP_PATH_Y_OFFSET
    return max(cnc.Y_LOW_BOUND, min(cnc.Y_HIGH_BOUND, y_wp))


# -------------------------------------------------- liquid handling operations


def pick_up_next_tip(cnc, pipette, deck, state, offset):
    """Move toolhead to next available tip in tip rack and press to engage."""
    loc = state.find_next([SLOT_TIPS], "tip")
    if loc is None:
        raise RuntimeError(f"No tips available in Slot {SLOT_TIPS}")
    slot, well = loc
    x, y = _xy(deck, slot, well, offset)
    y_wp = _tip_y_waypoint(cnc, y)
    print(f"  pick_up_tip  Slot{slot}/{well}")
    cnc.move_to_point_safe_orthogonal(
        x,
        y,
        Z_HOVER,
        waypoint=y_wp,
        axis_order="yxy",
        speed=MOVE_SPEED,
    )
    cnc.move_to_point_safe(x, y, Z_TIP_PICKUP, speed=MOVE_SPEED)
    cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)
    state.set_status(slot, well, "empty")
    return slot, well


def discard_tip(cnc, pipette, deck, state, offset):
    """Move toolhead to next free waste position and eject the tip."""
    loc = state.find_next([SLOT_WASTE], "empty")
    if loc is None:
        raise RuntimeError(f"No empty waste positions in Slot {SLOT_WASTE}")
    slot, well = loc
    x, y = _xy(deck, slot, well, offset)
    y_wp = _tip_y_waypoint(cnc, y)
    print(f"  discard_tip  Slot{slot}/{well}")
    cnc.move_to_point_safe_orthogonal(
        x,
        y,
        Z_HOVER,
        waypoint=y_wp,
        axis_order="yxy",
        speed=MOVE_SPEED,
    )
    cnc.move_to_point_safe(x, y, Z_WASTE_EJECT, speed=MOVE_SPEED)
    pipette.tip_eject()
    cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)
    state.set_status(slot, well, "tip")


def aspirate_at(cnc, pipette, deck, slot, well, volume, z_height, offset):
    x, y = _xy(deck, slot, well, offset)
    cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)
    cnc.move_to_point_safe(x, y, z_height, speed=MOVE_SPEED)
    pipette.aspirate(volume)
    cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)


def dispense_at(cnc, pipette, deck, slot, well, volume, z_height, offset):
    x, y = _xy(deck, slot, well, offset)
    cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)
    cnc.move_to_point_safe(x, y, z_height, speed=MOVE_SPEED)
    pipette.dispense(volume)
    cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)


def mix_at(cnc, pipette, deck, slot, well, volume, cycles, z_height, offset):
    """Aspirate then dispense ``volume`` µL in place for ``cycles`` rounds."""
    x, y = _xy(deck, slot, well, offset)
    cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)
    cnc.move_to_point_safe(x, y, z_height, speed=MOVE_SPEED)
    for _ in range(cycles):
        pipette.aspirate(volume)
        pipette.dispense(volume)
    cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)


def dilute(
    cnc,
    pipette,
    deck,
    slot,
    src_well,
    dst_well,
    src_z,
    dst_z,
    volume,
    mix_volume,
    mix_cycles,
    mix_z,
    offset,
):
    """Aspirate from src, dispense into dst, mix — minimising Z travel.

    Stays at depth for dispense→mix and mix→next-aspirate so the CNC
    does not do a redundant hover between consecutive steps.
    """
    sx, sy = _xy(deck, slot, src_well, offset)
    dx, dy = _xy(deck, slot, dst_well, offset)
    mx, my = _xy(deck, slot, dst_well, offset)  # mix in dst

    # Aspirate from src
    cnc.move_to_point_safe(sx, sy, Z_HOVER, speed=MOVE_SPEED)
    cnc.move_to_point_safe(sx, sy, src_z, speed=MOVE_SPEED)
    pipette.aspirate(volume)

    # Travel to dst at hover, descend, dispense — stay down for mixing
    cnc.move_to_point_safe(sx, sy, Z_HOVER, speed=MOVE_SPEED)
    cnc.move_to_point_safe(dx, dy, Z_HOVER, speed=MOVE_SPEED)
    cnc.move_to_point_safe(dx, dy, dst_z, speed=MOVE_SPEED)
    pipette.dispense(volume)

    # Mix in-place without going back up
    if mix_z is not None and mix_z != dst_z:
        cnc.move_to_point_safe(mx, my, mix_z, speed=MOVE_SPEED)
    for _ in range(mix_cycles):
        pipette.aspirate(mix_volume)
        pipette.dispense(mix_volume)

    # Leave tip at depth — caller moves to hover when ready
    cnc.move_to_point_safe(mx, my, Z_HOVER, speed=MOVE_SPEED)


def transfer(
    cnc,
    pipette,
    deck,
    src_slot,
    src_well,
    src_z,
    dst_slot,
    dst_well,
    dst_z,
    volume,
    offset,
    mix_after=False,
    mix_volume=None,
    mix_cycles=0,
    mix_z=None,
):
    """Aspirate from source, dispense at destination, optionally mix after."""
    aspirate_at(cnc, pipette, deck, src_slot, src_well, volume, src_z, offset)
    dispense_at(cnc, pipette, deck, dst_slot, dst_well, volume, dst_z, offset)
    if mix_after:
        mix_at(
            cnc,
            pipette,
            deck,
            dst_slot,
            dst_well,
            mix_volume or volume,
            mix_cycles,
            mix_z if mix_z is not None else dst_z,
            offset,
        )


# ---------------------------------------------------------------- protocol


def run():
    # Load deck and labware
    deck = Deck()
    deck.load_labware_definition(
        SLOT_PLATE, load_definition("corning_24_wellplate_3.4ml_flat", version=1)
    )
    deck.load_labware(SLOT_TIPS, str(TIPRACK_PATH))
    deck.load_labware_definition(
        SLOT_RESERVOIR, load_definition("opentrons_tough_4_reservoir_72ml", version=1)
    )
    deck.load_labware(SLOT_WASTE, str(TIPRACK_PATH))

    # Column-major well order: A1, B1, C1, D1, A2, B2, …, D6
    well_order = [w.name for w in deck.get_labware(SLOT_PLATE).wells()]
    assert len(well_order) == 24, f"expected 24 wells, got {len(well_order)}"

    # Load deck state
    STATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(PRESET_PATH, "r", encoding="utf-8") as f:
        preset = yaml.safe_load(f)
    state = DeckState(state_file=str(STATE_OUTPUT))
    state.init_from_preset(preset)

    # Tool config
    pipette_config = load_tool_config("sartorius_pipette")
    pipette_offset = pipette_config.get("offset", {"x": 0, "y": 0, "z": 0})

    # Initialize hardware
    cnc = CNC_Machine(com=COM_PORT_CNC, virtual=VIRTUAL, log_level=logging.INFO)
    cnc.connect()
    cnc.home()

    pipette = SartoriusPipette(
        com_port=pipette_config.get("com_port", COM_PORT_PIPETTE),
        virtual=VIRTUAL,
        default_speed=pipette_config.get("default_speed", 5),
    )
    pipette.connect()

    print("=" * 60)
    print("Serial dilution (1:2) across 24-well plate")
    print(f"  Virtual:        {VIRTUAL}")
    print(f"  Wells:          {len(well_order)} ({well_order[0]}..{well_order[-1]})")
    print(f"  Prefill:        {PREFILL_VOLUME}µL per well x{len(well_order)-1}")
    print(f"  Stock load:     {STOCK_VOLUME}µL into Slot{SLOT_PLATE}/{well_order[0]}")
    print(f"  Dilution xfer:  {DILUTION_VOLUME}µL with mix x{MIX_CYCLES}")
    print("=" * 60)

    try:
        # --- Phase 1: Prefill 23 wells with diluent --------------------
        print(f"\n[Phase 1] Prefill 23 wells with {PREFILL_VOLUME}µL diluent")
        pick_up_next_tip(cnc, pipette, deck, state, pipette_offset)
        for well in well_order[1:]:
            print(f"  prefill -> Slot{SLOT_PLATE}/{well}")
            transfer(
                cnc,
                pipette,
                deck,
                SLOT_RESERVOIR,
                RES_DILUENT_WELL,
                Z_RESERVOIR,
                SLOT_PLATE,
                well,
                Z_PLATE_DISPENSE,
                PREFILL_VOLUME,
                pipette_offset,
            )
            state.set_status(SLOT_PLATE, well, "filled")
        discard_tip(cnc, pipette, deck, state, pipette_offset)

        # --- Phase 2: Load stock, then serial dilute ------------------
        print(f"\n[Phase 2] Load stock + serial dilute {len(well_order)} wells")
        pick_up_next_tip(cnc, pipette, deck, state, pipette_offset)

        # Transfer stock from reservoir A1 to plate A1
        first_well = well_order[0]
        print(f"  stock -> Slot{SLOT_PLATE}/{first_well} ({STOCK_VOLUME}µL)")
        transfer(
            cnc,
            pipette,
            deck,
            SLOT_RESERVOIR,
            RES_STOCK_WELL,
            Z_RESERVOIR,
            SLOT_PLATE,
            first_well,
            Z_PLATE_DISPENSE,
            STOCK_VOLUME,
            pipette_offset,
        )
        state.set_status(SLOT_PLATE, first_well, "filled")

        # Serial 1:2 dilution across remaining wells (optimised: no redundant Z hops)
        for i in range(len(well_order) - 1):
            src = well_order[i]
            dst = well_order[i + 1]
            print(f"  dilute {src} -> {dst} ({DILUTION_VOLUME}µL, mix x{MIX_CYCLES})")
            dilute(
                cnc,
                pipette,
                deck,
                SLOT_PLATE,
                src,
                dst,
                Z_PLATE_ASPIRATE,
                Z_PLATE_DISPENSE,
                DILUTION_VOLUME,
                MIX_VOLUME,
                MIX_CYCLES,
                Z_PLATE_ASPIRATE,
                pipette_offset,
            )
            state.set_status(SLOT_PLATE, dst, "filled")

        discard_tip(cnc, pipette, deck, state, pipette_offset)

        print("\n" + "=" * 60)
        print("Protocol complete")
        print("=" * 60)
        state.save()
        print(f"Deck state saved -> {STATE_OUTPUT}")

    finally:
        try:
            cnc.move_to_point_safe(0, 0, 0, speed=MOVE_SPEED)
        except Exception as e:
            print(f"[cleanup] move-home failed: {e}")
        pipette.close()
        cnc.close()


if __name__ == "__main__":
    run()

