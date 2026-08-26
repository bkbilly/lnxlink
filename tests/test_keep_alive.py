"""Tests for Keep Alive state detection."""
# pylint: disable=missing-function-docstring

from unittest.mock import patch

from lnxlink.modules import keep_alive


def xset_only(command_output):
    """Patch Keep Alive to use a deterministic X11-only fixture."""
    return (
        patch.object(
            keep_alive,
            "which",
            side_effect=lambda command: "/usr/bin/xset" if command == "xset" else None,
        ),
        patch.object(keep_alive, "get_display_variable", return_value=":0"),
        patch.object(keep_alive, "syscommand", return_value=(command_output, "", 0)),
    )


def test_x11_keep_alive_is_on_when_dpms_is_disabled():
    addon = keep_alive.Addon.__new__(keep_alive.Addon)
    output = "Standby: 0    Suspend: 0    Off: 0\nDPMS is Disabled"
    which_patch, display_patch, command_patch = xset_only(output)

    with which_patch, display_patch, command_patch:
        assert addon.get_info() is True


def test_x11_keep_alive_is_off_when_dpms_is_enabled():
    addon = keep_alive.Addon.__new__(keep_alive.Addon)
    output = "Standby: 600    Suspend: 600    Off: 600\nDPMS is Enabled"
    which_patch, display_patch, command_patch = xset_only(output)

    with which_patch, display_patch, command_patch:
        assert addon.get_info() is False


def test_x11_without_dpms_is_ignored():
    addon = keep_alive.Addon.__new__(keep_alive.Addon)
    output = "Server does not have the DPMS Extension"
    which_patch, display_patch, command_patch = xset_only(output)

    with which_patch, display_patch, command_patch:
        assert addon.get_info() is False


def test_x11_without_dpms_does_not_override_gnome():
    addon = keep_alive.Addon.__new__(keep_alive.Addon)
    outputs = {
        "gsettings get org.gnome.desktop.session idle-delay": ("uint32 0", "", 0),
        (
            "gsettings get org.gnome.settings-daemon.plugins.power "
            "sleep-inactive-ac-type"
        ): ("'nothing'", "", 0),
        "xset -display :0 q": ("Server does not have the DPMS Extension", "", 0),
    }

    with patch.object(keep_alive, "which", return_value="/usr/bin/tool"), patch.object(
        keep_alive, "get_display_variable", return_value=":0"
    ), patch.object(
        keep_alive,
        "syscommand",
        side_effect=lambda command, **kwargs: outputs[command],
    ):
        assert addon.get_info() is True


def test_all_available_sleep_mechanisms_must_be_disabled():
    addon = keep_alive.Addon.__new__(keep_alive.Addon)
    outputs = {
        "gsettings get org.gnome.desktop.session idle-delay": ("uint32 0", "", 0),
        (
            "gsettings get org.gnome.settings-daemon.plugins.power "
            "sleep-inactive-ac-type"
        ): ("'nothing'", "", 0),
        "xset -display :0 q": ("DPMS is Enabled", "", 0),
    }

    with patch.object(keep_alive, "which", return_value="/usr/bin/tool"), patch.object(
        keep_alive, "get_display_variable", return_value=":0"
    ), patch.object(
        keep_alive,
        "syscommand",
        side_effect=lambda command, **kwargs: outputs[command],
    ):
        assert addon.get_info() is False


def test_enabled_gnome_idle_is_not_masked_by_disabled_dpms():
    addon = keep_alive.Addon.__new__(keep_alive.Addon)
    outputs = {
        "gsettings get org.gnome.desktop.session idle-delay": ("uint32 600", "", 0),
        (
            "gsettings get org.gnome.settings-daemon.plugins.power "
            "sleep-inactive-ac-type"
        ): ("'nothing'", "", 0),
        "xset -display :0 q": ("DPMS is Disabled", "", 0),
    }

    with patch.object(keep_alive, "which", return_value="/usr/bin/tool"), patch.object(
        keep_alive, "get_display_variable", return_value=":0"
    ), patch.object(
        keep_alive,
        "syscommand",
        side_effect=lambda command, **kwargs: outputs[command],
    ):
        assert addon.get_info() is False
