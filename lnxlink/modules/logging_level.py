"""Information and control of logging level"""
import logging

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Logging Level"
        self.lnxlink = lnxlink

    def exposed_controls(self):
        """Exposes to home assistant"""
        log_levels = [
            "NOTSET",
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
        ]
        return {
            "Logging Level": {
                "type": "select",
                "icon": "mdi:math-log",
                "options": log_levels,
                "entity_category": "diagnostic",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        current_level = logger.getEffectiveLevel()
        level_name = logging.getLevelName(current_level)
        return level_name

    def start_control(self, topic, data):
        """Control system"""
        if data in [0, "notset", "Notset", "NOTSET"]:
            logger.setLevel(logging.NOTSET)
        elif data in [1, 10, "debug", "Debug", "DEBUG"]:
            logger.setLevel(logging.DEBUG)
        elif data in [2, 20, "info", "Info", "INFO"]:
            logger.setLevel(logging.INFO)
        elif data in [3, 30, "warning", "Warning", "WARNING"]:
            logger.setLevel(logging.WARNING)
        elif data in [4, 40, "error", "Error", "ERROR"]:
            logger.setLevel(logging.ERROR)
        elif data in [5, 50, "critical", "Critical", "CRITICAL"]:
            logger.setLevel(logging.CRITICAL)
