import os


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Required Restart'

    def exposedControls(self):
        return {
            "Required Restart": {
                "type": "binary_sensor",
                "icon": "mdi:alert-octagon-outline",
                "entity_category": "diagnostic",
            },
        }

    def getControlInfo(self):
        if os.path.exists('/var/run/reboot-required'):
            return "ON"
        else:
            return "OFF"
