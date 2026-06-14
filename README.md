<h1>cnc-4-science</h1>

> Turn a low-cost Genmitsu CNC into a self-driving lab module.

`cnc-4-science` is a Python control library for Genmitsu (GRBL) CNC routers
used as gantries for **scientific automation** — liquid handling, fraction
collection, vision-based capping, pick-and-place, fraction collection,
indentation, and any other workflow that maps cleanly to "move this tool to
that well and do something." Each module is built around a 3-step workflow:

| 1. Mount a Tool | 2. Define the Deck | 3. Write a Workflow |
| --- | --- | --- |
| Bolt a 3D-printed mount + your instrument onto the spindle carriage. Wire it through the GRBL spindle terminals (M3/M5) or a separate serial port. | Describe your labware and slot positions in YAML — Opentrons-compatible labware or custom JSON definitions. | Drive everything from Python: `cnc.move_to_location(...)`, `tool.do_thing()`. The library handles G-code, bounds checking, and alarm recovery. |

```bash
pip install cnc-4-science
```

---

## Reference applications

Each example below is a complete, copyable project. Order the parts, follow
the assembly guide (~1 hour), set up the venv, edit two YAML files, and run.

| Example | Tool | Workflow | Photos / videos |
| ------- | ---- | -------- | --------------- |
| [`hello_cnc/`](examples/hello_cnc/) | Stock spindle | Home, move, spindle on/off — the hardware smoke test | _TBD_ |
| [`liquid_handling/`](examples/liquid_handling/) | Sartorius Picus 2 pipette | Serial dilution across a 24-well plate | _TBD_ |
| [`vacuum_pick_and_place/`](examples/vacuum_pick_and_place/) | Vacuum gripper (spindle-driven) | Physical tic-tac-toe — CLI + optional browser UI | _TBD_ |

See [`examples/README.md`](examples/README.md) for the standard 5-step user
journey every example follows.

---

## Quick start

```bash
# 1. Pick an example and read its README + ASSEMBLY_INSTRUCTIONS.md.
#    Order/print the parts, assemble the hardware (~1 hour).

# 2. From the example folder:
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows
# source .venv/bin/activate      # Linux / macOS
pip install -r requirements.txt

# 3. Edit tools/cnc_config.yaml (COM port, travel bounds) and the tool config.

# 4. Smoke-test the machine:
python ../hello_cnc/hello_cnc.py

# 5. Calibrate Z heights, copy the values into cnc_config.yaml:
python z_helper.py

# 6. Run the protocol.
python protocols/<name>.py
```

> **New to the library?** Read [docs/SETUP.md](docs/SETUP.md) for the
> long-form software walkthrough (deck → labware → toolhead/driver →
> tool offsets → Z calibration → protocol).
>
> **Building your own application?** Copy [`examples/liquid_handling/`](examples/liquid_handling/)
> or [`examples/vacuum_pick_and_place/`](examples/vacuum_pick_and_place/) as
> a template — the conventions are documented in
> [`examples/AGENTS.md`](examples/AGENTS.md).

---

## API reference

### Motion

| Method | Description |
|---|---|
| `home()` / `origin()` | Home and park; or move to origin without homing. |
| `connect()` / `close()` | Open / close the serial connection to the controller. |
| `move_to_point(x, y, z)` | Absolute move (XYZ in mm). |
| `move_to_point_safe(x, y, z)` | Raise Z to clearance, move XY, lower Z. Prevents collisions with labware. |
| `move_to_point_safe_orthogonal(x, y, z, waypoint, axis_order)` | One-axis-at-a-time waypoint move (`yxy`, `xyx`, `xyxy`, `yxyx`). |
| `move_to_location(location, index)` | Move to a named position from `location_status.yaml`. |
| `spindle_on(rpm)` / `spindle_off()` | `M3` / `M5`. Doubles as the on/off for vacuum or solenoid tools wired to the spindle terminals. |
| `is_alarm()` / `recover_if_alarm()` | Alarm-state check + auto-rehome. Called internally before every move. |

### Deck and labware

The `cnc_deck` module provides `Well`, `Labware`, and `Deck` objects for
coordinate resolution:

```python
from cnc_machine_core import Deck

deck = Deck()                                                # standard 4-slot deck
plate = deck.load_labware("1", "labware/my_labware.json")    # returns Labware

well = plate["A1"]
x, y, z = well.position()
x, y, z = well.position(offset={"x": 6.75, "y": -4.0})       # with tool offset
```

Built-in decks (pass by name or path to a custom JSON):

- `cnc_4_slot_deck` — standard 4-slot (2×2) **[default]**
- `cnc_1_slot_deck` — single open slot at origin (no labware required)

Labware definitions are created with the
[Opentrons Labware Creator](https://labware.opentrons.com/#/create) — only
the XY well coordinates are used. Z heights are calibrated empirically per
(tool, labware, action) because they depend on the tool mount and labware
seating, not the labware geometry alone. See
[docs/SETUP.md §4](docs/SETUP.md#4-calibrate-z-heights).

### Direct positioning (no labware)

For simple setups, use the open deck and move to raw coordinates:

```python
from cnc_machine_core import Deck

deck = Deck("cnc_1_slot_deck")
cnc.move_to_point_safe(x=100, y=50, z=-20)
```

Regular grids without named wells can be described in YAML and addressed by
index via `move_to_location()`:

```yaml
vial_rack:
  num_x: 2          # columns
  num_y: 4          # rows
  x_origin: 166.5
  y_origin: 125
  z_origin: 0
  x_offset: 36
  y_offset: -36
```

The location index walks a full column before advancing.

<img width="1580" height="1190" alt="vial_rack" src="https://github.com/user-attachments/assets/2022a495-b026-4f38-a9e6-7f2ad14fdd05" />

### Deck state

The `deck_state` module tracks per-well status across all slots with YAML
persistence:

```python
from cnc_machine_core import DeckState

ds = DeckState()
ds.init_wells_from_labware("1", plate)
ds.init_from_preset({"1": {"A1": "sample"}})
ds.set_status("1", "A1", "processed")                # auto-saves
loc = ds.find_next(["1", "2"], "sample")             # ("1", "A2")
ds.count(["1"], "processed")
ds.summary()
```

Status strings are application-defined. A sample preset is in
[`examples/liquid_handling/deck_preset.yaml`](examples/liquid_handling/deck_preset.yaml).

### Z calibration helper

Each example ships its own `z_helper.py` — copy-and-edit, because the helper
needs to know about that example's tool offset and labware. See
[`examples/liquid_handling/z_helper.py`](examples/liquid_handling/z_helper.py)
and
[`examples/vacuum_pick_and_place/z_helper.py`](examples/vacuum_pick_and_place/z_helper.py)
for the two shipped variants.

### Tool wrapper contract

Every tool class follows the same shape, so the protocols read the same way
across examples:

```python
class MyTool:
    def __init__(self, cnc_machine, tool_config):
        self.cnc = cnc_machine
        self.offset = tool_config.get("offset", {"x": 0, "y": 0, "z": 0})
        # extract parameters from tool_config["parameters"]
```

See
[`examples/liquid_handling/tools/picus_pipette.py`](examples/liquid_handling/tools/picus_pipette.py)
for a wrapper around a vendor serial driver, and
[`examples/vacuum_pick_and_place/tools/vacuum_gripper.py`](examples/vacuum_pick_and_place/tools/vacuum_gripper.py)
for a wrapper that drives the CNC's spindle terminals directly (no separate
serial port).

---

## Authors

- Owen Melville
- Kelvin Chow

## Acknowledgements

This library was inspired by the open-source CNC-based scientific instruments
developed by the [KABLab](https://sites.bu.edu/kablab/) at Boston University.
In particular:

> List, D.; Gardner, A.; Claure, I.; Wong, J. Y.; Brown, K. A.
> *ASMI: An automated, low-cost indenter for soft matter.*
> HardwareX **20**, e00601 (2024).
> [doi:10.1016/j.ohx.2024.e00601](https://doi.org/10.1016/j.ohx.2024.e00601)

If you use `cnc-4-science` in published work, please cite the paper above
alongside this repository.

## License

GNU General Public License v3.0 or later. See [LICENSE](LICENSE).
