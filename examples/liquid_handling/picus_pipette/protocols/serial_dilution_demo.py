"""1:2 serial dilution across a 24-well plate.

Deck layout, Z heights, and CNC settings are loaded from tools/cnc_config.yaml.
Pipette settings (port, offset, volumes) come from tools/picus_config.yaml.

Workflow:
    Phase 1 — Prefill:
        Pick up tip, prefill 23 wells (A1 reserved for stock) with diluent
        from the reservoir's diluent well (batched aspirations), then discard tip.
    Phase 2 — Dilution:
        Pick up new tip, transfer stock from the reservoir's stock well to plate
        A1, then run serial dilution column-by-column (A1→B1→C1→D1→A2→…→D6)
        with mixing between each step. Discard tip at end.
"""

import logging
import sys
from pathlib import Path

import yaml
from cnc_machine_core import CNC_Machine, Deck, DeckState
from opentrons_shared_data.labware import load_definition

# Make sibling `tools/` package importable when run as a script
DEMO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_ROOT))

from tools.picus_pipette import PicusPipette  # noqa: E402

# --- Paths ---
TOOLS_DIR = DEMO_ROOT / "tools"
CNC_CONFIG_PATH = TOOLS_DIR / "cnc_config.yaml"
PIPETTE_CONFIG_PATH = TOOLS_DIR / "picus_config.yaml"
PRESET_PATH = DEMO_ROOT / "deck_preset.yaml"
STATE_OUTPUT = DEMO_ROOT / "output" / "deck_state.yaml"
TIPRACK_PATH = DEMO_ROOT / "custom_labware" / "sartorius_24_tiprack_5000ul.json"


# --- Load configs ---
with open(CNC_CONFIG_PATH, "r", encoding="utf-8") as _f:
    CNC_CFG = yaml.safe_load(_f)
with open(PIPETTE_CONFIG_PATH, "r", encoding="utf-8") as _f:
    PIPETTE_CFG = yaml.safe_load(_f)

VIRTUAL = CNC_CFG.get("virtual", False)
MOVE_SPEED = CNC_CFG.get("move_speed", 1500)

_Z = CNC_CFG["z_heights"]
Z_HOVER = _Z["hover"]
Z_TIP_PICKUP = _Z["tip_pickup"]
Z_WASTE_EJECT = Z_TIP_PICKUP + _Z.get("waste_eject_offset", 10.0)
Z_RESERVOIR = _Z["reservoir"]
Z_PLATE_ASPIRATE = _Z["plate_aspirate"]
Z_PLATE_DISPENSE = _Z["plate_dispense"]
TIP_PATH_Y_OFFSET = CNC_CFG.get("tip_path_y_offset", 15.0)

_V = PIPETTE_CFG["volumes"]
PREFILL_VOLUME = _V["prefill"]
STOCK_VOLUME = PREFILL_VOLUME * _V.get("stock_multiplier", 3)
DILUTION_VOLUME = PREFILL_VOLUME * _V.get("dilution_multiplier", 2)
MIX_VOLUME = _V["mix"]
MIX_CYCLES = _V["mix_cycles"]
TIP_MAX_VOLUME = _V.get("tip_max", 5000)
ASPIRATE_BATCH_COUNT = _V.get("aspirate_batch_count", 6)

# Deck layout (from cnc_config.yaml; must match deck_preset.yaml)
_DECK = CNC_CFG["deck"]
DECK_DEFINITION = _DECK.get("definition")  # built-in name or path; None = default
_SLOTS = _DECK["slots"]
SLOT_PLATE = _SLOTS["plate"]
SLOT_TIPS = _SLOTS["tips"]
SLOT_RESERVOIR = _SLOTS["reservoir"]
SLOT_WASTE = _SLOTS["waste"]
_RES = _DECK["reservoir_wells"]
RES_STOCK_WELL = _RES["stock"]
RES_DILUENT_WELL = _RES["diluent"]


# ---------------------------------------------------------------- helpers


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
    deck = Deck(DECK_DEFINITION)
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

    # Pipette mounting offset (from picus_config.yaml)
    pipette_offset = PIPETTE_CFG.get("offset", {"x": 0, "y": 0, "z": 0})

    # Initialize hardware
    cnc = CNC_Machine.from_config(CNC_CONFIG_PATH, log_level=logging.INFO)
    cnc.connect()
    cnc.home()

    pipette = PicusPipette(
        com_port=PIPETTE_CFG["com_port"],
        virtual=VIRTUAL,
        default_speed=PIPETTE_CFG.get("default_speed", 5),
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
        # --- Phase 1: Prefill 23 wells with diluent (batched aspirations) ----------
        print(f"\n[Phase 1] Prefill 23 wells with {PREFILL_VOLUME}µL diluent")
        pick_up_next_tip(cnc, pipette, deck, state, pipette_offset)
        wells_to_fill = well_order[1:]  # skip A1 (reserved for stock)
        batch_well_count = max(
            1,
            min(ASPIRATE_BATCH_COUNT, TIP_MAX_VOLUME // PREFILL_VOLUME),
        )
        tip_volume_ul = 0
        for i in range(0, len(wells_to_fill), batch_well_count):
            batch = wells_to_fill[i : i + batch_well_count]
            batch_aspirate_volume = PREFILL_VOLUME * len(batch)
            aspirate_at(
                cnc,
                pipette,
                deck,
                SLOT_RESERVOIR,
                RES_DILUENT_WELL,
                batch_aspirate_volume,
                Z_RESERVOIR,
                pipette_offset,
            )
            tip_volume_ul += batch_aspirate_volume
            # Dispense to each well in batch
            for well in batch:
                print(f"  prefill -> Slot{SLOT_PLATE}/{well}")
                dispense_at(
                    cnc,
                    pipette,
                    deck,
                    SLOT_PLATE,
                    well,
                    PREFILL_VOLUME,
                    Z_PLATE_DISPENSE,
                    pipette_offset,
                )
                state.set_status(SLOT_PLATE, well, "filled")
                tip_volume_ul -= PREFILL_VOLUME

        if tip_volume_ul > 0:
            print(
                f"  return_residual -> Slot{SLOT_RESERVOIR}/{RES_DILUENT_WELL} ({tip_volume_ul}µL)"
            )
            dispense_at(
                cnc,
                pipette,
                deck,
                SLOT_RESERVOIR,
                RES_DILUENT_WELL,
                tip_volume_ul,
                Z_RESERVOIR,
                pipette_offset,
            )
            if hasattr(pipette, "blow_out"):
                x, y = _xy(deck, SLOT_RESERVOIR, RES_DILUENT_WELL, pipette_offset)
                cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)
                cnc.move_to_point_safe(x, y, Z_RESERVOIR, speed=MOVE_SPEED)
                pipette.blow_out()
                cnc.move_to_point_safe(x, y, Z_HOVER, speed=MOVE_SPEED)
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
