"""Tests for systemd service installation."""

import builtins
import subprocess
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from lnxlink import config_setup
from lnxlink.consts import SERVICEHEADLESS, SERVICEUSER


def test_privileged_service_write_passes_exact_text_to_sudo_tee(tmp_path):
    """The privileged fallback must not serialize the bytes representation."""
    service_path = tmp_path / "lnxlink.service"
    calls = []

    def deny_service_write(path, *args, **kwargs):
        if Path(path) == service_path:
            raise PermissionError
        return builtins.open(path, *args, encoding="utf-8", **kwargs)

    def record_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(config_setup, "_get_service_user", return_value=0)
        )
        stack.enter_context(
            patch.object(config_setup, "_query_true_false", return_value=False)
        )
        stack.enter_context(
            patch.object(
                config_setup,
                "_get_service_vars",
                return_value=("sudo", "", SERVICEHEADLESS, str(tmp_path)),
            )
        )
        stack.enter_context(
            patch.object(config_setup.shutil, "which", return_value="/usr/bin/lnxlink")
        )
        stack.enter_context(
            patch.object(
                config_setup, "open", side_effect=deny_service_write, create=True
            )
        )
        stack.enter_context(
            patch.object(config_setup.subprocess, "run", side_effect=record_run)
        )
        config_setup.setup_systemd("/tmp/lnxlink.yaml")

    tee_command, tee_kwargs = calls[0]
    expected = SERVICEHEADLESS.format(exec_cmd="/usr/bin/lnxlink -c /tmp/lnxlink.yaml")
    assert tee_command == ["sudo", "tee", str(service_path)]
    assert tee_kwargs["input"] == expected
    assert tee_kwargs["text"] is True
    assert tee_kwargs["check"] is True
    assert tee_kwargs["stdout"] is subprocess.DEVNULL
    assert not expected.startswith("b'")
    assert all(call_kwargs["check"] is True for _, call_kwargs in calls)


def test_user_service_still_writes_directly(tmp_path):
    """A writable user service must not go through sudo or tee."""
    calls = []

    def record_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(config_setup, "_get_service_user", return_value=0)
        )
        stack.enter_context(
            patch.object(config_setup, "_query_true_false", return_value=True)
        )
        stack.enter_context(
            patch.object(
                config_setup,
                "_get_service_vars",
                return_value=("", "--user", SERVICEUSER, str(tmp_path)),
            )
        )
        stack.enter_context(
            patch.object(config_setup.shutil, "which", return_value="/usr/bin/lnxlink")
        )
        stack.enter_context(
            patch.object(config_setup.subprocess, "run", side_effect=record_run)
        )
        config_setup.setup_systemd("/tmp/lnxlink.yaml")

    expected = SERVICEUSER.format(exec_cmd="/usr/bin/lnxlink -c /tmp/lnxlink.yaml")
    assert (tmp_path / "lnxlink.service").read_text(encoding="UTF-8") == expected
    assert all("tee" not in command for command, _ in calls)
    assert calls[-2][0] == ["systemctl", "--user", "daemon-reload"]
    assert calls[-1][0] == ["systemctl", "--user", "enable", "lnxlink.service"]
