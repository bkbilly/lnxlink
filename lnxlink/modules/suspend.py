import subprocess

class Addon():
    name = 'Suspend'
    icon = 'mdi:progress-clock'
    unit = 'button'

    def startControl(self, topic, data):
        subprocess.call(["systemctl", "suspend"])

    def exposedControls(self):
        return {
            "suspend": {
                "type": "button",
                "icon": "mdi:progress-clock",
            }
        }
