# Changelog

## Unreleased
- **CAD filenames normalized to kebab-case.** Renamed `M6_thumb_screw` \u2192 `m6-thumb-screw`, `suction_cup_holder` \u2192 `suction-cup-holder`, `sartorius_24_tiprack_5000ul` \u2192 `sartorius-24-tiprack-5000ul`, and `sartorius-5000uL-pipette-tool-holder-{A,B}` \u2192 `sartorius-5000ul-pipette-tool-holder-{a,b}` so every STL/STEP file follows the same lowercase-kebab convention. References in [`liquid_handling/ASSEMBLY_INSTRUCTIONS.md`](examples/liquid_handling/ASSEMBLY_INSTRUCTIONS.md), [`vacuum_pick_and_place/ASSEMBLY_INSTRUCTIONS.md`](examples/vacuum_pick_and_place/ASSEMBLY_INSTRUCTIONS.md), and both BOM CSVs updated to match. The Opentrons labware load name `sartorius_24_tiprack_5000ul` (in `custom_labware/*.json`, `cnc_config.yaml`, `deck_preset.yaml`) stays snake_case \u2014 that's the Opentrons load-name convention and must match the JSON filename for `load_definition()` to resolve.
- **CAD files moved per-example.** The top-level `3d printing files/` dump is gone; each example now ships its 3D-printed parts in its own `cad/{step,stl}/` folder.
  - [`examples/liquid_handling/cad/`](examples/liquid_handling/cad/): `100mm-z-spacer`, `deck-slot-5mm-offset`, `deck-slot-standard`, `m6-thumb-screw`, `sartorius-24-tiprack-5000ul`, `sartorius-5000ul-pipette-tool-holder-a`, `sartorius-5000ul-pipette-tool-holder-b`.
  - [`examples/vacuum_pick_and_place/cad/`](examples/vacuum_pick_and_place/cad/): `deck-slot-standard`, `m6-thumb-screw`, `suction-cup-holder`, `vacuum-gripper-toolhead-mount`, `vacuum-pump-mounting-plate`.
  - Shared parts (`deck-slot-standard`, `m6-thumb-screw`) are duplicated under each example so each one is a self-contained build (\u003c1 MB extra total).
- **Assembly typo fixes.** `deck-slot-5mm-taller.stl` \u2192 `deck-slot-5mm-offset.stl`, `M6-thumb-screws.stl` \u2192 `m6-thumb-screw.stl`, `suction-cup-holder.stl` (was unchanged but linked) in the two `ASSEMBLY_INSTRUCTIONS.md` and BOM CSVs. Every print-row in the BOM is now a clickable link to its `cad/stl/` file.

## 0.9.1 - 2026-06-15
- **Separate PyPI README.** `pyproject.toml` now points `readme` at a new `README_PYPI.md` — a slim, text-only API summary (`CNC_Machine`, `Deck`, `DeckState`, minimal `cnc_config.yaml`) with a link out to the full GitHub README for hardware/build docs and example projects. The GitHub `README.md` stays as the rich landing page (hero gifs, reference applications, full API reference).

## 0.9.0 - 2026-06-15
- **COM-port discovery docs.** Finding the GRBL board's serial port is not self-discoverable, so [docs/SETUP.md §0](docs/SETUP.md#finding-the-serial-port-windows--macos--linux) now has a *Finding the serial port (Windows / macOS / Linux)* subsection: a table mapping each example to the exact `cnc_config.yaml` (and `picus_config.yaml` for liquid_handling) that needs editing, the unplug/list/plug-in identification trick, and per-OS commands (`Get-CimInstance Win32_SerialPort`, `ls /dev/tty.*`, `ls /dev/ttyUSB* /dev/ttyACM*`) plus CH340 driver / `dialout` group notes. Each example README and the root README's Quick start now link to it inline.
- **README hero**: added side-by-side preview gifs (5\u00d7 speed) at the top of the README for the liquid-handling and pick-and-place examples; each gif links out to the full-length YouTube recording. Renamed the *Reference applications* table column from `Photos / videos` to `Sample workflow video` and linked the same YouTube videos there (`hello_cnc` left blank). Source `media/*.mp4` recordings are too large for git and are hosted on YouTube; `media/*.mp4`/`*.mov`/`*.webm` are now gitignored, only the preview gifs are tracked.
- **Breaking: `Deck(deck_definition)` is now required \u2014 no default.** Previously `Deck()` silently picked `cnc_4_slot_deck`. Callers must now pass the deck name explicitly (`Deck("cnc_4_slot_deck")` for the Genmitsu 3018 layout, `Deck("cnc_1_slot_deck")` for the open layout, or a path to a custom JSON) so the CNC footprint is visible at the call site. Updated `examples/vacuum_pick_and_place/app_runtime.py`, README, and [docs/SETUP.md](docs/SETUP.md).- **Clarified that the built-in `cnc_4_slot_deck` is sized for the Genmitsu 3018-PROVer V2** (~300×180 mm bed). Larger CNCs (3040, 6040, …) should copy the JSON and remeasure slot corners. Note added to README, [docs/SETUP.md](docs/SETUP.md), [examples/AGENTS.md](examples/AGENTS.md), the `Deck` docstring, and both example `cnc_config.yaml` files.
- **Per-example `z_helper.py` removed.** Each example's shipped `z_heights:` is calibrated for the reference build in its `ASSEMBLY_INSTRUCTIONS.md`; if a downstream build differs, remeasure by hand (jog with [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations) or `cnc.move_to_point(...)` from a Python REPL) and edit the `z_heights:` block. Procedure documented in [docs/SETUP.md §4](docs/SETUP.md#4-calibrate-z-heights).
- **Smoke-test step dropped from per-example READMEs.** `hello_cnc/hello_cnc.py` is a one-time CNC sanity check for new hardware, not a prerequisite for every protocol. The standard user journey in [examples/README.md](examples/README.md) is now 3 steps (hardware → software → configure & run).
- Updated [examples/AGENTS.md](examples/AGENTS.md) (dropped §6 z_helper.py section, README guidance) and top-level [README.md](README.md) (Quick start, Z calibration section) to match.
- **BOM tables populated** in each example's `ASSEMBLY_INSTRUCTIONS.md`. Each example gets a sibling `<project>_bom.csv` (`hello_CNC_bom.csv`, `liquid_handling_CNC_demo_bom.csv`, `pick_and_place_CNC_demo_bom.csv` — matching the `Project` field in the upstream spreadsheet) so the parts list is diffable and renders directly on GitHub. The upstream master spreadsheet is kept locally only and is gitignored.
- New `examples/hello_cnc/ASSEMBLY_INSTRUCTIONS.md` covering the base-CNC build (the smoke test had no assembly doc before).
- **License changed from MIT to GPL-3.0-or-later.** Updated `LICENSE` to the full GNU GPL v3 text and `pyproject.toml`'s `license` field accordingly.
- **README restructured** around the 3-step workflow (Mount a Tool → Define the Deck → Write a Workflow). Trimmed redundancy: removed the long "Starting a New Application" section (now covered by [docs/SETUP.md](docs/SETUP.md) and the per-example READMEs). Moved authors and acknowledgements to the bottom. Added an acknowledgement to the [KABLab](https://sites.bu.edu/kablab/) at Boston University with a citation to *List et al., "ASMI: An automated, low-cost indenter for soft matter", HardwareX 20, e00601 (2024)*.
- **Z calibration helper docs**: the helper is shipped per-example (`examples/<name>/z_helper.py`) — README and `docs/SETUP.md` now link to both shipped variants instead of only the liquid_handling one.
- **Repo cleanup**:
  - Removed `tests/` — the only test file was broken (wrong import path, stale bounds assertions) and `examples/hello_cnc/hello_cnc.py` is the de-facto hardware smoke test.
  - Removed local build artifacts from the working tree (`dist/`, `.pytest_cache/`, `__pycache__/`, `src/cnc_4_science.egg-info/`); added `.pytest_cache/` to `.gitignore`.
- **Hardware docs (placeholders)**: each example now ships a self-contained `ASSEMBLY_INSTRUCTIONS.md` next to its README (BOM, base CNC + deck stages, per-tool wiring, CAD index). Targets a ~1-hour build once parts are in hand.
- **README structure standardized** across examples: every example README now follows the same 5-step user journey — hardware setup (link to `ASSEMBLY_INSTRUCTIONS.md`) → software setup (venv + `pip install`) → smoke test (`hello_cnc`) → calibrate Z → run protocol. New top-level `examples/README.md` summarizes the journey and indexes every example. The root README adds a quick-start block and a media-placeholder table for per-example photos/videos.
- **Examples scaffolding guide**: new [`examples/AGENTS.md`](examples/AGENTS.md) documenting the shared layout, config schema, and driver-class pattern for new examples.
- **New example**: `examples/vacuum_pick_and_place/` — physical tic-tac-toe over a CNC gantry with a vacuum gripper. Supports 1-player vs Easy/Medium/Hard AI and 2-player modes; pieces are picked from a 15-well storage rack and placed on a 15-well game board (3x3 play area). Adapted from `kelvinchow23/cnc-tictactoe` without SiLA. Follows the `liquid_handling/` template: `tools/cnc_config.yaml` + `tools/vacuum_config.yaml`, `tools/vacuum_gripper.py` (thin wrapper that drives the CNC's spindle output via `cnc.spindle_on()` / `cnc.spindle_off()` instead of a separate serial port — the vacuum pump is wired to the GRBL spindle terminals), `protocols/tic_tac_toe.py` CLI entry point, custom labware in `custom_labware/`, deck preset in `presets/`.
  - **Shared `GameSession`** (`game_session.py`): single thread-safe state machine that owns the board, deck state, hardware handles, and AI. The CLI and the optional web frontend both drive the same `GameSession`, so behaviour is identical across surfaces. `app_runtime.py` factors out CNC/gripper bootstrap and shutdown.
  - **Optional lightweight web frontend** (`web/app.py` + `web/static/`): FastAPI app exposing `/api/state`, `/api/start`, `/api/move`, `/api/ai-move`, `/api/reset`, with a vanilla HTML/JS single-page UI. The board flashes the next CNC move before the gantry executes it (peek/play split). 1-/2-Player mode selector greys out AI difficulty and symbol-selection in 2-player mode. Reset replays the move history in reverse to clear the board. Run with `uvicorn web.app:app --host 0.0.0.0 --port 8000`. The CLI still works exactly as before — `python protocols/tic_tac_toe.py`.

## 0.8.1 - 2026-06-11
- **Docs**: added [`docs/SETUP.md`](docs/SETUP.md) — end-to-end walkthrough for new applications (deck definition → labware sourcing options → toolhead driver/wrapper → XY/Z offset measurement → Z calibration → protocol → dry-run). Linked from README quickstart.
  - Prerequisites now explicitly call out that `bounds:` is CNC-model-specific (shipped configs target the Genmitsu 3018) and recommend verifying real travel with a GRBL UI like [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations) before editing `cnc_config.yaml`.
  - Reworded the Z-from-labware-is-ignored rationale: too many independently-variable terms (deck shim, labware seating, tool mount, tip length) to maintain four agreeing calibrations, so we collapse to one empirical Z per (tool, labware, action) via `z_helper.py`.

## 0.8.0 - 2026-06-10
- **Deck definitions renamed and addressable by name**:
  - `deck/cnc_deck_definition.json` → `deck/cnc_4_slot_deck.json` (deckId `cnc_4_slot_deck`).
  - `deck/cnc_open.json` → `deck/cnc_1_slot_deck.json` (deckId `cnc_1_slot_deck`).
  - `Deck(deck_definition)` now accepts a built-in name (`Deck("cnc_1_slot_deck")`) or a path. Default is unchanged (`cnc_4_slot_deck`).
  - Example `tools/cnc_config.yaml` declares `deck.definition: cnc_4_slot_deck` so the deck choice is visible from config.
- **Examples reorganized**: merged `templates/` and `examples/` into a single `examples/` tree. Removed legacy `liquid_handling_demo/`. `examples/startup/` renamed to `examples/hello_cnc/`.
- **Liquid handling demo restructured** as a reusable template at `examples/liquid_handling/`:
  - Protocol moved to `protocols/serial_dilution_demo.py` (was `protocol.py` at root).
  - Per-tool config split: CNC is now treated as just another tool. Configs live under `tools/`:
    - `tools/cnc_config.yaml` — CNC machine, deck layout (slot→role), Z heights, virtual flag.
    - `tools/picus_config.yaml` — pipette tool (port, offset, default_speed, volumes). Replaces the old `tool_definitions.json`.
  - Consistent `picus_*` naming throughout: `tools/picus_pipette.py` (`PicusPipette` wrapper, was `SartoriusPipette`) and `tools/picus_driver.py` (vendored Picus 2 driver, was the `picus/` subpackage).
  - Deck slot assignment moved into `cnc_config.yaml` under `deck:` so it's visible from config instead of buried in the protocol.
- **New `CNC_Machine.from_config(path)` classmethod**: loads CNC port, baud, and bounds from a YAML config file. Accepts `**overrides` kwargs.
- `hardware_check.py` and `z_helper.py` updated to use `CNC_Machine.from_config(...)` and the new per-tool config paths.
- Z bounds in `z_helper.py` now derive from CNC config (`cnc.Z_LOW_BOUND` / `cnc.Z_HIGH_BOUND`) instead of hardcoded `-35..0`.

## 0.7.0 - 2026-06-09
- **Distribution renamed**: PyPI package is now `cnc-4-science` (was `cnc-machine-core`). Import name `cnc_machine_core` is unchanged.
- **Published to PyPI**: install with `pip install cnc-4-science`. Releases are automated via GitHub Actions on `v*` tags using PyPI Trusted Publisher (OIDC).
- **Liquid handling demo moved** from `liquid_handling_demo/serial_dilution/` (installable package) to `templates/serial_dilution_demo/` (flat-layout reference template). Run with `python protocol.py`; no install of the demo itself required.
- Added project metadata (license, authors, urls, classifiers, keywords) to `pyproject.toml`.
- Added `.github/workflows/publish.yml` for automated PyPI releases.
- Removed redundant top-level `requirements.txt` (dependencies now in `pyproject.toml`).
- Templates directory is excluded from the published wheel (only library code ships to PyPI).
- Synced `pyproject.toml` version to changelog (was stale at 0.1.0).

## 0.6.0 - 2026-06-09
- Restructured liquid handling demo as installable package `serial-dilution-demo` under `liquid_handling_demo/serial_dilution/`.
- Package layout: `src/serial_dilution_demo/` with `tools/` (incl. vendored picus driver) and `protocol.py` entry point.
- `pyproject.toml` declares `cnc-machine-core` as a local path dependency (uv editable) — no `sys.path` hacks.
- Entry point: `serial-dilution` CLI command (or `python -m serial_dilution_demo`).
- Standard labware loaded at runtime via `opentrons-shared-data`; only custom tip rack JSON stored locally.
- Added `Deck.load_labware_definition(slot_id, dict)` to `cnc_machine_core`.
- Added `opentrons-shared-data` to `cnc-machine-core` dependencies.

## 0.5.0 - 2026-03-18
- Restructured to standard `src/` layout: core modules now under `src/cnc_machine_core/`.
- Package imports changed: `from cnc_machine_core import CNC_Machine, Deck, DeckState`.
- Deck and labware JSON data files moved into the package.

## 0.4.1 - 2026-03-18
- Added `is_alarm()` method to check if GRBL is in alarm state.
- Added `recover_if_alarm()` method that auto-homes on alarm before moves.
- All move methods now call `recover_if_alarm()` before executing.
- `wait_until_idle()` now raises `RuntimeError` immediately on alarm instead of timing out after 60s.

## 0.4.0 - 2026-03-18
- Moved `DeckState` well status tracker to core as `deck_state` module.
- Removed app-specific `VALID_STATUSES` — statuses are now application-defined strings.
- Added `deck_state` to `pyproject.toml` exports.
- Added sample deck preset template at `templates/starter_app/presets/deck_preset.yaml`.
- Updated README with DeckState API docs and architecture diagram.

## 0.3.0 - 2026-03-18
- Redesigned `cnc_deck` module with `Well`, `Labware`, and `Deck` object model (Opentrons-inspired).
- `load_labware()` now returns a `Labware` object; wells accessed via `plate["A1"].position(offset=...)`.
- Old tuple-based convenience methods (`list_wells`, `get_well_position`) still work for backward compatibility.
- Added `deck/cnc_open.json` — single-slot open deck layout (no labware required).
- Updated starter template protocols to use new Well/Labware API.

## 0.2.0 - 2026-03-18
- Added `cnc_deck` module with standard `Deck` class for slot lookup, labware loading, well coordinate resolution, and well ordering.
- Added standard 4-slot deck definition at `deck/cnc_deck_definition.json`.
- Added starter application template at `templates/starter_app/` with sample tool, vacuum gripper template, tool definitions template, simple well-cycle protocol, and Z calibration helper.
- Updated `pyproject.toml` to export `cnc_deck` module and include deck/labware data files.
- Updated README with deck/labware API docs, "Starting a New Application" guide, architecture diagram, and tool contract specification.

## 0.1.3 - 2026-03-17
- Added `xyxy` and `yxyx` axis orders to `move_to_point_safe_orthogonal()` accepting dual waypoints for 4-step routing.
- Fixed `wait_until_idle()` serial buffer flush to avoid reading stale `ok` responses.

## 0.1.2 - 2026-03-13
- Added `move_to_point_safe_orthogonal()` method for axis-separated safe moves through a waypoint (Y->X->Y or X->Y->X).

## 0.1.1 - 2026-03-11
- Added `spindle_on(speed)` and `spindle_off()` methods using GRBL M3/M5 spindle commands.

## 0.1.0 - 2026-03-11
- Added `pyproject.toml` so `cnc_machine.py` can be installed as package `cnc-machine-core`.
- Declared runtime dependencies (`pyyaml`, `pyserial`) for clean installs.
