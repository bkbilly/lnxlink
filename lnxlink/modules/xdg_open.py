"""Open URLs or files"""
import logging
from .scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "xdg_open"

    def start_control(self, topic, data):
        """Control system"""
        logger.info("/usr/bin/xdg-open %s", data)
        syscommand(f"/usr/bin/xdg-open {data}")
