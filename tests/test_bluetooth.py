"""Tests for the Bluetooth module."""
# pylint: disable=missing-class-docstring,missing-function-docstring

from unittest.mock import MagicMock, patch

from lnxlink.modules import bluetooth


class FakeLnxlink:
    def __init__(self):
        self.config = {"settings": {}}


def test_device_icon_mapping():
    assert bluetooth.Addon._device_icon("audio-headset") == "mdi:headphones"
    assert bluetooth.Addon._device_icon("input-gaming") == "mdi:gamepad-variant"
    assert bluetooth.Addon._device_icon("input-mouse") == "mdi:mouse"
    assert bluetooth.Addon._device_icon("input-keyboard") == "mdi:keyboard"
    assert bluetooth.Addon._device_icon("phone") == "mdi:cellphone"
    assert bluetooth.Addon._device_icon(None) == "mdi:bluetooth"


def test_bluetooth_exposed_controls():
    fake_conn = MagicMock()
    with patch("lnxlink.modules.bluetooth.open_dbus_connection", return_value=fake_conn), \
         patch.object(bluetooth.Addon, "_get_adapter_path", return_value="/org/bluez/hci0"), \
         patch.object(bluetooth.Addon, "_get_bluetoothdata", return_value={
             "power": "ON",
             "devices": {
                 "AA:BB:CC:DD:EE:FF": {
                     "name": "Sony WH-1000XM4",
                     "power": "ON",
                     "batteries": {},
                     "attributes": {
                         "mac": "AA:BB:CC:DD:EE:FF",
                         "battery": "90",
                         "rssi": -65,
                         "paired": True,
                         "trusted": True,
                         "blocked": False,
                         "icon": "audio-headset",
                     },
                 }
             },
         }):
        lnxlink = FakeLnxlink()
        addon = bluetooth.Addon(lnxlink)
        controls = addon.exposed_controls()

        assert "Bluetooth Power" in controls
        assert "Bluetooth Device Sony WH-1000XM4 AABBCCDDEEFF" in controls
        device_switch = controls["Bluetooth Device Sony WH-1000XM4 AABBCCDDEEFF"]
        assert device_switch["type"] == "switch"
        assert device_switch["icon"] == "mdi:headphones"
        assert "Bluetooth Device Sony WH-1000XM4 AABBCCDDEEFF Battery" in controls
