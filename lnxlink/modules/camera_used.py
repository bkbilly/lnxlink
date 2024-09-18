"""Checks if the webcam is used"""
import glob
from threading import Thread
from inotify.adapters import Inotify
from lnxlink.modules.scripts.helpers import syscommand


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
            # Initialize camera
            _, _, returncode = syscommand("fuser /dev/video*", ignore_errors=True)
            cam_used = False
            if returncode == 0:
                cam_used = True
            self.lnxlink.run_module(self.name, cam_used)

    def _watch_events(self):
        for _ in self.inotify.event_gen(yield_nones=False):
            cam_used = False
            _, _, returncode = syscommand("fuser /dev/video*", ignore_errors=True)
            if returncode == 0:
                cam_used = True
            self.lnxlink.run_module(self.name, cam_used)

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Camera used": {
                "type": "binary_sensor",
                "icon": "mdi:webcam",
            },
        }
