# cnc-4-science

Python control library for **low-cost, easy-to-assemble, open-source GRBL CNC
routers** used as the gantry for scientific automation — liquid handling,
pick-and-place, fraction collection, anything that fits the pattern
"move this tool to that well and do something."

Reference hardware is the Genmitsu 3018-PROVer V2, but the library is
GRBL-generic.

Full docs, hardware build guides, and end-to-end example projects (liquid
handling, vacuum pick-and-place) live on GitHub:
<https://github.com/AccelerationConsortium/cnc-4-science>.

## Install

```bash
pip install cnc-4-science
```

Python 3.9+.

## API at a glance

Public surface is exported from `cnc_machine_core`:

```python
from cnc_machine_core import CNC_Machine, Deck, DeckState
```

### `CNC_Machine` — motion + spindle

| Method                                              | Purpose                                                                 |
| --------------------------------------------------- | ----------------------------------------------------------------------- |
| `CNC_Machine.from_config(path, **overrides)`        | Construct from a YAML config (`com_port`, `baud_rate`, `bounds`).       |
| `connect()` / `close()`                             | Open / close the GRBL serial connection.                                |
| `home()` / `origin()`                               | Home and park; or move to origin without homing.                        |
| `move_to_point(x, y, z)`                            | Absolute move (mm).                                                     |
| `move_to_point_safe(x, y, z)`                       | Raise Z to clearance, move XY, lower Z. Avoids deck collisions.         |
| `move_to_point_safe_orthogonal(x, y, z, waypoint, axis_order)` | One-axis-at-a-time waypoint move (`yxy`, `xyx`, `xyxy`, `yxyx`). |
| `move_to_location(location, index)`                 | Move to a named grid position from `location_status.yaml`.              |
| `spindle_on(rpm)` / `spindle_off()`                 | `M3` / `M5`. Also the on/off for vacuum or solenoid tools wired to the spindle terminals. |
| `is_alarm()` / `recover_if_alarm()`                 | GRBL alarm state check + auto-rehome (called internally before moves).  |

### `Deck` + `Labware` — coordinate resolution

```python
from cnc_machine_core import Deck
from opentrons_shared_data.labware import load_definition

deck = Deck("cnc_4_slot_deck")   # built-in: 4-slot, sized for the Genmitsu 3018
# deck = Deck("cnc_1_slot_deck")   # built-in: open / single slot
# deck = Deck("path/to/my_deck.json")  # custom JSON

# Standard SBS labware by Opentrons load name:
plate = deck.load_labware_definition(
    "1", load_definition("corning_96_wellplate_360ul_flat", 1)
)

# Or a custom JSON for non-SBS gear:
# plate = deck.load_labware("1", "custom_labware/my_rack.json")

x, y, z = plate["A1"].position()                       # absolute machine coordinates
x, y, z = plate["A1"].position(offset=tool.offset)     # apply tool's XY/Z mount offset
```

There is no default deck — pass an explicit name (or path) so the CNC
footprint is visible at the call site.

### `DeckState` — per-well status tracking

```python
from cnc_machine_core import DeckState

ds = DeckState()
ds.init_wells_from_labware("1", plate)
ds.init_from_preset({"1": {"A1": "sample"}})
ds.set_status("1", "A1", "processed")        # auto-saves to YAML
loc = ds.find_next(["1", "2"], "sample")     # ("1", "A2")
ds.count(["1"], "processed")
ds.summary()
```

Status strings are application-defined.

### Minimal config

`cnc_config.yaml`:

```yaml
cnc:
  com_port: COM4          # Windows: COMx | macOS: /dev/tty.usbserial-* | Linux: /dev/ttyUSB0
  baud_rate: 115200
  bounds:
    x: [0, 280]
    y: [0, 180]
    z: [-37, 0]

virtual: false            # true = dry-run; log G-code only, no hardware
```

`bounds:` must match your physical CNC envelope; the shipped values are for
the Genmitsu 3018.

## License

GNU General Public License v3.0 or later.
