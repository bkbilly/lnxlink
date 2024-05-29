"""Suspend/sleep the system"""
from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Suspend"

    def start_control(self, topic, data):
        """Control system"""
        syscommand("systemctl suspend")

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Suspend": {
                "type": "button",
                "icon": "mdi:progress-clock",
            }
        }
