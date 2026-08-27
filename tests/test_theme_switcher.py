"""Tests for the Theme Switcher module."""
# pylint: disable=missing-class-docstring,missing-function-docstring

from unittest.mock import MagicMock, patch

from lnxlink.modules import theme_switcher


class FakeLnxlink:
    def __init__(self, settings=None):
        self.config = {"settings": {"theme_switcher": settings or {}}}
        self.run_module_calls = []

    def add_settings(self, name, default):
        pass

    def run_module(self, topic, data, force_update=False):
        self.run_module_calls.append((topic, data, force_update))


def test_theme_switcher_exposed_controls():
    lnxlink = FakeLnxlink()
    addon = theme_switcher.Addon(lnxlink)
    controls = addon.exposed_controls()
    assert "Theme" in controls
    assert controls["Theme"]["type"] == "switch"


def test_theme_switcher_get_info_gnome_dark():
    lnxlink = FakeLnxlink()
    addon = theme_switcher.Addon(lnxlink)

    with patch("lnxlink.modules.theme_switcher.which", return_value="/usr/bin/gsettings"), \
         patch("lnxlink.modules.theme_switcher.syscommand", return_value=("'prefer-dark'", "", 0)):
        info = addon.get_info()
        assert info["status"] == "ON"
        assert info["attributes"]["is_dark"] is True
        assert info["attributes"]["source"] == "gnome_gsettings"


def test_theme_switcher_get_info_kde_light():
    lnxlink = FakeLnxlink()
    addon = theme_switcher.Addon(lnxlink)

    def fake_which(cmd):
        return "/usr/bin/kreadconfig6" if cmd == "kreadconfig6" else None

    with patch("lnxlink.modules.theme_switcher.which", side_effect=fake_which), \
         patch("lnxlink.modules.theme_switcher.syscommand", return_value=("BreezeLight", "", 0)):
        info = addon.get_info()
        assert info["status"] == "OFF"
        assert info["attributes"]["is_dark"] is False
        assert info["attributes"]["source"] == "kde_config"


def test_theme_switcher_start_control_dark():
    lnxlink = FakeLnxlink()
    addon = theme_switcher.Addon(lnxlink)

    with patch("lnxlink.modules.theme_switcher.which", return_value="/usr/bin/gsettings"), \
         patch("lnxlink.modules.theme_switcher.syscommand", return_value=("", "", 0)) as mock_cmd:
        addon.start_control(["theme"], "ON")
        assert mock_cmd.called
        assert len(lnxlink.run_module_calls) == 1
