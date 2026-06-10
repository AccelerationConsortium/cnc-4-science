# Changelog

## 0.8.0 - 2026-06-10
- **Deck definitions renamed and addressable by name**:
  - `deck/cnc_deck_definition.json` → `deck/cnc_4_slot_deck.json` (deckId `cnc_4_slot_deck`).
  - `deck/cnc_open.json` → `deck/cnc_1_slot_deck.json` (deckId `cnc_1_slot_deck`).
  - `Deck(deck_definition)` now accepts a built-in name (`Deck("cnc_1_slot_deck")`) or a path. Default is unchanged (`cnc_4_slot_deck`).
  - Example `tools/cnc_config.yaml` declares `deck.definition: cnc_4_slot_deck` so the deck choice is visible from config.
- **Examples reorganized**: merged `templates/` and `examples/` into a single `examples/` tree. Removed legacy `liquid_handling_demo/`. `examples/startup/` renamed to `examples/hello_cnc/`.
- **Liquid handling demo restructured** as a reusable template at `examples/liquid_handling/picus_pipette/`:
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
