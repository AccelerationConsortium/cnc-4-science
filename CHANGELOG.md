# Changelog

## [0.2.0] - 2026-03-10

### Added
- `fraction_collector/` package: deck-based instrument architecture for CNC fraction collection
- Deck definition (`deck/cnc_deck_definition.json`): 4-slot (2x2) deck layout, Opentrons-style JSON
- Tool definitions (`tools/tool_definitions.json`): configurable tool offsets and control interfaces
- `VialCapper` tool: Z-axis press for capping vials
- `VacuumGripper` tool: pick/place using CNC spindle as vacuum
- `DropCounter` tool: Vernier drop counter with integrated Runze valve control
- `FractionCollector` instrument class: deck + labware + tool orchestration with coordinate resolution (slot offset + well position + tool offset)
- Example protocol (`protocols/example_protocol.py`)
- Labware stored in root `labware/` directory (Opentrons JSON schema v2)
