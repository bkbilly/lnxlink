"""Checks if the webcam is used"""
import subprocess
import glob


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Camera used"

    def get_info(self):
        """Gather information from the system"""
        videos = glob.glob("/dev/video*", recursive=True)
        cam_used = False
        for video in videos:
            proc = subprocess.run(
                f"fuser {video}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if proc.returncode == 0:
                cam_used = True

        if cam_used:
            return "ON"
        return "OFF"

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Camera used": {
                "type": "binary_sensor",
                "icon": "mdi:webcam",
            },
        }
