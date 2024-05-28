"""Turns on or off the screen"""
import re
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Screen OnOff"
        self.lnxlink = lnxlink
        if which("xset") is None:
            raise SystemError("System command 'xset' not found")

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
        status = "ON"
        if self.lnxlink.display is not None:
            command = f"xset -display {self.lnxlink.display} q"
            stdout, _, _ = syscommand(command)
            match = re.findall(r"Monitor is (\w*)", stdout)
            if match:
                status = match[0].upper()
            else:
                logger.debug("Screen_onoff error: %s\n%s", command, stdout)
        else:
            logger.debug("No display variable found")

        return status

    def start_control(self, topic, data):
        """Control system"""
        if data.lower() == "off":
            syscommand(f"xset -display {self.lnxlink.display} dpms force off")
        elif data.lower() == "on":
            syscommand(f"xset -display {self.lnxlink.display} dpms force on")
