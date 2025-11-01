"""Turns on or off the screen"""
import re
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand, get_display_variable

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Screen OnOff"
        self.display_variable = None
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
        self.display_variable = get_display_variable()
        if self.display_variable is not None:
            command = f"xset -display {self.display_variable} q"
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
        command = data.lower()
        if command not in {"on", "off"}:
            logger.error("Expected `on` or `off`, received: `%s`", command)
        if self.display_variable is not None:
            maybe_display = f"-display {self.display_variable}"
        else:
            maybe_display = ""
        syscommand(f"xset {maybe_display} dpms force {command}")
