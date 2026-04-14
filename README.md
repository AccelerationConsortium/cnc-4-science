<h1> CNC MACHINE CODE </h1>

Authors: Owen Melville, Kelvin Chow

Last Updated: 2026-03-18

<h2> Overall description </h2>
This package can be used to control Genmitsu CNC machines. This is useful for accelerated discovery because you can put your tools onto the CNC machine. All you need is to install the packages in requirements.txt then you can import cnc_machine.py and use its methods to intuitively and seemlessly move the cnc machine with whatever scientific tools you want to incorporate. 

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

Alternative deck layouts are in `deck/`:
- `cnc_deck_definition.json` — standard 4-slot (2×2)
- `cnc_open.json` — single slot at origin (open deck, no labware required)

Labware definitions are created using the [Opentrons Labware Creator](https://labware.opentrons.com/#/create). Only the X and Y well coordinates from the Opentrons JSON are used. Z heights are defined per-protocol as calibrated constants, since Z depends on the specific tool and labware combination rather than the labware geometry alone.

Custom labware JSON files go in `labware/`. See the existing files there for reference.

<h3>Direct Positioning (No Labware)</h3>

For simpler setups that don't need labware definitions, use the open deck and move directly to absolute coordinates:

```python
from cnc_machine_core import Deck

deck = Deck(deck_definition="deck/cnc_open.json")
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

A starter Z calibration script is included at `templates/starter_app/protocols/z_helper.py`. It moves the CNC to a selected slot/well (with tool offset applied), then lets the user step Z up and down at three granularity levels (coarse, medium, fine) to find the correct working height. This is much faster than manually jogging and reading coordinates.

Note: the helper requires the deck and labware to be configured for your application. The template version in the core repo uses a generic single-slot setup, so you will likely need to copy it into your application and update the deck/labware/tool configuration to match your actual setup before it is useful.

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
A sample preset is in `templates/starter_app/presets/deck_preset.yaml`.

<h3>Starting a New Application</h3>

After physically setting up the CNC machine, run `examples/startup/hardware_check.py` as a sanity check to verify the serial connection, homing, movement, and spindle all work correctly. Update the COM port and axis bounds in the script to match your setup before running:

```bash
python examples/startup/hardware_check.py
```

Once the hardware check passes, create your application from the starter template:

1. **Copy the template** — copy `templates/starter_app/` to a new repository
2. **Install cnc-machine-core** — install as a dependency in your project's virtual environment:

   **Linux / macOS:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install git+https://github.com/AccelerationConsortium/cnc-4-science.git
   ```

   **Windows:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install git+https://github.com/AccelerationConsortium/cnc-4-science.git
   ```

   Or for local editable development:
   ```bash
   pip install -e path/to/cnc-machine
   ```

3. **Add your labware** — place labware JSON files in the core `labware/` directory or your own project
4. **Configure slots** — edit `LABWARE_BY_SLOT` in your protocols to map slots to labware
5. **Calibrate tool offsets** — measure and update `tools/tool_definitions.json` with real x/y/z offsets
6. **Calibrate Z heights** — run `protocols/z_helper.py` to find working Z for each tool + labware combo
7. **Validate** — run `protocols/simple_well_cycle.py` in virtual mode, then on hardware
8. **Implement tools** — use `tools/vacuum_gripper.py` as a starting point for custom tools

<h4>Architecture</h4>

```
cnc-machine (core)                     Your Application
├── src/cnc_machine_core/                ├── tools/
│   ├── cnc_machine.py  (motion)         │   ├── your_tool.py
│   ├── cnc_deck.py     (deck/wells)     │   └── tool_definitions.json
│   ├── deck_state.py   (state)          ├── protocols/
│   ├── deck/           (definitions)    │   └── your_workflow.py
│   └── labware/        (labware JSON)   ├── presets/
├── templates/          (starter app)    │   └── my_preset.yaml
└── pyproject.toml                       └── ...
```

- **Core** owns: machine control, deck/labware primitives, standard definitions, starter templates
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

See `templates/starter_app/tools/vacuum_gripper.py` for a complete template and standard reference.

<h3>Advice on Integration with Scientific Instruments</h3>

- Create a separate python file for each tool (camera, force sensor, syringe pump, etc.)
  
- Create an instrument class that imports cnc_machine along with the python files for each tool (eg fraction_collector.py)
  
- In your instrument class make methods that intuitively describe the general actions of your instrument (eg dispense_fraction)
  
- Make your workflows in seperate python files or Jupyter notebook files that create an instance of your instrument class
  
- This will make your workflows as clean and simple as possible while hard to mess up!
