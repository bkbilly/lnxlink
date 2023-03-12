import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Shutdown'
        self.lnxlink = lnxlink

    def startControl(self, topic, data):
        self.lnxlink.temp_connection_callback(True)
        subprocess.call(["shutdown", "1", "&"])

    def exposedControls(self):
        return {
            "shutdown": {
                "type": "button",
                "icon": "mdi:power",
            }
        }
