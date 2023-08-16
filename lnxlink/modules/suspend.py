"""Suspend/sleep the system"""
import subprocess


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Suspend"

    def start_control(self, topic, data):
        """Control system"""
        subprocess.call(["systemctl", "suspend"])

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "suspend": {
                "type": "button",
                "icon": "mdi:progress-clock",
            }
        }
