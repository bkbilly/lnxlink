"""Watches for configuration changes and restarts LNXlink"""
import logging
import hashlib
import os

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Watch Changes"
        self.lnxlink = lnxlink
        self.last_time = 0
        self.last_updated = os.path.getmtime(self.lnxlink.config_path)
        self.last_hash = self._get_file_hash(self.lnxlink.config_path)

    def get_info(self):
        """Gather information from the system"""
        current_time = os.path.getmtime(self.lnxlink.config_path)
        if current_time != self.last_updated:
            self.last_updated = current_time
            current_hash = self._get_file_hash(self.lnxlink.config_path)
            if current_hash != self.last_hash:
                self.last_hash = current_hash
                self.lnxlink.restart_script()

    def _get_file_hash(self, filepath):
        """Generates a SHA-256 hash of the file content."""
        hasher = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                # Read in chunks to handle large files efficiently
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except FileNotFoundError:
            return None
