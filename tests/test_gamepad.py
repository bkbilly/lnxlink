"""Tests for gamepad watcher lifecycle."""
# pylint: disable=missing-function-docstring

from unittest.mock import patch

from lnxlink.modules import gamepad


class FakeThread:
    """Record watcher creation without opening input devices."""

    instances = []

    def __init__(self, target, args, daemon):
        self.target = target
        self.args = args
        self.daemon = daemon
        self.alive = False
        self.instances.append(self)

    def start(self):
        self.alive = True

    def is_alive(self):
        return self.alive


def test_adding_gamepad_retains_existing_watcher():
    addon = gamepad.Addon(None)
    outputs = iter(
        [
            ("H: Handlers=event1 js0", "", 0),
            ("H: Handlers=event1 js0\nH: Handlers=event2 js1", "", 0),
        ]
    )

    FakeThread.instances = []
    with patch.object(gamepad, "Thread", FakeThread), patch.object(
        gamepad, "syscommand", side_effect=lambda *args, **kwargs: next(outputs)
    ):
        addon.watch_gamepads()
        event1_watcher = addon.running_threads["event1"]
        addon.watch_gamepads()

    assert addon.running_threads["event1"] is event1_watcher
    assert set(addon.running_threads) == {"event1", "event2"}
    assert [thread.args for thread in FakeThread.instances] == [
        ("event1",),
        ("event2",),
    ]


def test_unchanged_topology_starts_no_watcher():
    addon = gamepad.Addon(None)
    outputs = iter(
        [
            ("H: Handlers=event1 js0", "", 0),
            ("H: Handlers=event1 js0", "", 0),
        ]
    )

    FakeThread.instances = []
    with patch.object(gamepad, "Thread", FakeThread), patch.object(
        gamepad, "syscommand", side_effect=lambda *args, **kwargs: next(outputs)
    ):
        addon.watch_gamepads()
        addon.watch_gamepads()

    assert len(FakeThread.instances) == 1


def test_removing_gamepad_does_not_wait_for_reader():
    addon = gamepad.Addon(None)
    outputs = iter(
        [
            ("H: Handlers=event1 js0\nH: Handlers=event2 js1", "", 0),
            ("H: Handlers=event2 js1", "", 0),
        ]
    )

    FakeThread.instances = []
    with patch.object(gamepad, "Thread", FakeThread), patch.object(
        gamepad, "syscommand", side_effect=lambda *args, **kwargs: next(outputs)
    ):
        addon.watch_gamepads()
        event2_watcher = addon.running_threads["event2"]
        addon.watch_gamepads()

    assert addon.running_threads == {"event2": event2_watcher}
