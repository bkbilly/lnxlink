import subprocess

class Addon():
    name = 'Restart'
    icon = 'mdi:restart'
    unit = 'button'

    def startControl(self, topic, data):
        subprocess.call(["shutdown", "-r", "now"])

    def exposedControls(self):
        return {
            "shutdown": {
                "type": "button",
                "icon": "mdi:restart",
            }
        }