import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Send Keys'

    def exposedControls(self):
        return {
            "Send_Keys": {
                "type": "text",
                "icon": "mdi:keyboard-outline",
            }
        }

    def startControl(self, topic, data):
        subprocess.call(f"xdotool key {data}", shell=True)
