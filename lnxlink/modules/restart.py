import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Restart'
        self.lnxlink = lnxlink

    def startControl(self, topic, data):
        self.lnxlink.temp_connection_callback(True)
        subprocess.call(["shutdown", "-r", "now", "&"])

    def exposedControls(self):
        return {
            "restart": {
                "type": "button",
                "icon": "mdi:restart",
            }
        }
