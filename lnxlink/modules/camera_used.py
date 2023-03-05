import subprocess
import glob


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Camera used'
        self.icon = 'mdi:webcam'
        self.sensor_type = 'binary_sensor'

    def getInfo(self):
        videos = glob.glob('/dev/video*', recursive=True)
        cam_used = False
        for video in videos:
            proc = subprocess.run(
                f"fuser {video}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            if proc.returncode == 0:
                cam_used = True

        if cam_used:
            return "ON"
        return "OFF"
