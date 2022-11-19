import subprocess


class Addon():
    name = 'bash'
    icon = None
    unit = None

    def startControl(self, topic, data):
        subprocess.call(f"{data}", shell=True)
