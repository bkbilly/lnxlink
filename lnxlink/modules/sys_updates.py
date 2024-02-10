"""Checks for system updates"""
import time
from shutil import which
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "System Updates"
        self.last_time = 0
        self.update_interval = 360  # Check for updates every 6 minutes
        self.update_available = False
        self.package_manager = None
        if which("apt") is not None:
            self.package_manager = {
                "command": "apt list --upgradable | wc -l",
                "largerthan": 2,
            }
        elif which("yum") is not None:
            self.package_manager = {
                "command": "yum -q updateinfo list updates | wc -l",
                "largerthan": 2,
            }
        elif which("pacman") is not None:
            self.package_manager = {
                "command": "pacman -Qu | wc -l",
                "largerthan": 0,
            }
        elif which("dnf") is not None:
            self.package_manager = {
                "command": "dnf updateinfo list | wc -l",
                "largerthan": 1,
            }
        else:
            raise SystemError("System commands not found for package manager")

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
        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            self.last_time = cur_time
            stdout, _, _ = syscommand(self.package_manager["command"])
            self.update_available = int(stdout) > self.package_manager["largerthan"]
        return self.update_available
