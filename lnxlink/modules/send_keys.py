"""Uses xdotool to press keyboard keys"""
import os
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Send Keys"
        self.lnxlink = lnxlink
        if which("xdotool") is None:
            raise SystemError("System command 'xdotool' not found")

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Send Keys": {
                "type": "text",
                "icon": "mdi:keyboard-outline",
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        if os.environ.get("DISPLAY") is None:
            if self.lnxlink.display is not None:
                os.environ["DISPLAY"] = self.lnxlink.display
                logger.info("Initializing empty DISPLAY environment variable")
        syscommand(f"xdotool key {data}")
