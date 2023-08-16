"""Checks for system updates"""
import subprocess
import time


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "System Updates"
        self.last_time = 0
        self.update_interval = 7200  # Check for updates every 2 hours

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "System Updates": {
                "type": "binary_sensor",
                "icon": "mdi:package-variant",
                "entity_category": "diagnostic",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        packages = [
            {
                "command": "apt list --upgradable | wc -l",
                "logic": "> 2",
            },
            {
                "command": "yum -q updateinfo list updates | wc -l",
                "logic": "> 2",
            },
        ]

        update_available = False
        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            for package in packages:
                proc = subprocess.run(
                    package["command"],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                result = proc.stdout.strip().decode()
                update_available = eval(f"{result}{package['logic']}")
                if update_available:
                    return True
        return update_available
