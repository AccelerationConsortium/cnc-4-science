# Changelog

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
