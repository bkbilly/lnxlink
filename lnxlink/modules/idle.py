import subprocess


class Addon():
    name = 'Idle'
    icon = 'mdi:timer-sand'
    unit = 'sec'

    def getInfo(self):
        stdout = subprocess.run(
            'xprintidle',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8").strip()

        idle_sec = round(float(stdout.strip()) / 1000, 0)

        return idle_sec
