"""Tests for the Custom Sensors module."""
# pylint: disable=missing-class-docstring,missing-function-docstring

from unittest.mock import MagicMock, patch

from lnxlink.modules import custom_sensors


class FakeLnxlink:
    def __init__(self, settings=None):
        self.config = {"settings": {"custom_sensors": settings or {}}}
        self.run_module_calls = []

    def add_settings(self, name, default):
        pass

    def run_module(self, topic, data, force_update=False):
        self.run_module_calls.append((topic, data, force_update))


def test_custom_sensors_exposed_controls_dict():
    settings = {
        "gpu_power": {
            "name": "GPU Power Draw",
            "command": "echo 45.2",
            "device_class": "power",
            "state_class": "measurement",
            "unit": "W",
            "icon": "mdi:flash",
            "interval": 5,
        }
    }
    lnxlink = FakeLnxlink(settings)
    addon = custom_sensors.Addon(lnxlink)
    controls = addon.exposed_controls()
    assert "GPU Power Draw" in controls
    assert controls["GPU Power Draw"]["type"] == "sensor"
    assert controls["GPU Power Draw"]["unit"] == "W"
    assert controls["GPU Power Draw"]["device_class"] == "power"
    assert controls["GPU Power Draw"]["subtopic"] is True


def test_custom_sensors_get_info_runs_command():
    settings = {
        "gpu_power": {
            "name": "GPU Power Draw",
            "command": "echo 45.2",
            "interval": 1,
        }
    }
    lnxlink = FakeLnxlink(settings)
    addon = custom_sensors.Addon(lnxlink)
    addon.exposed_controls()

    with patch("lnxlink.modules.custom_sensors.syscommand", return_value=("45.2", "", 0)):
        addon.get_info(force_update=True)
        assert len(lnxlink.run_module_calls) == 1
        topic, data, _ = lnxlink.run_module_calls[0]
        assert topic == "Custom Sensors/gpu_power"
        assert data["value"] == "45.2"


def test_custom_sensors_json_output():
    settings = {
        "smart_data": {
            "name": "Smart Info",
            "command": "echo '{\"value\": 100, \"health\": \"good\"}'",
            "interval": 1,
        }
    }
    lnxlink = FakeLnxlink(settings)
    addon = custom_sensors.Addon(lnxlink)
    addon.exposed_controls()

    with patch(
        "lnxlink.modules.custom_sensors.syscommand",
        return_value=('{"value": 100, "health": "good"}', "", 0),
    ):
        addon.get_info(force_update=True)
        assert len(lnxlink.run_module_calls) == 1
        _, data, _ = lnxlink.run_module_calls[0]
        assert data["value"] == 100
        assert data["health"] == "good"
