import subprocess


class Addon():
    name = 'Keep Alive'
    icon = 'mdi:mouse-variant'
    unit = None
    sensor_type = 'switch'
    keepalive = 'OFF'

    def exposedControls(self):
        return {
            "Keep_Alive": {
                "type": "switch",
                "icon": "mdi:mouse-variant",
            }
        }

    def getInfo(self):
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
