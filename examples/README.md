# Examples

Reference projects that exercise `cnc_machine_core` end-to-end. Use these as
**templates** when building your own application — copy the closest match and
edit it.

| Example | Hardware | Software |
| ------- | -------- | -------- |
| [`hello_cnc/`](hello_cnc/) | None beyond the base CNC | [README](hello_cnc/README.md) — **run this first as a smoke test** |
| [`liquid_handling/`](liquid_handling/) | [ASSEMBLY_INSTRUCTIONS.md](liquid_handling/ASSEMBLY_INSTRUCTIONS.md) (~1 hr) | [README](liquid_handling/README.md) |
| [`vacuum_pick_and_place/`](vacuum_pick_and_place/) | [ASSEMBLY_INSTRUCTIONS.md](vacuum_pick_and_place/ASSEMBLY_INSTRUCTIONS.md) (~1 hr) | [README](vacuum_pick_and_place/README.md) |

## Standard user journey

Every example follows the same 5-step flow — pick one and follow its README:

1. **Hardware setup (~1 hr)** — order/print parts (BOM in `ASSEMBLY_INSTRUCTIONS.md`),
   wire the tool, mount the deck.
2. **Software setup** — `python -m venv .venv` → activate → `pip install -r requirements.txt`.
3. **Configure** — edit `tools/cnc_config.yaml` (COM port, bounds) and the tool config.
4. **Smoke test** — run [`hello_cnc/hello_cnc.py`](hello_cnc/) to verify the gantry.
5. **Calibrate Z + run** — `python z_helper.py`, copy values to `cnc_config.yaml`,
   then run the protocol.

To create a new example, follow [AGENTS.md](AGENTS.md) — it documents the
shared layout, config schema, driver-class pattern, and the conventions all
of the above follow.
