"""Checks if the webcam is used"""
import glob
from threading import Thread
from inotify.adapters import Inotify


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Camera used"
        self.lnxlink = lnxlink
        self.inotify = Inotify()
        self.cameras = []
        Thread(target=self._watch_events, daemon=True).start()

    def get_info(self):
        """Gather information from the system"""
        cameras = glob.glob("/dev/video*", recursive=True)
        if cameras != self.cameras:
            self.cameras = cameras
            for camera in cameras:
                self.inotify.add_watch(camera)

    def _watch_events(self):
        for event in self.inotify.event_gen(yield_nones=False):
            cam_used = event[1][0] == "IN_OPEN"
            self.lnxlink.run_module(self.name, cam_used)

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Camera used": {
                "type": "binary_sensor",
                "icon": "mdi:webcam",
            },
        }
