import subprocess


class Addon():
    name = 'xdg_open'
    icon = None
    unit = None

    def startControl(self, topic, data):
        print(f"/usr/bin/xdg-open {data}")
        subprocess.call(f"/usr/bin/xdg-open {data}", shell=True)
