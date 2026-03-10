"""Example protocol demonstrating deck setup, labware loading, and tool usage."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cnc_machine import CNC_Machine
from fraction_collector.fraction_collector import FractionCollector

# --- Initialize CNC in virtual mode for testing ---
cnc = CNC_Machine(com="COM5", virtual=True)
cnc.connect()
cnc.home()

# --- Create FractionCollector ---
fc = FractionCollector(cnc)

# --- Load labware onto deck slots ---
fc.load_labware("1", "labware/vialtrayholder_25_tuberack_1000ul.json")
fc.load_labware("2", "labware/axygen_96_wellplate_500ul.json")

# --- Load tools ---
fc.load_tools_from_json("fraction_collector/tools/tool_definitions.json")

# --- Move to specific wells ---
fc.move_to_well("1", "A1")
fc.move_to_well("1", "B3")
fc.move_to_well("2", "H12")

# --- Use a tool: vial capper ---
capper = fc.get_tool("vial_capper")
x, y, z = fc.get_well_position("1", "A1")
capper.press(x, y, z)

# --- Use a tool: vacuum gripper ---
gripper = fc.get_tool("vacuum_gripper")
x1, y1, z1 = fc.get_well_position("2", "A1")
x2, y2, z2 = fc.get_well_position("1", "A1")
gripper.pick(x1, y1, z1)
gripper.place(x2, y2, z2)

# --- Iterate through all wells in a labware ---
for well_name in fc.list_wells("1"):
    fc.move_to_well("1", well_name)

cnc.origin()
cnc.close()
