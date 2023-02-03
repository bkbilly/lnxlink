import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Camera used'
        self.icon = 'mdi:webcam'
        self.sensor_type = 'binary_sensor'

    def getInfo(self):
        stdout = subprocess.run(
            "lsmod | grep '^uvcvideo ' | awk '{print $3}'",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")

        cam_used = bool(int(stdout.strip()))
        if cam_used:
            return "ON"
        return "OFF"
