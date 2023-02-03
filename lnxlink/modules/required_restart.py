import os


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Required Restart'
        self.sensor_type = 'binary_sensor'
        self.icon = 'mdi:alert-octagon-outline'

    def getInfo(self):
        if os.path.exists('/var/run/reboot-required'):
            return "ON"
        else:
            return "OFF"
