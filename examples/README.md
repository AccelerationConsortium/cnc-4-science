# Examples

Reference projects that exercise `cnc_machine_core` end-to-end. Use these as
**templates** when building your own application — copy the closest match and
edit it.

| Example | What it shows |
| ------- | ------------- |
| [`hello_cnc/`](hello_cnc/) | Minimum-viable smoke test: connect, home, move, spindle on/off. **Run this first** after assembling the machine. |
| [`liquid_handling/`](liquid_handling/) | Serial-dilution protocol driven by a Sartorius Picus electronic pipette. Demonstrates the multi-tool config pattern and Opentrons standard labware. Hardware: [HARDWARE.md](liquid_handling/HARDWARE.md). |
| [`vacuum_pick_and_place/`](vacuum_pick_and_place/) | Physical tic-tac-toe board with a vacuum gripper. Demonstrates a thin-wrapper tool (vacuum driven by the GRBL spindle), interactive CLI, optional FastAPI web frontend, and a shared `GameSession` state machine. Hardware: [HARDWARE.md](vacuum_pick_and_place/HARDWARE.md). |

Each example owns its own per-tool hardware docs (`HARDWARE.md`). The shared
base CNC + deck are documented at [`docs/hardware/`](../docs/hardware/).

To create a new example, follow [AGENTS.md](AGENTS.md) — it documents the
shared layout, config schema, driver-class pattern, and the conventions all
of the above follow.
