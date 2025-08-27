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
        command = data.lower()
        if not command in {"on", "off"}:
            logger.error("Expected `on` or `off`, received: `%s`", command)
        if self.lnxlink.display is not None:
            maybe_display = f"-display {self.lnxlink.display}"
        else:
            maybe_display = ""
        syscommand(
            f"xset {maybe_display} dpms force {command}"
        )
