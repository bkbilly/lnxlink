"""Gets Display Environment"""
from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Display Environment"
        self.lnxlink = lnxlink

    def get_info(self):
        """Gather information from the system"""
        display_var, _, _ = syscommand("echo $DISPLAY")
        if display_var:
            if display_var == "":
                display_var = None
            self.lnxlink.display = display_var
            return display_var
        other_displays, _, _ = syscommand(
            "sed -zn 's/^DISPLAY=//p' /proc/*/environ 2> /dev/null | LC_ALL=C sort -zu | tr '\\0' '\\n'"
        )
        other_displays = other_displays.split("\n")
        if len(other_displays) > 0:
            if other_displays[0] == "":
                other_displays[0] = None
            self.lnxlink.display = other_displays[0]
            return other_displays[0]
        return None

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
