"""Checks for system updates"""
import time
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "System Updates"
        self.last_time = 0
        self.update_interval = 360  # Check for updates every 6 minutes
        self.updates = {
            "needs_update": "OFF",
            "packages": {"updates": []},
        }
        self.package_manager = None
        if which("apt") is not None:
            self.package_manager = {
                "command": "apt list --upgradable | grep -v '.*\\.\\.\\.' | awk -F '/' '{print $1}'",
                "largerthan": 0,
            }
        elif which("yum") is not None:
            self.package_manager = {
                "command": "yum -q updateinfo list updates",
                "largerthan": 2,
            }
        elif which("pacman") is not None:
            self.package_manager = {
                "command": "pacman -Qu",
                "largerthan": 0,
            }
        elif which("dnf") is not None:
            self.package_manager = {
                "command": "dnf updateinfo list",
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
                "value_template": "{{ value_json.needs_update }}",
            },
            "System Updates Count": {
                "type": "sensor",
                "icon": "mdi:package-variant",
                "entity_category": "diagnostic",
                "value_template": "{{ value_json.packages.updates | count }}",
                "attributes_template": "{{ value_json.packages | tojson }}",
                "enabled": False,
            },
        }

    def get_info(self):
        """Gather information from the system"""
        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            self.last_time = cur_time
            stdout, _, _ = syscommand(self.package_manager["command"])
            if len(stdout) == 0:
                self.updates["needs_update"] = "OFF"
                self.updates["packages"]["updates"] = []
            else:
                current_updates = stdout.split("\n")
                needs_update = len(current_updates) > self.package_manager["largerthan"]
                self.updates["needs_update"] = "ON" if needs_update else "OFF"
                self.updates["packages"]["updates"] = current_updates
        return self.updates
