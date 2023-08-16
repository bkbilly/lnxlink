"""Checks if restart is needed"""
import os


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Required Restart"

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Required Restart": {
                "type": "binary_sensor",
                "icon": "mdi:alert-octagon-outline",
                "entity_category": "diagnostic",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        if os.path.exists("/var/run/reboot-required"):
            return "ON"
        return "OFF"
