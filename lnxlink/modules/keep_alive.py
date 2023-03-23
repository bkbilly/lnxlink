import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Keep Alive'
        self.keepalive = 'OFF'

    def exposedControls(self):
        return {
            "Keep Alive": {
                "type": "switch",
                "icon": "mdi:mouse-variant",
            }
        }

    def getControlInfo(self):
        if self.keepalive == 'ON':
            subprocess.run(
                "xdotool key 0x00",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).stdout.decode("UTF-8")

        return self.keepalive

    def startControl(self, topic, data):
        if data.lower() == 'off':
            self.keepalive = 'OFF'
        elif data.lower() == 'on':
            self.keepalive = 'ON'
