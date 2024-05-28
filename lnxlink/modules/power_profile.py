"""Selects the Power Profile"""
import re
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink=None):
        """Setup addon"""
        self.name = "Power Profile"
        self.lnxlink = lnxlink
        if which("powerprofilesctl") is None:
            raise SystemError("System command 'powerprofilesctl' not found")
        self.options = self._get_power_profiles()

    def get_info(self):
        """Gather information from the system"""
        stdout, _, _ = syscommand("powerprofilesctl get")
        return stdout

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        if len(self.options) > 0:
            discovery_info = {
                "Power Profile": {
                    "type": "select",
                    "icon": "mdi:leaf",
                    "options": self.options,
                }
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        syscommand(f"powerprofilesctl set {data}")

    def _get_power_profiles(self):
        """Get the power profiles in the correct order"""
        profiles_pattern = re.compile(r"([\w-]+):\n")

        stdout, _, _ = syscommand("powerprofilesctl list")
        profiles = re.findall(profiles_pattern, stdout)

        return profiles
