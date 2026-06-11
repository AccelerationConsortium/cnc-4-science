<h1> CNC MACHINE CODE </h1>

Authors: Owen Melville, Kelvin Chow

Last Updated: 2026-03-18

<h2> Overall description </h2>
This package can be used to control Genmitsu CNC machines. This is useful for accelerated discovery because you can put your tools onto the CNC machine.

Install from PyPI:

```bash
pip install cnc-4-science
```

Then import `cnc_machine_core` and use its methods to intuitively and seamlessly move the CNC machine with whatever scientific tools you want to incorporate. See `examples/liquid_handling/` for a full worked example.

> **New to the library?** Read [docs/SETUP.md](docs/SETUP.md) for a step-by-step
> walkthrough of building a new application: deck → labware → toolhead/driver →
> tool offsets → Z calibration → protocol. The section below is the quick API
> reference; SETUP.md is the long-form how-to.

<h3>Basic Functions:</h3>

- Home CNC machine
  
- Move to absolute points (x,y,z)
  
- Move to locations defined in a structured way (Eg move to Vial Position 0)

- Control of the spindle output
  
- Handles all gcode and CNC communication so you don't have to
  
- Makes sure you don't move the CNC machine to a position it can't go

- Automatic alarm detection and recovery (re-homes if a limit switch is triggered)

- Orthogonal waypoint moves for collision avoidance between deck slots

 <h3>API Reference</h3>

| Method | Description |
|---|---|
| `home()` | Homes the robot and parks at the origin |
| `origin()` | Moves the robot to the origin |
| `connect()` / `close()` | Open and close serial connection to the CNC |
| `move_to_point(x, y, z)` | Move to absolute coordinates |
| `move_to_point_safe(x, y, z)` | Raises Z to clearance first, moves XY, then lowers Z. Prevents collisions with labware |
| `move_to_point_safe_orthogonal(x, y, z, waypoint, axis_order)` | Moves one axis at a time through waypoints for collision avoidance. Axis orders: `yxy`, `xyx`, `xyxy`, `yxyx` |
| `move_to_location(location, index)` | Move to a named location at the given index |
| `spindle_on(speed)` | Turn on spindle at given RPM (M3) |
| `spindle_off()` | Turn off spindle (M5) |
| `is_alarm()` | Returns `True` if GRBL is in alarm state (e.g. limit switch triggered) |
| `recover_if_alarm()` | Checks for alarm and auto-homes to recover. Called internally before every move |

<h3>Deck and Labware</h3>

The `cnc_deck` module provides `Well`, `Labware`, and `Deck` objects for coordinate resolution:

```python
from cnc_machine_core import Deck

deck = Deck()                                        # standard 4-slot deck
plate = deck.load_labware("1", "labware/my_labware.json")  # returns Labware

well = plate["A1"]                                   # Well object
x, y, z = well.position()                            # absolute CNC coordinates
x, y, z = well.position(offset={"x": 6.75, "y": -4.0})  # with tool offset

for well in plate.wells():                           # iterate in ordering
    print(well.name, well.position())
```

Alternative deck layouts are in `deck/` (pass by name or path):
- `cnc_4_slot_deck.json` — standard 4-slot (2×2) **[default]**
- `cnc_1_slot_deck.json` — single slot at origin (open deck, no labware required)

Labware definitions are created using the [Opentrons Labware Creator](https://labware.opentrons.com/#/create). Only the X and Y well coordinates from the Opentrons JSON are used. Z heights are defined per-protocol as calibrated constants, since Z depends on the specific tool and labware combination rather than the labware geometry alone.

Custom labware JSON files go in `labware/`. See the existing files there for reference.

<h3>Direct Positioning (No Labware)</h3>

For simpler setups that don't need labware definitions, use the open deck and move directly to absolute coordinates:

```python
from cnc_machine_core import Deck

deck = Deck("cnc_1_slot_deck")           # built-in name; or pass a path to custom JSON
# No labware needed — move to raw coordinates
cnc.move_to_point_safe(x=100, y=50, z=-20)
```

Alternatively, position arrays can be defined in a YAML file and addressed by index using `move_to_location()`. This is useful for regular grids where you don't need named wells. Positions are defined in `location_status.yaml`:

```yaml
vial_rack:
  num_x: 2          # columns
  num_y: 4          # rows
  x_origin: 166.5   # first position X
  y_origin: 125     # first position Y
  z_origin: 0
  x_offset: 36      # spacing between columns
  y_offset: -36     # spacing between rows
```

The location index moves through a full column before advancing to the next. Index 0 is at the origin.

<img width="1580" height="1190" alt="image" src="https://github.com/user-attachments/assets/2022a495-b026-4f38-a9e6-7f2ad14fdd05" />

<h3>Z Calibration Helper</h3>

A Z calibration script is included at `examples/liquid_handling/z_helper.py`. It moves the CNC to a selected slot/well (with tool offset applied), then lets the user step Z up and down at three granularity levels (coarse, medium, fine) to find the correct working height. This is much faster than manually jogging and reading coordinates. Copy it into your own application and update the deck/labware/tool configuration for your setup.

<h3>Deck State</h3>

The `deck_state` module tracks per-well status across all deck slots with YAML persistence:

```python
from cnc_machine_core import DeckState

ds = DeckState()
ds.init_wells_from_labware("1", plate)              # from Labware object
ds.init_from_preset({"1": {"A1": "sample"}})         # override specific wells
ds.set_status("1", "A1", "processed")               # update (auto-saves)
loc = ds.find_next(["1", "2"], "sample")             # first match -> ("1", "A2")
ds.count(["1"], "processed")                         # count by status
ds.summary()                                         # print slot breakdown
```

Status strings are application-defined — use whatever makes sense for your workflow.
A sample preset is in `examples/liquid_handling/deck_preset.yaml`.

<h3>Starting a New Application</h3>

After physically setting up the CNC machine, run `examples/hello_cnc/hardware_check.py` as a sanity check to verify the serial connection, homing, movement, and spindle all work correctly. Edit `examples/hello_cnc/cnc_config.yaml` to match your COM port and bounds before running:

```bash
python examples/hello_cnc/hardware_check.py
```

Once the hardware check passes, create your application from the starter example at `examples/liquid_handling/` (a full worked example using a Sartorius Picus 2 pipette for serial dilution).

1. **Copy the example** — copy `examples/liquid_handling/` to a new repository or directory
2. **Install cnc-4-science** — install as a dependency in your project's virtual environment:

   **Linux / macOS / Raspberry Pi:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install cnc-4-science
   ```

   **Windows:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install cnc-4-science
   ```

   Or for local editable development against an unreleased core:
   ```bash
   pip install -e path/to/cnc-machine
   ```

3. **Configure your CNC** — edit `tools/cnc_config.yaml` (COM port, baud, bounds). Then load it in your script with `CNC_Machine.from_config("tools/cnc_config.yaml")`
4. **Add your labware** — place custom labware JSON files in `custom_labware/`, or load standard Opentrons labware via `opentrons_shared_data.labware.load_definition(...)`
5. **Configure each tool** — create `tools/<tool>_config.yaml` per pipette/effector with COM port, mounting offset, Z heights, and any tool-specific parameters
6. **Calibrate Z heights** — run `python z_helper.py` to find working Z for each tool + labware combo; copy results into the tool's `<tool>_config.yaml`
7. **Validate** — set `virtual: true` in `tools/cnc_config.yaml` for a dry run, then on hardware
8. **Implement tools** — use `tools/picus_pipette.py` as a pattern for wrapping new tools

<h4>Architecture</h4>

```
cnc-4-science (library, on PyPI)         Your Application (copied example)
├── src/cnc_machine_core/                  ├── protocols/
│   ├── cnc_machine.py  (motion)            │   └── serial_dilution_demo.py
│   ├── cnc_deck.py     (deck/wells)        ├── z_helper.py
│   ├── deck_state.py   (state)             ├── deck_preset.yaml
│   ├── deck/           (definitions)       ├── custom_labware/
│   └── labware/        (labware JSON)      ├── tools/
├── examples/                                │   ├── cnc_config.yaml          (CNC + deck layout + Z heights)
│   ├── hello_cnc/                          │   ├── picus_config.yaml        (tool: port, offset, volumes)
│   └── liquid_handling/                    │   ├── picus_pipette.py         (tool wrapper)
└── pyproject.toml                           │   └── picus_driver.py          (vendored low-level driver)
                                              └── requirements.txt  (`cnc-4-science`)
```

- **Library** owns: machine control, deck/labware primitives, standard definitions
- **App** owns: concrete tool implementations, calibrated configs, workflow protocols

<h4>Tool Contract</h4>

Every tool class must follow this interface:

```python
class MyTool:
    def __init__(self, cnc_machine, tool_config):
        self.cnc = cnc_machine
        self.offset = tool_config.get("offset", {"x": 0, "y": 0, "z": 0})
        # extract parameters from tool_config["parameters"]
```

See `examples/liquid_handling/tools/picus_pipette.py` for a working reference implementation.

<h3>Advice on Integration with Scientific Instruments</h3>

- Create a separate python file for each tool (camera, force sensor, syringe pump, etc.)
  
- Create an instrument class that imports cnc_machine along with the python files for each tool (eg fraction_collector.py)
  
- In your instrument class make methods that intuitively describe the general actions of your instrument (eg dispense_fraction)
  
- Make your workflows in seperate python files or Jupyter notebook files that create an instance of your instrument class
  
- This will make your workflows as clean and simple as possible while hard to mess up!
