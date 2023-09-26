"""Checks if the webcam is used"""
import subprocess


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Camera used"

    def get_info(self):
        """Gather information from the system"""
        proc = subprocess.run(
            "fuser /dev/video*",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        cam_used = False
        if proc.returncode == 0:
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
