"""Opt-in to send anonymous usage data to help improve LNXlink"""
import json
import logging
import os
import time
import uuid

import requests

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    DEFAULT_URL = "https://analyzer.bkbilly.workers.dev"

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Statistics"
        self.lnxlink = lnxlink
        self.lnxlink.add_settings("statistics", self._settings(), replace_empty=True)
        settings = self.lnxlink.config["settings"]["statistics"]
        # Check for updates every 24 hours
        self.update_interval = 86400
        # 15 minutes after lnxlink starts
        self.last_time = time.time() - self.update_interval + 900
        self.url = settings["url"]
        if self.url is None or self.url == "":
            raise SystemError("Statistics is not setup correctly")
        self.uuid = settings["uuid"]

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
            requests.post(url=url, data=data, timeout=10)
            self.last_time = cur_time

    def _settings(self):
        """Return statistics settings, migrating previous config values."""
        settings = self.lnxlink.config["settings"].get("statistics", {})
        if isinstance(settings, dict):
            return {
                "url": settings.get("url", self.DEFAULT_URL),
                "uuid": settings.get("uuid") or self._get_legacy_uuid(),
            }
        return {
            "url": settings if settings is not None else self.DEFAULT_URL,
            "uuid": self._get_legacy_uuid(),
        }

    def _get_legacy_uuid(self):
        """Read the old UUID file or create a new UUID for migration."""
        config_dir = os.path.dirname(os.path.realpath(self.lnxlink.config_path))
        uuid_file = os.path.join(config_dir, "lnxlink_uuid.txt")
        if os.path.exists(uuid_file):
            with open(uuid_file, encoding="UTF-8") as file:
                return file.read().strip()
        return uuid.uuid4().hex
