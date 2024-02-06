"""Open URLs or files"""
import logging
from shutil import which
from .scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "xdg_open"
        if which("xdg-open") is None:
            raise SystemError("System command 'xdg-open' not found")

    def start_control(self, topic, data):
        """Control system"""
        logger.info("/usr/bin/xdg-open %s", data)
        syscommand(f"/usr/bin/xdg-open {data}")
