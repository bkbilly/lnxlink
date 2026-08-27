"""Tests for the Wallpaper Switcher module."""
# pylint: disable=missing-class-docstring,missing-function-docstring

from unittest.mock import MagicMock, patch

from lnxlink.modules import wallpaper_switcher


class FakeLnxlink:
    def __init__(self, settings=None):
        self.config = {"settings": {"wallpaper_switcher": settings or {}}}

    def add_settings(self, name, default):
        pass

    def setup_discovery(self, filter_name=None):
        pass


def test_wallpaper_switcher_exposed_controls_no_options():
    lnxlink = FakeLnxlink()
    addon = wallpaper_switcher.Addon(lnxlink)
    controls = addon.exposed_controls()
    assert "Wallpaper Path" in controls
    assert controls["Wallpaper Path"]["type"] == "text"


def test_wallpaper_switcher_exposed_controls_with_options():
    lnxlink = FakeLnxlink({"options": ["/tmp/wall1.jpg", "/tmp/wall2.png"]})
    addon = wallpaper_switcher.Addon(lnxlink)
    controls = addon.exposed_controls()
    assert "Wallpaper Path" in controls
    assert "Wallpaper Select" in controls
    assert controls["Wallpaper Select"]["type"] == "select"
    assert "wall1.jpg" in controls["Wallpaper Select"]["options"]


def test_wallpaper_switcher_set_wallpaper_gnome():
    lnxlink = FakeLnxlink({"options": ["/tmp/wall1.jpg"]})
    addon = wallpaper_switcher.Addon(lnxlink)
    addon.backend = "gnome"

    with patch("os.path.exists", return_value=True), \
         patch("lnxlink.modules.wallpaper_switcher.which", return_value="/usr/bin/gsettings"), \
         patch("lnxlink.modules.wallpaper_switcher.syscommand", return_value=("", "", 0)) as mock_cmd:
        addon.start_control(["wallpaper_switcher", "wallpaper_select"], "wall1.jpg")
        assert mock_cmd.called
