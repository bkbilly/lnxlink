"""Checks for system updates"""
import time
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "System Updates"
        self.last_time = 0
        self.update_interval = 360  # Check for updates every 6 minutes
        self.update_available = False

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

        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            self.last_time = cur_time
            for package in packages:
                stdout, _, _ = syscommand(package["command"])
                self.update_available = eval(f"{stdout}{package['logic']}")
                if self.update_available:
                    return True
        return self.update_available
