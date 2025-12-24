"""Identify the current display environment"""
from lnxlink.modules.scripts.helpers import get_display_variable


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Display Environment"

    def get_info(self):
        """Gather information from the system"""
        return get_display_variable()

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Display Environment": {
                "type": "sensor",
                "icon": "mdi:panorama-variant-outline",
                "entity_category": "diagnostic",
                "enabled": False,
            }
        }
