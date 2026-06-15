# Setting Up a CNC Machine for a New Application

This guide walks through the end-to-end workflow for turning a bare Genmitsu CNC
into a working instrument for a new experiment. The two examples shipped with
the library cover the two ends of the spectrum:

- [examples/hello_cnc/](../examples/hello_cnc/) — open deck, direct coordinates,
  no labware. The minimum needed to verify the machine moves.
- [examples/liquid_handling/](../examples/liquid_handling/) — full deck layout,
  Opentrons + custom labware, calibrated tool offsets, multi-phase protocol.

The order of operations below is the same one used to build the liquid handling
demo. Follow it from top to bottom for any new application.

---

## 0. Prerequisites

- A homed, working Genmitsu CNC (GRBL firmware over USB serial).
- The COM port / `/dev/tty*` device of the controller.
- The physical XY/Z travel envelope of your machine (mm) — see below.
- Python 3.10+ with `cnc-4-science` installed:
  ```bash
  pip install cnc-4-science
  ```
- A first-pass hardware check before doing anything else:
  ```bash
  python examples/hello_cnc/hello_cnc.py
  ```
  Edit [examples/hello_cnc/cnc_config.yaml](../examples/hello_cnc/cnc_config.yaml)
  first to match your COM port and travel bounds.

### Verify your CNC travel bounds (this is model-specific!)

**The `bounds:` block in `cnc_config.yaml` MUST match your physical machine.**
The shipped configs use the Genmitsu CNC **3018** envelope (X 0..280, Y 0..180,
Z -37..0) because that's the model the liquid handling demo runs on. A 3020,
4040, PROVerXL, etc. will have a completely different envelope, and the
library's bounds-check will silently skip any move outside what you declared
— or worse, you'll declare bounds that exceed the machine and crash the
gantry into a limit switch.

Before editing the YAML, use a GRBL jog UI to *measure* the real travel of
your specific unit:

1. Install [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations)
   (or UGS / bCNC — anything that talks GRBL over the same COM port).
2. Home the machine.
3. Jog X to the positive limit (until it hits the switch or you see resistance),
   read `MPos.X`. Repeat for X negative, Y±, Z±.
4. Subtract a small safety margin (1–3 mm) from each end.
5. Put the resulting numbers into `bounds:` in `cnc_config.yaml`.

Close Candle before running any Python script — only one process can hold the
serial port at a time.

If hello_cnc homes, jogs, and toggles the spindle, the machine is good and you
can start building the application.

---

## 1. Define your deck layout

The deck is the static map from "slot N" to absolute machine coordinates. It is
defined once per physical mounting plate. You almost never edit slot positions
at runtime — they are calibrated to the holes you cut/printed/clamped onto the
CNC bed.

### Two built-in decks

Both shipped definitions are **sized for the Genmitsu 3018-PROVer V2**
(~300×180 mm bed). Larger CNCs (3040, 6040, etc.) will usually want a
custom deck with more / larger slots — copy `cnc_4_slot_deck.json` and
re-measure the slot corners.

There is no default — always pass an explicit deck name (or path) so the
CNC footprint is visible at the call site.

| Definition           | Layout       | Use case                                    |
| -------------------- | ------------ | ------------------------------------------- |
| `cnc_4_slot_deck`    | 2×2 SBS-ish  | Multi-labware protocols on the 3018.        |
| `cnc_1_slot_deck`    | Open / origin| Single fixture; or pure raw-coordinate use. |

```python
from cnc_machine_core import Deck

deck = Deck("cnc_4_slot_deck")      # 4-slot, Genmitsu 3018 footprint
deck = Deck("cnc_1_slot_deck")      # open / single fixture
deck = Deck("path/to/my_deck.json") # custom JSON
```

### Anatomy of a deck JSON

A deck is a list of slots, each with an absolute `position` (the corner of the
slot in machine XY) and a `boundingBox` (so labware loaded onto it knows where
its origin lives). See
[src/cnc_machine_core/deck/cnc_4_slot_deck.json](../src/cnc_machine_core/deck/cnc_4_slot_deck.json)
for the exact schema. To make a custom deck:

1. Copy `cnc_4_slot_deck.json` and rename it (e.g. `my_3_slot_deck.json`).
2. Edit `locations.slots`: set each slot's `id`, `displayName`, `position`
   `[x, y, z]` in mm (absolute machine coordinates), and `boundingBox` to the
   footprint of whatever labware will sit there (SBS 127.7 × 85.5 mm by
   default).
3. Pass the path to `Deck("path/to/my_3_slot_deck.json")`.

Pick the slot corners by jogging the spindle to the front-left corner of each
physical mounting location and reading the GRBL `MPos`. Record those numbers
in the deck JSON. After this is done, all per-protocol movement is expressed
in *slot* + *well* — you should not be retuning the deck again.

---

## 2. Load labware onto slots

Once the deck exists, each slot gets a piece of *labware* — a JSON file in the
Opentrons format that describes the wells inside that slot relative to its
corner. The library converts to absolute machine coordinates automatically:

```
absolute_well_xyz = slot.position + labware.cornerOffsetFromSlot + well.xyz
```

You have three options for sourcing labware, in order of preference.

### Option A — Standard Opentrons labware (SBS plates, tipracks, reservoirs)

If your container is a normal SBS-format plate / tiprack / reservoir, it
probably already exists in [opentrons-shared-data](https://github.com/Opentrons/opentrons/tree/edge/shared-data/labware/definitions).
Load it by load name with no JSON files of your own:

```python
from opentrons_shared_data.labware import load_definition
from cnc_machine_core import Deck

deck = Deck("cnc_4_slot_deck")
plate_def = load_definition("corning_24_wellplate_3.4ml_flat", 1)
plate = deck.load_labware_definition("1", plate_def)
```

This is what the liquid handling demo does for the 24-well plate and the
4-channel reservoir.

### Option B — Custom labware via the Opentrons Labware Creator

If your container is *SBS-shaped* (127.7 × 85.5 mm footprint) but not a stock
part — a custom 3D-printed tube rack, a sample-specific plate, a tiprack from a
non-Opentrons vendor — generate a JSON for it at
<https://labware.opentrons.com/#/create>:

1. Set the dimensions, well count, well shape, depth, spacing, A1 offset.
2. Export the JSON.
3. Drop it into your project's `custom_labware/` folder.
4. Load it with the path:
   ```python
   plate = deck.load_labware("1", "custom_labware/my_24_tuberack.json")
   ```

This is the [`sartorius_24_tiprack_5000ul.json`](../examples/liquid_handling/custom_labware/sartorius_24_tiprack_5000ul.json)
case in the demo — a custom tiprack matching the Picus tip footprint.

Only the X / Y well coordinates from the JSON are used. **Z heights are *not*
trusted from the labware definition.** In principle Z could be computed as
`slot.z + labware.cornerOffsetFromSlot.z + well.z + tool.offset.z + tip_length`,
but in practice there are too many independently-variable terms (deck shim
thickness, labware seating, tool mounting height, tip length per box) — getting
any one of them wrong by 1 mm crashes the tool. Rather than maintain four
calibration knobs that all have to agree, we collapse them into a single
empirical number per (tool, labware, action) tuple, measured by hand once and
pinned in `tools/cnc_config.yaml`. See step 4.

Access wells by name once loaded:

```python
well = plate["A1"]
x, y, z = well.position()                         # absolute coordinates
x, y, z = well.position(offset={"x": 6.75, "y": -4.0})  # with tool offset

for well in plate.wells():        # iterate in column-major Opentrons order
    cnc.move_to_point_safe(*well.position(offset=tool_offset))
```

### Option C — Non-SBS containers (use `move_to_location` arrays)

If your container doesn't fit SBS — a vial rack you machined yourself, a
custom HPLC tray, a row of beakers on a benchtop fixture — skip the
labware/JSON pipeline entirely and use `move_to_location()` with a YAML grid
definition. See [examples/hello_cnc/location_status.yaml](../examples/hello_cnc/location_status.yaml):

```yaml
vial_rack:
  num_x: 2          # columns
  num_y: 4          # rows
  x_origin: 166.5   # absolute machine X of position 0
  y_origin: 125     # absolute machine Y of position 0
  z_origin: 0
  x_offset: 37.5    # column pitch (measure with calipers)
  y_offset: -36     # row pitch (negative = back-to-front)
```

Then in code:

```python
m = CNC_Machine.from_config("cnc_config.yaml",
                            locations_file="location_status.yaml")
m.move_to_location("vial_rack", 0, safe=True)  # position 0
m.move_to_location("vial_rack", 3, safe=True)  # 4th position (column-major)
```

Indices walk *down a column*, then to the next column (index 0 is
`x_origin, y_origin`, index 1 is one row down, etc).

### Option D — Pure raw coordinates (no labware at all)

For one-off probes, a single fixture, alignment work, or motion debugging,
skip both labware and location grids and use `move_to_point_safe()` directly:

```python
cnc.move_to_point_safe(x=100.0, y=50.0, z=-20.0)
```

This is what `hello_cnc.py`'s line `m.move_to_point(100, 100, -30)` does.
Useful while you're still figuring out what *should* become a labware
definition. Always prefer `_safe` over the bare `move_to_point` — it lifts Z
first, moves XY, then drops Z, which keeps the tool from dragging through
whatever is on the deck.

For motion *between* two crowded slots, also see `move_to_point_safe_orthogonal()`
in the [API reference](../README.md#api-reference) — it lets you specify a
waypoint and axis order to route around obstacles.

---

## 3. Configure the toolhead

The "toolhead" is whatever is bolted to the spindle mount: a pipette, a
camera, a force sensor, a syringe pump, a peristaltic pump, a webcam, a vial
capper. Each tool needs four things:

1. **A communication channel.** A serial port (most common), USB HID, I²C,
   etc.
2. **A driver.** Either vendor-supplied or written by you. Wraps the wire
   protocol in Python methods.
3. **A wrapper class.** A thin Python class that *uses* the driver and exposes
   the high-level actions your protocols need (`aspirate`, `tip_eject`,
   `capture_image`, `dispense_fraction`).
4. **An XY/Z mounting offset.** The tool tip is not at the spindle center.
   The offset captures how far off it is.

### 3.1 Driver

If the vendor publishes a Python driver (PyPI / GitHub), pin a version in
`requirements.txt`. If not, vendor a copy into `tools/` — that's what the
liquid handling demo does with [`tools/picus_driver.py`](../examples/liquid_handling/tools/picus_driver.py).
A driver typically exposes raw operations: open the port, send a command,
parse the response.

### 3.2 Tool wrapper class

Every wrapper follows the same shape:

```python
class MyTool:
    def __init__(self, cnc_machine, tool_config):
        self.cnc = cnc_machine
        self.offset = tool_config.get("offset", {"x": 0, "y": 0, "z": 0})
        # ... extract whatever else the protocol needs from tool_config
        self._driver = None  # constructed in connect()

    def connect(self):
        ...
    def close(self):
        ...

    # High-level verbs the protocol calls:
    def aspirate(self, volume_ul): ...
    def dispense(self, volume_ul): ...
```

[`tools/picus_pipette.py`](../examples/liquid_handling/tools/picus_pipette.py)
is the reference implementation. Two patterns worth copying:

- **Virtual mode**: take a `virtual: bool` flag. In virtual mode, `print()`
  the action and skip the driver. This lets every protocol dry-run without
  hardware.
- **High-level vocabulary**: name methods after what the protocol thinks
  about (`aspirate`, `dispense`, `blow_out`, `tip_eject`), not what the wire
  protocol thinks about (`send_packet`, `cmd_0x07`).

### 3.3 XY/Z tool offset from the spindle origin

The CNC's coordinate frame is centered on the spindle. The actual *tip* of
your tool — pipette nozzle, camera focus point, capper jaw — is mounted
*beside* the spindle, offset by some `(dx, dy, dz)`. Without the offset, you
will pipette into the wall next to your well.

**Measuring the offset:**

1. Jog the CNC so the spindle center is over a known reference point (a
   crosshair, a well A1 with a centered marker, a calibration plate).
2. Read `MPos` → call this `(x_spindle, y_spindle, z_spindle)`.
3. Now jog so the **tool tip** is over the same reference. Read `MPos` →
   `(x_tool, y_tool, z_tool)`.
4. Offset = `(x_tool − x_spindle, y_tool − y_spindle, z_tool − z_spindle)`.
5. Put those numbers under `offset:` in the tool's config YAML.

Then in every protocol move:

```python
x, y, z = plate["A1"].position(offset=pipette.offset)
cnc.move_to_point_safe(x, y, z)
```

The offset moves with the tool wrapper — if you swap tools, you swap configs,
and protocols don't need to change.

### 3.4 Tool config YAML

Each tool gets its own `tools/<tool>_config.yaml` so swapping a tool means
editing one file. Pattern from the demo
([`tools/picus_config.yaml`](../examples/liquid_handling/tools/picus_config.yaml)):

```yaml
toolId: picus_pipette
displayName: Sartorius Picus 2 5000µL Pipette

com_port: COM3            # serial port for the tool itself
default_speed: 5

offset:                   # mm, relative to spindle center
  x: 0.0
  y: 0.0
  z: 0.0

volumes:                  # whatever the protocol needs
  prefill: 1100
  mix: 1200
  tip_max: 5000
```

The CNC config (`cnc_config.yaml`) owns deck layout, bounds, COM port for the
gantry, and Z heights per labware. The *tool* config owns only the tool. Keep
the split clean.

---

## 4. Calibrate Z heights

Once the deck is fixed and the tool is mounted, you still need to know *how
low* to drop Z in each labware. Z depends on at least four independent things:

- The tool's Z offset from the spindle origin (how far the tool sticks down
  past the spindle nose).
- The labware's intrinsic Z (well depth, tiprack tip height, reservoir floor).
- The deck/slot Z (shim thickness, mounting hardware, how flat the bed is).
- The action (`tip_pickup` engages near the top of a tip, `plate_aspirate`
  reaches the well floor — same labware, very different Z).

In theory you could measure each term separately and add them. In practice
that's four chances to be wrong by a millimeter, and a millimeter is the
difference between aspirating from the floor and ramming the pipette through
the plate. The simpler and more reliable approach: ignore the breakdown and
measure the *final* Z empirically per (tool, labware, action), once, then
pin the numbers in `tools/cnc_config.yaml` under `z_heights:`.

### Procedure

With the tool mounted and the deck installed, for each (labware, action) pair:

1. Open a GRBL UI like [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations)
   (or use `CNC_Machine` from a Python REPL, e.g. `cnc.move_to_point(...)`).
2. Move XY over the relevant well — use the labware's well coordinates plus
   your tool offset: `plate["A1"].position(offset=tool.offset)`.
3. Jog Z down in coarse steps (~2 mm), then medium (~0.5 mm), then fine
   (~0.1 mm) until the tool tip kisses the surface you care about
   (tip-pickup engages near the top of a tip; `plate_aspirate` reaches the
   well floor — same labware, different Z).
4. Read the absolute Z off the controller and write it into the
   `z_heights:` block of `tools/cnc_config.yaml`.

Do this once per build. The shipped examples come with `z_heights:` already
filled in for their reference build (see each example's
`ASSEMBLY_INSTRUCTIONS.md`); if your build matches, you don't need to
remeasure. If you replace a tool, reseat labware, or change a shim,
remeasure only the affected entries.

```yaml
z_heights:
  hover: 0.0
  tip_pickup: -35.5
  reservoir: -36.5
  plate_aspirate: -36.5
  plate_dispense: -36.5
```

These are the named Z values the protocol uses. The XY of each well comes
from labware; the Z comes from this block. If you replace a tool or reseat a
labware, remeasure the affected entries.

---

## 5. Write the protocol

Protocols live in `protocols/` and contain *only the workflow logic* — no
serial ports, no labware paths, no Z numbers. Everything sourced from config:

```python
from pathlib import Path
import yaml
from opentrons_shared_data.labware import load_definition
from cnc_machine_core import CNC_Machine, Deck
from tools.picus_pipette import PicusPipette

HERE = Path(__file__).resolve().parent
CNC_CFG  = HERE.parent / "tools" / "cnc_config.yaml"
TOOL_CFG = HERE.parent / "tools" / "picus_config.yaml"

cnc_cfg  = yaml.safe_load(CNC_CFG.read_text())
tool_cfg = yaml.safe_load(TOOL_CFG.read_text())

# 1. Build the machine (deck-aware via cnc_config.yaml)
cnc = CNC_Machine.from_config(CNC_CFG)
deck = Deck(cnc_cfg["deck"]["definition"])
plate = deck.load_labware_definition("1",
            load_definition("corning_24_wellplate_3.4ml_flat", 1))
tips  = deck.load_labware("2", str(HERE.parent / "custom_labware" /
            "sartorius_24_tiprack_5000ul.json"))

# 2. Build the tool
pipette = PicusPipette(com_port=tool_cfg["com_port"],
                       virtual=cnc_cfg.get("virtual", False))

# 3. Run the workflow
cnc.connect(); pipette.connect()
try:
    z = cnc_cfg["z_heights"]
    offset = tool_cfg["offset"]
    for well in plate.wells():
        x, y, _ = well.position(offset=offset)
        cnc.move_to_point_safe(x, y, z["plate_dispense"])
        pipette.dispense(100)
finally:
    pipette.close(); cnc.close()
```

[examples/liquid_handling/protocols/serial_dilution_demo.py](../examples/liquid_handling/protocols/serial_dilution_demo.py)
is a worked version of this pattern.

### Dry-run first

Set `virtual: true` in `cnc_config.yaml` and re-run the protocol. The CNC
class logs every G-code it would emit; the tool wrapper logs every action it
would take. Read the log end-to-end before powering anything on. Then flip
`virtual: false` and run on hardware.

---

## 6. Track deck state (optional)

For protocols that consume / produce wells over time (tip racks emptying,
samples processed, fractions collected), use `DeckState`:

```python
from cnc_machine_core import DeckState

ds = DeckState()
ds.init_wells_from_labware("2", tips)
next_slot, next_well = ds.find_next(["2"], "available")
ds.set_status("2", next_well, "used")
```

Status strings are application-defined. State is auto-persisted to YAML in
`output/`, so a crashed protocol can resume from where it stopped.

---

## Cheat sheet — building a new application from scratch

| Step | What you do                                  | Where it lives                          |
| ---: | -------------------------------------------- | --------------------------------------- |
|    1 | Run `hello_cnc.py` once to verify the gantry | `examples/hello_cnc/`                   |
|    2 | Copy `examples/liquid_handling/` as template | `your_project/`                         |
|    3 | Edit deck slot positions (rarely)            | custom `deck.json` or built-in          |
|    4 | Load labware (Opentrons name, JSON, or grid) | `custom_labware/`, `location_status.yaml`|
|    5 | Drop in vendor driver                        | `tools/<vendor>_driver.py`              |
|    6 | Write thin tool wrapper                      | `tools/<tool>.py`                       |
|    7 | Measure XY/Z offset spindle → tool tip       | `tools/<tool>_config.yaml` → `offset:`  |
|    8 | Measure Z heights by hand (see §4)           | `tools/cnc_config.yaml` → `z_heights:`  |
|    9 | Write the workflow against config + wrapper  | `protocols/<workflow>.py`               |
|   10 | Dry-run with `virtual: true`, then hardware  | `tools/cnc_config.yaml`                 |

---

## See also

- [README — API reference and quickstart](../README.md)
- [examples/hello_cnc/](../examples/hello_cnc/) — minimal motion sanity check
- [examples/liquid_handling/](../examples/liquid_handling/) — full template
- [Opentrons Labware Creator](https://labware.opentrons.com/#/create)
- [Opentrons shared-data labware definitions](https://github.com/Opentrons/opentrons/tree/edge/shared-data/labware/definitions)
