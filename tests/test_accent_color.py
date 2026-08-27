"""Tests for the Accent Color module."""
# pylint: disable=missing-class-docstring,missing-function-docstring

from unittest.mock import patch

from lnxlink.modules import accent_color


class FakeLnxlink:
    def __init__(self, settings=None):
        self.config = {"settings": {"accent_color": settings or {}}}

    def add_settings(self, name, default):
        pass


def test_accent_color_exposed_controls():
    lnxlink = FakeLnxlink()
    addon = accent_color.Addon(lnxlink)
    controls = addon.exposed_controls()
    assert "Accent Color" in controls
    assert controls["Accent Color"]["type"] == "sensor"


def test_accent_color_kde_kreadconfig():
    lnxlink = FakeLnxlink()
    addon = accent_color.Addon(lnxlink)

    with patch("os.path.exists", return_value=True), \
         patch("lnxlink.modules.accent_color.which", return_value="/usr/bin/kreadconfig6"), \
         patch("lnxlink.modules.accent_color.syscommand", return_value=("82, 160, 80", "", 0)), \
         patch("configparser.ConfigParser.read", side_effect=Exception("skip direct parse")):
        info = addon.get_info()
        assert info["hex"] == "#52a050"
        assert info["attributes"]["rgb"] == [82, 160, 80]
        assert info["attributes"]["r"] == 82
        assert info["attributes"]["g"] == 160
        assert info["attributes"]["b"] == 80


def test_accent_color_gnome():
    lnxlink = FakeLnxlink()
    addon = accent_color.Addon(lnxlink)

    with patch("os.path.exists", return_value=False), \
         patch("lnxlink.modules.accent_color.which", return_value="/usr/bin/gsettings"), \
         patch("lnxlink.modules.accent_color.syscommand", return_value=("'blue'", "", 0)):
        info = addon.get_info()
        assert info["hex"] == "#3584e4"
        assert info["attributes"]["rgb"] == [53, 132, 228]
        assert info["attributes"]["backend"] == "gnome"


def test_parse_color_string_hex():
    assert accent_color.Addon._parse_color_string("#3daee9") == (61, 174, 233)
    assert accent_color.Addon._parse_color_string("#fff") == (255, 255, 255)
    assert accent_color.Addon._parse_color_string("82,160,80") == (82, 160, 80)
