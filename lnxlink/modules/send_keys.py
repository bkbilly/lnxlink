import subprocess


class Addon():
    name = 'Send Keys'

    def exposedControls(self):
        return {
            "Send_Keys": {
                "type": "text",
                "icon": "mdi:keyboard-outline",
            }
        }

    def startControl(self, topic, data):
        subprocess.call(f"xdotool key {data}", shell=True)
