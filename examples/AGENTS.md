# Scaffolding a new `cnc-machine` example project

This file is a checklist for humans (or coding agents) creating a new project on
top of `cnc_machine_core`. It describes the conventions the existing examples —
[`liquid_handling/`](liquid_handling/) and
[`vacuum_pick_and_place/`](vacuum_pick_and_place/) — both follow, and the
minimum set of files you need to write.

The goal is "copy one of the existing examples, change the labware/tool, run."
If you find yourself reinventing one of the patterns below, stop and reuse it.

---

## 1. Directory layout

```
my_new_example/
├── README.md                 # what it does, how to run it
├── requirements.txt          # cnc-4-science + tool-specific libs (pyserial, etc.)
├── tools/
│   ├── cnc_config.yaml       # CNC + deck + Z heights + travel routing
│   ├── <tool>_config.yaml    # one YAML per physical tool (offset, RPM, delays)
│   └── <tool>.py             # driver class for that tool (VacuumGripper, ...)
├── custom_labware/           # *.json — your Opentrons-format labware definitions
│   └── *.json
├── presets/
│   └── *_preset.yaml         # starting deck-state for protocols that need one
├── protocols/
│   └── <protocol>.py         # entry point — `python protocols/<protocol>.py`
├── app_runtime.py            # `build_session()` factory (only if >1 entry point)
└── output/                   # state snapshots — git-ignored
```

Drop anything you don't need (e.g. `presets/` if the protocol has no persistent
deck state, `app_runtime.py` if there's only one entry point).

---

## 2. Configs — `tools/cnc_config.yaml`

**Schema is shared across all examples.** Copy
[`vacuum_pick_and_place/tools/cnc_config.yaml`](vacuum_pick_and_place/tools/cnc_config.yaml)
and edit the values. Required keys:

| Key | Purpose |
| --- | --- |
| `cnc.com_port` / `baud_rate` / `bounds` | Serial + travel envelope |
| `virtual` | `true` = log G-code only, no hardware |
| `move_speed` | mm/min for XY travel |
| `z_heights` | per-action Z (measured by hand once — see [docs/SETUP.md §4](../docs/SETUP.md#4-calibrate-z-heights)) |
| `deck.definition` | deck JSON id (e.g. `cnc_4_slot_deck`) — omit for default |
| `deck.slots` | **role-keyed** map, e.g. `storage: "3"`, `gameboard: "4"` |
| `travel` *(optional)* | dogleg routing — see [`vacuum_pick_and_place`](vacuum_pick_and_place/tools/cnc_config.yaml) |

Use **roles as keys** (`storage`, `gameboard`, `tiprack`, `waste`) — never bare
slot numbers in protocol code. The protocol reads `slots["storage"]` and stays
readable when you re-arrange the deck.

---

## 3. Configs — `tools/<tool>_config.yaml`

One file per physical tool. Required keys:

```yaml
toolId: vacuum_gripper         # used as the calibration key
offset:                        # XY offset from spindle center, mm
  x: 7.846
  y: 0.0
  z: 0.0
# Tool-specific knobs follow — RPM, delays, ports, etc.
vacuum_rpm: 1500
grip_delay_s: 0.5
place_delay_s: 3.5
```

The driver class (e.g. `tools/vacuum_gripper.py`) takes these as constructor
kwargs. Don't read YAML inside the driver — that's `app_runtime.py`'s job.

---

## 4. The driver class — `tools/<tool>.py`

Owns the *physical* tool. Pattern (see
[`tools/vacuum_gripper.py`](vacuum_pick_and_place/tools/vacuum_gripper.py)):

- Constructor takes `cnc` + plain config kwargs (no YAML, no Paths).
- `connect()` / `close()` for serial or auxiliary hardware.
- Action methods (`pick(x, y, z)`, `place(...)`, `pipette(...)`) take **machine
  coordinates already including the tool offset**. Compute the offset once at
  the call site via `labware[well].position(offset=tool.offset)`.
- Honor a `virtual` flag if the tool has its own hardware beyond the CNC.

---

## 5. The factory — `app_runtime.py` (optional)

Only needed if you have more than one entry point that shares wiring (e.g. CLI
+ web). See
[`vacuum_pick_and_place/app_runtime.py`](vacuum_pick_and_place/app_runtime.py).
Expose **one function**:

```python
def build_session() -> tuple[Session, CNC_Machine, Tool]:
    """Open CNC, load configs+labware, instantiate tool, return everything."""
```

and a matching `shutdown(cnc, tool, *, virtual)` so the CLI, web, and any test
harness can all reuse the same lifecycle.

If your project is a single script, skip this file and do the wiring inline at
the top of the protocol.

---

## 7. The protocol — `protocols/<protocol>.py`

The actual user-facing script. Conventions:

- `from app_runtime import build_session, shutdown` (or do the wiring inline if
  there's no `app_runtime.py`).
- Wrap the main body in `try/finally: shutdown(...)` so the gantry always
  parks and serial always closes.
- For interactive prompts, accept `q` (quit) and `r` (reset) at *every* input
  point — not just the top-level menu.
- Print one human-readable line per CNC action (`"  X: storage A1 -> board B2"`)
  so the operator can follow along.
- No `if __name__ == "__main__"` guard — these scripts aren't a package, they
  exist to be invoked directly.

---

## 8. README

Cover, in order: what the project does, hardware required (link to
`ASSEMBLY_INSTRUCTIONS.md`), install (`pip install -r requirements.txt`),
`tools/cnc_config.yaml` edits, and the run command. Note that `z_heights:`
are pre-calibrated for the reference build — link to
[docs/SETUP.md §4](../docs/SETUP.md#4-calibrate-z-heights) for the manual
remeasure procedure. Keep it short — the configs are self-documenting via
comments.
