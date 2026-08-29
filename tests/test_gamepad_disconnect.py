"""Regression tests for gamepad activity on disconnect."""
# pylint: disable=missing-class-docstring,missing-function-docstring

import errno
import struct
from unittest.mock import Mock, patch

from lnxlink.modules.gamepad import Addon


class DisconnectingInput:
    """Return one input event, then emulate a disconnected evdev device."""

    def __init__(self):
        self.reads = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _size):
        self.reads += 1
        if self.reads == 1:
            return struct.pack("llHHI", 0, 0, 1, 1, 1)
        raise OSError(errno.ENODEV, "No such device")


class SingleEventInput:
    def __init__(self):
        self.reads = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _size):
        self.reads += 1
        if self.reads == 1:
            return struct.pack("llHHI", 0, 0, 1, 1, 1)
        return b""


def test_disconnect_clears_recent_activity():
    gamepad = Addon(None)
    watcher_token = object()
    gamepad.watcher_tokens["event4"] = watcher_token

    with patch("builtins.open", return_value=DisconnectingInput()):
        gamepad.watch_input("event4", watcher_token)

    assert not gamepad.last_used
    with patch.object(gamepad, "watch_gamepads"):
        assert gamepad.get_info() is False


def test_removed_gamepad_does_not_clear_other_activity():
    gamepad = Addon(None)
    gamepad.gamepads = ["event4", "event5"]
    gamepad.running_threads = {
        "event4": Mock(is_alive=lambda: True),
        "event5": Mock(is_alive=lambda: True),
    }
    gamepad.last_used = {"event4": 100, "event5": 200}

    with patch(
        "lnxlink.modules.gamepad.syscommand",
        return_value=("H: Handlers=event5 js1", "", 0),
    ):
        gamepad.watch_gamepads()

    assert gamepad.last_used == {"event5": 200}
    with patch.object(gamepad, "watch_gamepads"):
        with patch("lnxlink.modules.gamepad.time.time", return_value=210):
            assert gamepad.get_info() is True


def test_old_watcher_does_not_clear_replacement_activity():
    gamepad = Addon(None)
    old_token = object()
    replacement_token = object()
    gamepad.watcher_tokens["event4"] = replacement_token
    gamepad.last_used["event4"] = 200

    with patch("builtins.open", return_value=SingleEventInput()):
        with patch("lnxlink.modules.gamepad.time.time", return_value=500):
            gamepad.watch_input("event4", old_token)

    assert gamepad.watcher_tokens["event4"] is replacement_token
    assert gamepad.last_used == {"event4": 200}
