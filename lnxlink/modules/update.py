"""Checks for LNXlink updates"""
import re
import sys
import logging
import time
import requests
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "LNXlink update"
        self.lnxlink = lnxlink
        self.last_time = 0
        self.update_interval = 86400  # Check for updates every 24 hours
        self.message = {
            "installed_version": self.lnxlink.version,
            "latest_version": self.lnxlink.version,
            "release_summary": "",
            "release_url": "https://github.com/bkbilly/lnxlink/releases/latest",
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        image_url = (
            "https://raw.githubusercontent.com/bkbilly/lnxlink/6d844af/images/logo.png"
        )
        return {
            "Update": {
                "type": "update",
                "title": "LNXlink",
                "icon": "mdi:update",
                "entity_category": "diagnostic",
                "entity_picture": image_url,
                "install": "install",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            self._latest_version()
            self.last_time = cur_time

        return self.message

    def _latest_version(self):
        """Gets the currently published version of lnxlink"""
        url = "https://api.github.com/repos/bkbilly/lnxlink/releases/latest"
        try:
            resp = requests.get(url=url, timeout=5).json()
            body = re.sub(r"##.*\n", "", resp["body"])
            self.message["latest_version"] = resp["tag_name"]
            self.message["release_summary"] = body
            self.message["release_url"] = resp["html_url"]
        except Exception as err:
            logger.error(err)

    def start_control(self, topic, data):
        """Control system"""
        if "+edit" in self.lnxlink.version:
            syscommand(f"git -C {self.lnxlink.path} pull", timeout=15)
            syscommand(
                f"{sys.executable} -m pip install -e {self.lnxlink.path}", timeout=120
            )
        else:
            syscommand(f"{sys.executable} -m pip install -U lnxlink", timeout=120)
        self.lnxlink.restart_script()
