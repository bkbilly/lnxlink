import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Suspend'

    def startControl(self, topic, data):
        subprocess.call(["systemctl", "suspend"])

    def exposedControls(self):
        return {
            "suspend": {
                "type": "button",
                "icon": "mdi:progress-clock",
            }
        }
