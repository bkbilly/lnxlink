import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Screen OnOff'

    def exposedControls(self):
        return {
            "Screen OnOff": {
                "type": "switch",
                "icon": "mdi:monitor",
            }
        }

    def getControlInfo(self):
        stdout = subprocess.run(
            "xset q | grep -i 'monitor is'",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        results = stdout.lower()

        status = results.strip().replace('monitor is', '').strip().upper()
        return status

    def startControl(self, topic, data):
        if data.lower() == 'off':
            subprocess.call('xset dpms force off', shell=True)
        elif data.lower() == 'on':
            subprocess.call('xset dpms force on', shell=True)
