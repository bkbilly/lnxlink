"""Turns on or off the screen"""
import re
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Screen OnOff"
        self.lnxlink = lnxlink

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Screen OnOff": {
                "type": "switch",
                "icon": "mdi:monitor",
            }
        }

    def get_info(self):
        """Gather information from the system"""
        status = "ON"
        if self.lnxlink.display is not None:
            stdout, _, _ = syscommand(f"xset -display {self.lnxlink.display} q")
            match = re.findall(r"Monitor is (\w*)", stdout)
            if match:
                status = match[0].upper()

        return status

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            syscommand(f"xset -display {self.lnxlink.display} dpms force off")
        elif data.lower() == "on":
            syscommand(f"xset -display {self.lnxlink.display} dpms force on")
