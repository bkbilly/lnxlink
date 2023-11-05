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
        stdout, _, _ = syscommand("xset q")
        match = re.findall(r"Monitor is (\w*)", stdout)
        status = "ON"
        if match:
            status = match[0].upper()

        return status

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            syscommand("xset dpms force off")
        elif data.lower() == "on":
            syscommand("xset dpms force on")
