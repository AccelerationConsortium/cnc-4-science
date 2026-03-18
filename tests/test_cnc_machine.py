import os
import pytest
import yaml

from cnc_machine import CNC_Machine

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
LOCATIONS_FILE = os.path.join(FIXTURES_DIR, "test_locations.yaml")


@pytest.fixture(autouse=True, scope="session")
def _create_fixture_files():
    """Write a small locations YAML used by several tests."""
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    data = {
        "vial_rack": {
            "num_x": 2,
            "num_y": 4,
            "x_origin": 100.0,
            "y_origin": 80.0,
            "z_origin": 0.0,
            "x_offset": 20.0,
            "y_offset": -15.0,
        },
        "single_pos": {
            "num_x": 1,
            "num_y": 1,
            "x_origin": 50.0,
            "y_origin": 50.0,
            "z_origin": -10.0,
            "x_offset": 0,
            "y_offset": 0,
        },
    }
    with open(LOCATIONS_FILE, "w") as f:
        yaml.safe_dump(data, f)
    yield


@pytest.fixture
def cnc():
    """A virtual CNC_Machine with default bounds and test locations."""
    return CNC_Machine(
        com="COM_TEST",
        virtual=True,
        locations_file=LOCATIONS_FILE,
    )


@pytest.fixture
def cnc_no_locations():
    """A virtual CNC_Machine with no locations file."""
    return CNC_Machine(com="COM_TEST", virtual=True)


# ── Initialization ──────────────────────────────────────────────


class TestInit:
    def test_defaults(self, cnc):
        assert cnc.VIRTUAL is True
        assert cnc.SERIAL_PORT == "COM_TEST"
        assert cnc.BAUD_RATE == 115200

    def test_bounds(self, cnc):
        assert cnc.X_LOW_BOUND == 0
        assert cnc.X_HIGH_BOUND == 270
        assert cnc.Z_LOW_BOUND == -35
        assert cnc.Z_HIGH_BOUND == 0

    def test_locations_loaded(self, cnc):
        assert "vial_rack" in cnc.LOCATIONS
        assert cnc.LOCATIONS["vial_rack"]["x_origin"] == 100.0

    def test_no_locations_file(self, cnc_no_locations):
        assert cnc_no_locations.LOCATIONS == {}

    def test_missing_locations_file(self):
        m = CNC_Machine(com="X", virtual=True, locations_file="nonexistent.yaml")
        assert m.LOCATIONS == {}


# ── Connection ──────────────────────────────────────────────────


class TestConnection:
    def test_connect_virtual(self, cnc):
        cnc.connect()
        assert cnc.ser is None  # virtual never opens a real port

    def test_close_virtual(self, cnc):
        cnc.connect()
        cnc.close()
        assert cnc.ser is None


# ── Bounds Checking ─────────────────────────────────────────────


class TestBounds:
    @pytest.mark.parametrize("x,y,z,expected", [
        (0, 0, 0, True),
        (270, 150, -35, True),
        (135, 75, -17.5, True),
        (-1, 0, 0, False),
        (0, 151, 0, False),
        (0, 0, 1, False),
        (271, 0, 0, False),
        (None, None, None, True),   # all None is within bounds
        (100, None, -10, True),     # partial None
    ])
    def test_coordinates_within_bounds(self, cnc, x, y, z, expected):
        assert cnc.coordinates_within_bounds(x, y, z) is expected


# ── G-code Generation ──────────────────────────────────────────


class TestGcodeGeneration:
    def test_basic_move(self, cnc):
        gcode = cnc.get_gcode_path_to_point(10, 20, -5, speed=2000, gtype="G1")
        assert "G1" in gcode
        assert "X10.000" in gcode
        assert "Y20.000" in gcode
        assert "Z-5.000" in gcode
        assert "F2000" in gcode

    def test_rapid_move(self, cnc):
        gcode = cnc.get_gcode_path_to_point(0, 0, 0, gtype="G0")
        assert gcode.startswith("G0")

    def test_partial_axes(self, cnc):
        gcode = cnc.get_gcode_path_to_point(x=50, y=None, z=None)
        assert "X50.000" in gcode
        assert "Y" not in gcode.replace("G1", "")  # only G1, no Y
        assert "Z" not in gcode


# ── Movement (virtual) ─────────────────────────────────────────


class TestMovement:
    def test_move_to_point(self, cnc):
        cnc.connect()
        result = cnc.move_to_point(10, 20, -5)
        assert result is not None
        assert cnc._virtual_pos["X"] == 10.0
        assert cnc._virtual_pos["Y"] == 20.0
        assert cnc._virtual_pos["Z"] == -5.0

    def test_move_to_point_out_of_bounds(self, cnc):
        cnc.connect()
        result = cnc.move_to_point(999, 0, 0)
        assert result is None

    def test_move_to_point_safe(self, cnc):
        cnc.connect()
        cnc.move_to_point_safe(50, 75, -10)
        assert cnc._virtual_pos["X"] == 50.0
        assert cnc._virtual_pos["Y"] == 75.0
        assert cnc._virtual_pos["Z"] == -10.0

    def test_move_to_point_safe_out_of_bounds(self, cnc):
        cnc.connect()
        cnc.move_to_point_safe(999, 0, 0)
        # should not move
        assert cnc._virtual_pos["X"] == 0.0

    def test_move_through_points(self, cnc):
        cnc.connect()
        points = [(10, 10, -5), (20, 20, -10)]
        cnc.move_through_points(points, speed=2000)
        assert cnc._virtual_pos["X"] == 20.0
        assert cnc._virtual_pos["Z"] == -10.0

    def test_move_through_points_skips_oob(self, cnc):
        cnc.connect()
        points = [(10, 10, -5), (999, 0, 0), (30, 30, -15)]
        cnc.move_through_points(points)
        # last valid point wins
        assert cnc._virtual_pos["X"] == 30.0


# ── Homing & Origin ────────────────────────────────────────────


class TestHomingOrigin:
    def test_home(self, cnc):
        cnc.connect()
        cnc.home()
        # after homing with default park=(0,0,0), virtual pos should be 0,0,0
        assert cnc._virtual_pos == {"X": 0.0, "Y": 0.0, "Z": 0.0}

    def test_origin(self, cnc):
        cnc.connect()
        cnc.move_to_point(50, 50, -10)
        cnc.origin()
        assert cnc._virtual_pos["X"] == 0.0
        assert cnc._virtual_pos["Y"] == 0.0
        assert cnc._virtual_pos["Z"] == 0.0


# ── Locations ───────────────────────────────────────────────────


class TestLocations:
    def test_get_location_position_index_0(self, cnc):
        x, y, z = cnc.get_location_position("vial_rack", 0)
        assert x == 100.0
        assert y == 80.0
        assert z == 0.0

    def test_get_location_position_index_1(self, cnc):
        # index 1: col=1, row=0 -> x_origin + 1*x_offset
        x, y, z = cnc.get_location_position("vial_rack", 1)
        assert x == pytest.approx(120.0)
        assert y == pytest.approx(80.0)

    def test_get_location_position_wraps_row(self, cnc):
        # index 2: col=0, row=1 -> y_origin + 1*y_offset
        x, y, z = cnc.get_location_position("vial_rack", 2)
        assert x == pytest.approx(100.0)
        assert y == pytest.approx(65.0)

    def test_move_to_location(self, cnc):
        cnc.connect()
        cnc.move_to_location("vial_rack", 0)
        assert cnc._virtual_pos["X"] == pytest.approx(100.0)
        assert cnc._virtual_pos["Y"] == pytest.approx(80.0)

    def test_unknown_location(self, cnc):
        with pytest.raises(KeyError, match="Unknown location"):
            cnc.get_location_position("nonexistent", 0)


# ── Spindle ─────────────────────────────────────────────────────


class TestSpindle:
    def test_spindle_on(self, cnc):
        cnc.connect()
        cnc.spindle_on(speed=5000)
        assert any("M3 S5000" in line for line in cnc._virtual_log)

    def test_spindle_on_default_speed(self, cnc):
        cnc.connect()
        cnc.spindle_on()
        assert any("M3 S1000" in line for line in cnc._virtual_log)

    def test_spindle_off(self, cnc):
        cnc.connect()
        cnc.spindle_on(speed=3000)
        cnc.spindle_off()
        assert any("M5" in line for line in cnc._virtual_log)

    def test_spindle_on_off_sequence(self, cnc):
        cnc.connect()
        cnc.spindle_on(speed=8000)
        cnc.spindle_off()
        log = cnc._virtual_log
        m3_idx = next(i for i, l in enumerate(log) if "M3" in l)
        m5_idx = next(i for i, l in enumerate(log) if "M5" in l)
        assert m3_idx < m5_idx


# ── send_lines / follow_gcode_path ─────────────────────────────


class TestGcodeDispatch:
    def test_send_lines_returns_oks(self, cnc):
        cnc.connect()
        replies = cnc.send_lines(["G0 X10", "G0 Y20"])
        assert all(r == "ok" for r in replies)

    def test_follow_gcode_path_empty(self, cnc):
        cnc.connect()
        result = cnc.follow_gcode_path("")
        assert result == []

    def test_follow_gcode_path_logs(self, cnc):
        cnc.connect()
        cnc.follow_gcode_path("G1 X5 Y5 F1000\nG1 Z-2 F500\n")
        assert len(cnc._virtual_log) >= 2

    def test_set_safe_modes(self, cnc):
        cnc.connect()
        cnc.set_safe_modes()
        log_text = " ".join(cnc._virtual_log)
        for code in ("G21", "G90", "G94", "G54"):
            assert code in log_text
