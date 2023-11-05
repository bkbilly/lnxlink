"""Checks if the webcam is used"""
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Camera used"

    def get_info(self):
        """Gather information from the system"""
        _, _, returncode = syscommand("fuser /dev/video*", ignore_errors=True)
        cam_used = False
        if returncode == 0:
            cam_used = True

        return cam_used

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Camera used": {
                "type": "binary_sensor",
                "icon": "mdi:webcam",
            },
        }
