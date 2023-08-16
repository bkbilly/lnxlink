"""Restarts the system"""
import subprocess


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Restart"
        self.lnxlink = lnxlink

    def start_control(self, topic, data):
        """Control system"""
        self.lnxlink.temp_connection_callback(True)
        subprocess.call(["shutdown", "-r", "now", "&"])

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "restart": {
                "type": "button",
                "icon": "mdi:restart",
            }
        }
