import os


class Addon():
    name = 'Required Restart'
    icon = 'mdi:alert-octagon-outline'
    sensor_type = 'binary_sensor'
    unit = ''

    def getInfo(self):
        if os.path.exists('/var/run/reboot-required'):
            return "ON"
        else:
            return "OFF"
