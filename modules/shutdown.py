import subprocess

class Addon():
    name = 'Shutdown'
    icon = 'mdi:power'
    unit = 'button'

    def startControl(self, topic, data):
        subprocess.call(["shutdown", "now"])

    def exposedControls(self):
        return {
            "shutdown": {
                "type": "button",
                "icon": "mdi:power",
            }
        }
