import subprocess

class Addon():
    service = 'restart'
    name = 'Restart'
    icon = 'mdi:restart'
    unit = 'json'

    def startControl(self, topic, data):
        print(topic, data)
        subprocess.call(["shutdown", "-r", "now"])
