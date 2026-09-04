"""Tests for monitor identification in the brightness helper."""
# pylint: disable=missing-class-docstring,missing-function-docstring

import struct
from unittest.mock import mock_open, patch

from lnxlink.modules.scripts.monitor_brightness import (
    DDCIPMonitor,
    MonitorBrightness,
    SysfsMonitor,
)

EDID_HEADER = bytes.fromhex("00 FF FF FF FF FF FF 00")


def test_unique_name_uses_edid_serial():
    monitor = DDCIPMonitor("/dev/i2c-14", "AOC", "U34V5C", "1QDQ6HA000243")
    assert monitor.unique_name == "AOC U34V5C 1QDQ6HA000243"


def test_unique_name_survives_bus_renumbering():
    # The kernel assigns the i2c bus number at boot, and it can change.
    # That drifts the entity_id in Home Assistant and silently breaks automations.
    before = DDCIPMonitor("/dev/i2c-14", "AOC", "U34V5C", "1QDQ6HA000243")
    after = DDCIPMonitor("/dev/i2c-4", "AOC", "U34V5C", "1QDQ6HA000243")
    assert before.unique_name == after.unique_name


def test_unique_name_falls_back_to_bus_when_serial_missing():
    for serial in (None, "", "Unknown"):
        monitor = DDCIPMonitor("/dev/i2c-4", "GSM", "LG HDR WFHD", serial)
        assert monitor.unique_name == "GSM LG HDR WFHD i2c-4"


def test_sysfs_monitor_keeps_its_path_identifier():
    with patch.object(SysfsMonitor, "_read_value", return_value=255):
        monitor = SysfsMonitor("/sys/class/backlight/intel_backlight")
        assert monitor.unique_name == "Internal intel_backlight intel_backlight"


def test_list_displays_passes_serial_to_the_monitor():
    edid = EDID_HEADER + bytes(248)
    with patch(
        "lnxlink.modules.scripts.monitor_brightness.glob.glob",
        side_effect=lambda pattern: ["/dev/i2c-14"] if "i2c" in pattern else [],
    ), patch("builtins.open", mock_open(read_data=edid)), patch(
        "lnxlink.modules.scripts.monitor_brightness.fcntl.ioctl"
    ), patch.object(
        DDCIPMonitor, "parse_edid", return_value=("AOC", "U34V5C", "1QDQ6HA000243")
    ):
        monitors, _ = MonitorBrightness.list_displays()

    assert [m.unique_name for m in monitors] == ["AOC U34V5C 1QDQ6HA000243"]


def _edid(manufacturer="GSM", name="LG HDR WFHD", ascii_serial=None, binary_serial=0):
    """Builds a minimal but structurally valid EDID block for tests."""
    packed = 0
    for char in manufacturer:
        packed = (packed << 5) | (ord(char) - 64)
    block = bytearray(128)
    block[0:8] = EDID_HEADER
    block[8:10] = struct.pack(">H", packed)
    block[10:12] = struct.pack("<H", 1234)
    block[12:16] = struct.pack("<I", binary_serial)
    block[16], block[17] = 5, 30

    def descriptor(tag, text):
        body = text.encode("ascii")[:13]
        return bytes([0, 0, 0, tag, 0]) + body + b"\x0a" + b" " * (12 - len(body))

    block[54:72] = descriptor(0xFC, name)
    if ascii_serial is not None:
        block[72:90] = descriptor(0xFF, ascii_serial)
    return bytes(block)


def test_parse_edid_prefers_the_ascii_serial_descriptor():
    data = _edid(ascii_serial="1QDQ6HA000243", binary_serial=243)
    assert DDCIPMonitor.parse_edid(data)[2] == "1QDQ6HA000243"


def test_parse_edid_falls_back_to_the_binary_serial():
    # The LG panel on media-mllse-g3 ships no 0xFF descriptor but does carry
    # a serial in EDID bytes 12-15, which is what keeps its entity_id stable.
    data = _edid(ascii_serial=None, binary_serial=508025)
    assert DDCIPMonitor.parse_edid(data)[2] == "508025"


def test_parse_edid_reports_unknown_without_any_serial():
    data = _edid(ascii_serial=None, binary_serial=0)
    assert DDCIPMonitor.parse_edid(data)[2] == "Unknown"


def test_monitor_without_ascii_serial_still_gets_a_stable_name():
    manufacturer, name, serial = DDCIPMonitor.parse_edid(
        _edid(ascii_serial=None, binary_serial=508025)
    )
    on_bus_5 = DDCIPMonitor("/dev/i2c-5", manufacturer, name, serial)
    on_bus_4 = DDCIPMonitor("/dev/i2c-4", manufacturer, name, serial)
    assert on_bus_5.unique_name == "GSM LG HDR WFHD 508025"
    assert on_bus_5.unique_name == on_bus_4.unique_name
