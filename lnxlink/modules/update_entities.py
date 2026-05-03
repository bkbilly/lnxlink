"""Manually update entities"""
import logging

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Update Entities"
        self.lnxlink = lnxlink

    def exposed_controls(self):
        """Exposes to home assistant"""
        module_list = ["all"]
        for _, addon in self.lnxlink.addons.items():
            if hasattr(addon, "get_info"):
                module_list.append(addon.name)

        return {
            "Update Entities": {
                "type": "select",
                "icon": "mdi:cube-send",
                "options": module_list,
            },
        }

    def start_control(self, topic, data):
        """Control system"""
        logger.info(data)
        if data == "all":
            self.lnxlink.run_modules()
        else:
            self.lnxlink.run_modules(data)
