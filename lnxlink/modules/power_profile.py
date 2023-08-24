"""Selects the Power Profile"""
import re


class Addon:
    """Addon module"""

    def __init__(self, lnxlink=None):
        """Setup addon"""
        self.name = "Power Profile"
        self.lnxlink = lnxlink
        self.options = self._get_power_profiles()

    def get_info(self):
        """Gather information from the system"""
        stdout, _ = self.lnxlink.subprocess("powerprofilesctl get")
        return stdout

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Power Profile": {
                "type": "select",
                "icon": "mdi:leaf",
                "options": self.options,
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        self.lnxlink.subprocess(f"powerprofilesctl set {data}")

    def _get_power_profiles(self):
        """Get the power profiles in the correct order"""
        profiles_pattern = re.compile(r"([\w-]+):\n")

        stdout, _ = self.lnxlink.subprocess("powerprofilesctl list")
        profiles = re.findall(profiles_pattern, stdout)

        return profiles
