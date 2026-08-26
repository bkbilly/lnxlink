"""Tests for subprocess argument boundaries."""
# pylint: disable=missing-class-docstring,missing-function-docstring

import importlib.metadata

from lnxlink.modules import media, xdg_open
from lnxlink.modules.scripts import helpers


class _DummyCompletedProcess:
    def __init__(self, stdout=b"", stderr=b"", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_syscommand_list_keeps_arguments_separate(monkeypatch):
    calls = []

    def fake_run(command, shell, check, capture_output, timeout):
        calls.append(
            {
                "command": command,
                "shell": shell,
                "check": check,
                "capture_output": capture_output,
                "timeout": timeout,
            }
        )
        return _DummyCompletedProcess(stdout=b"ok\n")

    monkeypatch.setattr(helpers.subprocess, "run", fake_run)

    stdout, stderr, returncode = helpers.syscommand(["printf", "%s", "a b"])

    assert stdout == "ok"
    assert stderr == ""
    assert returncode == 0
    assert calls == [
        {
            "command": ["printf", "%s", "a b"],
            "shell": False,
            "check": False,
            "capture_output": True,
            "timeout": 3,
        }
    ]


def test_syscommand_string_keeps_shell_mode(monkeypatch):
    calls = []

    def fake_run(command, shell, check, capture_output, timeout):
        calls.append(
            {
                "command": command,
                "shell": shell,
                "check": check,
                "capture_output": capture_output,
                "timeout": timeout,
            }
        )
        return _DummyCompletedProcess(stdout=b"ok\n")

    monkeypatch.setattr(helpers.subprocess, "run", fake_run)

    stdout, stderr, returncode = helpers.syscommand("printf ok")

    assert stdout == "ok"
    assert stderr == ""
    assert returncode == 0
    assert calls == [
        {
            "command": "printf ok",
            "shell": True,
            "check": False,
            "capture_output": True,
            "timeout": 3,
        }
    ]


def test_import_install_package_uses_unquoted_install_spec(monkeypatch):
    calls = []

    def fake_version(name):
        if name == "demo":
            return "1.0.0"
        raise importlib.metadata.PackageNotFoundError

    def fake_syscommand(command, ignore_errors=False, timeout=3, background=False):
        calls.append(
            {
                "command": command,
                "ignore_errors": ignore_errors,
                "timeout": timeout,
                "background": background,
            }
        )
        return "", "", 0

    monkeypatch.setattr(helpers.importlib.metadata, "version", fake_version)
    monkeypatch.setattr(helpers, "find_uv_bin", lambda: "/usr/bin/uv")
    monkeypatch.setattr(helpers, "syscommand", fake_syscommand)

    module = helpers.import_install_package("demo", ">=2.0.0", "sys")

    assert module.__name__ == "sys"
    assert calls[0]["command"] == [
        "/usr/bin/uv",
        "pip",
        "install",
        "--python",
        helpers.sys.executable,
        "--break-system-packages",
        "-U",
        "--quiet",
        "demo>=2.0.0",
    ]


def test_xdg_open_uses_one_argv_per_path(monkeypatch):
    calls = []

    def fake_syscommand(command, background=False):
        calls.append((command, background))
        return "", "", 0

    monkeypatch.setattr(xdg_open, "syscommand", fake_syscommand)

    addon = object.__new__(xdg_open.Addon)
    addon.start_control(("xdg_open", "x"), "/tmp/My File.txt")

    assert calls == [(["xdg-open", "/tmp/My File.txt"], True)]


def test_media_playback_keeps_url_intact(monkeypatch):
    calls = []

    class DummyProcess:
        def wait(self):
            calls.append("wait")

    def fake_popen(command, shell, stdout, stderr):
        calls.append(
            {
                "command": command,
                "shell": shell,
                "stdout": stdout,
                "stderr": stderr,
            }
        )
        return DummyProcess()

    monkeypatch.setattr(media.subprocess, "Popen", fake_popen)

    addon = object.__new__(media.Addon)
    addon.process = None
    addon.run_playmedia_thread(
        "ffplay",
        {
            "opt_static": "",
            "opt_foreground": "-autoexit",
            "opt_background": "-nodisp -autoexit",
        },
        "/tmp/My File.mp3",
        "audio",
    )

    assert calls[0] == {
        "command": ["ffplay", "-nodisp", "-autoexit", "/tmp/My File.mp3"],
        "shell": False,
        "stdout": media.subprocess.DEVNULL,
        "stderr": media.subprocess.STDOUT,
    }
