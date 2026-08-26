"""Tests for webcam capture lifecycle and concurrent controls."""
# pylint: disable=invalid-name,missing-class-docstring,missing-function-docstring,protected-access

import time
from threading import Event, Lock, Thread

from lnxlink.modules import webcam


class FakeCapture:
    def __init__(self, frames, delay=0.0):
        self.frames = list(frames)
        self.delay = delay
        self.released = False
        self.read_started = Event()

    def read(self):
        self.read_started.set()
        if self.delay:
            time.sleep(self.delay)
        if self.frames:
            return self.frames.pop(0)
        return False, None

    def release(self):
        self.released = True


class FakeCV2:
    def __init__(self, capture):
        self.captures = capture if isinstance(capture, list) else [capture]
        self.capture_calls = 0

    def VideoCapture(self, *_):
        self.capture_calls += 1
        return self.captures[self.capture_calls - 1]

    def imencode(self, *_args, **_kwargs):
        return True, b"encoded-frame"


class FakeLnxlink:
    def __init__(self):
        self.calls = []
        self.call_received = Event()

    def run_module(self, name, value):
        self.calls.append((name, value))
        self.call_received.set()


def make_addon(capture):
    addon = object.__new__(webcam.Addon)
    addon.name = "Webcam"
    addon.lnxlink = FakeLnxlink()
    addon.lib = {"cv2": FakeCV2(capture)}
    addon.vid = None
    addon.read_thr = None
    addon._control_lock = Lock()
    addon._reader_failed = False
    return addon


def test_off_before_on_is_idempotent():
    addon = make_addon(FakeCapture([]))

    addon.start_control(("webcam",), "off")

    assert addon.vid is None
    assert addon.read_thr is None


def test_failed_read_clears_state_and_release():
    capture = FakeCapture([(False, None)])
    addon = make_addon(capture)
    addon.vid = capture

    addon.get_camera_frame()

    assert capture.released is True
    assert addon.vid is None
    assert addon.read_thr is None
    assert addon.get_info() is False


def test_live_capture_reports_on_and_can_stop_cleanly():
    capture = FakeCapture([(True, object())] * 20, delay=0.01)
    addon = make_addon(capture)

    addon.start_control(("webcam",), "on")
    assert capture.read_started.wait(timeout=1)
    assert addon.lnxlink.call_received.wait(timeout=1)

    assert addon.get_info() is True
    assert addon.lnxlink.calls

    addon.start_control(("webcam",), "off")

    assert capture.released is True
    assert addon.vid is None
    assert addon.read_thr is None


def test_repeated_on_keeps_the_active_capture_and_reader():
    capture = FakeCapture([(True, object())] * 20, delay=0.01)
    addon = make_addon(capture)

    addon.start_control(("webcam",), "on")
    first_thread = addon.read_thr
    addon.start_control(("webcam",), "on")

    assert addon.vid is capture
    assert addon.read_thr is first_thread
    assert addon.lib["cv2"].capture_calls == 1

    addon.start_control(("webcam",), "off")


def test_concurrent_on_controls_share_one_started_reader():
    capture = FakeCapture([(True, object())] * 20, delay=0.01)
    addon = make_addon(capture)
    callers = [
        Thread(target=addon.start_control, args=(("webcam",), "on")) for _ in range(2)
    ]

    for caller in callers:
        caller.start()
    for caller in callers:
        caller.join()

    assert capture.read_started.wait(timeout=1)
    assert addon.get_info() is True
    assert addon.lib["cv2"].capture_calls == 1

    addon.start_control(("webcam",), "off")


def test_on_during_failed_reader_cleanup_restarts_after_cleanup():
    class BlockingReleaseCapture(FakeCapture):
        def __init__(self):
            super().__init__([(False, None)])
            self.release_started = Event()
            self.release_continue = Event()

        def release(self):
            self.release_started.set()
            self.release_continue.wait(timeout=1)
            super().release()

    failed_capture = BlockingReleaseCapture()
    replacement_capture = FakeCapture([(True, object())] * 20, delay=0.01)
    addon = make_addon([failed_capture, replacement_capture])

    addon.start_control(("webcam",), "on")
    assert failed_capture.release_started.wait(timeout=1)

    restart = Thread(target=addon.start_control, args=(("webcam",), "on"))
    restart.start()
    failed_capture.release_continue.set()
    restart.join(timeout=1)

    assert not restart.is_alive()
    assert replacement_capture.read_started.wait(timeout=1)
    assert addon.vid is replacement_capture
    assert addon.lib["cv2"].capture_calls == 2

    addon.start_control(("webcam",), "off")
