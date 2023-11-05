"""Shutdown the system"""
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Shutdown"
        self.lnxlink = lnxlink

    def start_control(self, topic, data):
        """Control system"""
        self.lnxlink.temp_connection_callback(True)
        _, _, returncode = syscommand("systemctl poweroff")
        if returncode != 0:
            _, _, returncode = syscommand("shutdown now")

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "shutdown": {
                "type": "button",
                "icon": "mdi:power",
            }
        }
