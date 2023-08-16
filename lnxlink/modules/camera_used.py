"""Checks if the webcam is used"""
import subprocess
import glob


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Camera used"
        self.icon = "mdi:webcam"
        self.sensor_type = "binary_sensor"

    def get_old_info(self):
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
