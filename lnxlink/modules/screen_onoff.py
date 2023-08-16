"""Turns on or off the screen"""
import subprocess


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
        stdout, _ = self.lnxlink.subprocess(
            "xset q | grep -i 'monitor is'",
        )
        results = stdout.lower()

        status = results.strip().replace("monitor is", "").strip().upper()
        return status

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            subprocess.call("xset dpms force off", shell=True)
        elif data.lower() == "on":
            subprocess.call("xset dpms force on", shell=True)
