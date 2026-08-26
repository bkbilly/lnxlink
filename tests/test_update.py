"""Tests for LNXlink self-update command status."""
# pylint: disable=missing-function-docstring,protected-access

from unittest.mock import patch

import pytest

from lnxlink.modules import update


class DummyLnxlink:
    """Minimal LNXlink interface used by the update module."""

    def __init__(self, method="pipx"):
        self.version = "2026.8.0"
        self.install_method = method
        self.path = "/tmp/lnxlink-source"
        self.restart_calls = 0
        self.published = []

    def restart_script(self):
        self.restart_calls += 1

    def run_module(self, name, method):
        self.published.append((name, method))


@pytest.mark.parametrize("method", ["pipx", "uv", "flatpak", "pip", "system"])
@pytest.mark.parametrize("returncode, expected", [(0, True), (42, False)])
def test_update_methods_return_command_status(method, returncode, expected):
    """Single-command update methods must return their command status."""
    lnxlink = DummyLnxlink(method)
    addon = update.Addon(lnxlink)

    with patch.object(update, "syscommand", return_value=("", "", returncode)):
        assert addon._run_update() is expected


@pytest.mark.parametrize("helper", ["yay", "paru"])
@pytest.mark.parametrize("returncode, expected", [(0, True), (42, False)])
def test_aur_update_returns_package_manager_status(helper, returncode, expected):
    """AUR helper discovery success must not hide package-manager failure."""

    def command_result(command, **kwargs):
        if command == f"which {helper}":
            return f"/usr/bin/{helper}", "", 0
        if command.startswith(("yay ", "paru ")):
            return "", "", returncode
        return "", "", 1

    addon = update.Addon(DummyLnxlink("aur"))
    with patch.object(update, "syscommand", side_effect=command_result):
        assert addon._run_update() is expected


@pytest.mark.parametrize("method", ["pip_edit", "uv_edit"])
def test_editable_update_stops_after_failed_git_pull(method):
    """A failed source update must not reinstall and restart the old checkout."""
    commands = []

    def fail_pull(command, **kwargs):
        commands.append(command)
        return "", "", 1

    addon = update.Addon(DummyLnxlink(method))
    with patch.object(update, "syscommand", side_effect=fail_pull):
        assert addon._run_update() is False

    assert len(commands) == 1
    assert commands[0].startswith("git ")


@pytest.mark.parametrize("install_returncode, expected", [(0, True), (1, False)])
def test_editable_update_returns_reinstall_status(install_returncode, expected):
    """A successful pull is not enough when the reinstall fails."""
    returncodes = iter([0, install_returncode])

    def command_result(command, **kwargs):
        return "", "", next(returncodes)

    addon = update.Addon(DummyLnxlink("pip_edit"))
    with patch.object(update, "syscommand", side_effect=command_result):
        assert addon._run_update() is expected


@pytest.mark.parametrize("succeeded, restart_calls", [(False, 0), (True, 1)])
def test_restart_only_runs_after_successful_update(succeeded, restart_calls):
    """The control path must not restart after a failed update."""
    lnxlink = DummyLnxlink()
    addon = update.Addon(lnxlink)

    with patch.object(addon, "_run_update", return_value=succeeded):
        addon.start_control([], "install")

    assert lnxlink.restart_calls == restart_calls
    assert addon.message["in_progress"] is False
