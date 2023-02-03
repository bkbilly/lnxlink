import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'xdg_open'

    def startControl(self, topic, data):
        print(f"/usr/bin/xdg-open {data}")
        subprocess.call(f"/usr/bin/xdg-open {data}", shell=True)
