import subprocess
import re


class Addon():
    name = 'Bluetooth Battery'
    icon = 'mdi:battery'
    device_class = 'battery'
    unit = '%'

    def getInfo(self):
        stdout = subprocess.run(
            'upower --dump | grep percentage',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        results = stdout.strip().split()

        percentage = -1
        if len(results) >= 2:
            if re.match(r'\d+%', results[1]):
                percentage = int(results[1].replace("%", ""))

        return percentage
