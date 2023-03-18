import subprocess
import time


class Addon():

    def __init__(self, lnxlink):
        self.name = 'System Updates'
        self.icon = 'mdi:package-variant'
        self.sensor_type = 'binary_sensor'
        self.last_time = 0
        self.update_interval = 7200  # Check for updates every 2 hours

    def getInfo(self):
        packages = [
            {
                'command': 'apt list --upgradable | wc -l',
                'logic': '> 2',
            },
            {
                'command': 'yum -q updateinfo list updates | wc -l',
                'logic': '> 2',
            },
        ]

        update_available = False
        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            for package in packages:
                proc = subprocess.run(
                    package['command'],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                result = proc.stdout.strip().decode()
                update_available = eval(f"{result}{package['logic']}")
                if update_available:
                    return True
        return update_available
