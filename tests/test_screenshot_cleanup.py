"""Tests for screenshot process cleanup."""
# pylint: disable=missing-function-docstring

from lnxlink.modules import screenshot


class _DummyProcess:
    def __init__(self, pid):
        self.pid = pid
        self.killed = False

    def kill(self):
        self.killed = True


def test_release_without_process_does_not_signal(monkeypatch):
    killpg_calls = []
    run_calls = []

    def fail_getpgid(pid):
        raise AssertionError(f"unexpected getpgid call for pid {pid}")

    def fake_killpg(*args):
        killpg_calls.append(args)

    def fake_run(*args, **kwargs):
        run_calls.append((args, kwargs))

    monkeypatch.setattr(screenshot.os, "getpgid", fail_getpgid)
    monkeypatch.setattr(screenshot.os, "killpg", fake_killpg)
    monkeypatch.setattr(screenshot.subprocess, "run", fake_run)

    capture = object.__new__(screenshot.FastVideoCapture)
    capture.cap = None
    capture.process = None
    capture.running = True
    capture.thread = None

    capture.release()

    assert not killpg_calls
    assert not run_calls


def test_cleanup_reaps_only_owned_process_group(monkeypatch):
    killpg_calls = []
    proc = _DummyProcess(pid=321)

    monkeypatch.setattr(
        screenshot.os,
        "killpg",
        lambda pgid, sig: killpg_calls.append((pgid, sig)),
    )

    capture = object.__new__(screenshot.FastVideoCapture)
    capture.cap = None
    capture.process = proc
    capture.running = True
    capture.thread = None

    capture.cleanup()

    assert killpg_calls == [(321, 9)]
    assert proc.killed is False


def test_cleanup_uses_saved_group_after_launcher_exits(monkeypatch):
    killpg_calls = []
    proc = _DummyProcess(pid=321)

    monkeypatch.setattr(
        screenshot.os,
        "getpgid",
        lambda _pid: (_ for _ in ()).throw(ProcessLookupError()),
    )
    monkeypatch.setattr(
        screenshot.os,
        "killpg",
        lambda pgid, sig: killpg_calls.append((pgid, sig)),
    )

    capture = object.__new__(screenshot.FastVideoCapture)
    capture.cap = None
    capture.process = proc

    capture.cleanup()

    assert killpg_calls == [(321, 9)]
    assert proc.killed is False
