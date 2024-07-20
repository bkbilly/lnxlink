"""Sends statistics information"""
import os
import uuid
import json
import logging
import time
import requests

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Statistics"
        self.lnxlink = lnxlink
        # Check for updates every 24 hours
        self.update_interval = 86400
        # 15 minutes after lnxlink starts
        self.last_time = time.time() - self.update_interval + 900
        self.url = self.lnxlink.config["settings"]["statistics"]
        if self.url is None or self.url == "":
            raise SystemError("Statistics is not setup correctly")
        self.uuid = self._get_uuid()

    def get_info(self):
        """Gather information from the system"""
        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            version = self.lnxlink.version.split("+")[0]
            data = json.dumps(
                {
                    "uuid": self.uuid,
                    "version": version,
                }
            )
            logger.info("Sending statistics data: %s", data)
            url = self.url.rstrip("/")
            url = f"{url}/api/lnxlink"
            requests.post(url=url, data=data)
            self.last_time = cur_time

    def _get_uuid(self):
        """Creates a Unique ID once to send it to the analyzer server"""
        config_dir = os.path.dirname(os.path.realpath(self.lnxlink.config_path))
        uuid_file = os.path.join(config_dir, "lnxlink_uuid.txt")
        if os.path.exists(uuid_file):
            with open(uuid_file, encoding="UTF-8") as file:
                return file.read()
        else:
            tmp_uuid = uuid.uuid4().hex
            with open(uuid_file, "w", encoding="UTF-8") as file:
                file.write(tmp_uuid)
            return tmp_uuid
