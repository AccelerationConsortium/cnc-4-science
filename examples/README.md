# Examples

Reference projects that exercise `cnc_machine_core` end-to-end. Use these as
**templates** when building your own application — copy the closest match and
edit it.

| Example | Hardware | Software |
| ------- | -------- | -------- |
| [`hello_cnc/`](hello_cnc/) | [ASSEMBLY_INSTRUCTIONS.md](hello_cnc/ASSEMBLY_INSTRUCTIONS.md) (~1 hr) — base CNC only | [README](hello_cnc/README.md) — **first-time CNC sanity check** |
| [`liquid_handling/`](liquid_handling/) | [ASSEMBLY_INSTRUCTIONS.md](liquid_handling/ASSEMBLY_INSTRUCTIONS.md) (~1 hr) | [README](liquid_handling/README.md) |
| [`vacuum_pick_and_place/`](vacuum_pick_and_place/) | [ASSEMBLY_INSTRUCTIONS.md](vacuum_pick_and_place/ASSEMBLY_INSTRUCTIONS.md) (~1 hr) | [README](vacuum_pick_and_place/README.md) |

## Standard user journey

Every example follows the same 3-step flow — pick one and follow its README:

1. **Hardware setup (~1 hr)** — order/print parts (BOM in `ASSEMBLY_INSTRUCTIONS.md`),
   wire the tool, mount the deck.
2. **Software setup** — `python -m venv .venv` → activate → `pip install -r requirements.txt`.
3. **Configure & run** — edit `tools/cnc_config.yaml` (COM port, bounds) and the
   tool config, then run the protocol in `protocols/`.

> [`hello_cnc/`](hello_cnc/) is a **first-time CNC sanity check** (homes,
> jogs, toggles the spindle) — run it once when you set up a new machine.
> The other examples don't depend on it.
>
> The `z_heights:` shipped in each example's `cnc_config.yaml` are calibrated
> for the reference build in its `ASSEMBLY_INSTRUCTIONS.md`. If you reproduce
> that build exactly, leave them alone; if anything differs (tip length, deck
> shim, mount), remeasure by hand and edit `z_heights:` — see
> [docs/SETUP.md §4](../docs/SETUP.md#4-calibrate-z-heights).

To create a new example, follow [AGENTS.md](AGENTS.md) — it documents the
shared layout, config schema, driver-class pattern, and the conventions all
of the above follow.
