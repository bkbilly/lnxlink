"""Open URLs or files"""
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "xdg_open"
        if which("xdg-open") is None:
            raise SystemError("System command 'xdg-open' not found")

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "XDG Open": {
                "type": "text",
                "icon": "mdi:file-find-outline",
            }
        }

    def start_control(self, topic, data):
        """Control system"""
        logger.info("xdg-open %s", data)
        syscommand(f"xdg-open {data}", background=True)
