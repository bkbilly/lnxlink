"""Watches for configuration changes and restarts LNXlink"""
import hashlib
import logging
import os

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Watch Changes"
        self.lnxlink = lnxlink
        self.last_time = 0
        self.last_updated = self._get_file_mtime(self.lnxlink.config_path)
        self.last_hash = (
            self._get_file_hash(self.lnxlink.config_path)
            if self.last_updated is not None
            else None
        )

    def get_info(self):
        """Gather information from the system"""
        current_time = self._get_file_mtime(self.lnxlink.config_path)
        if current_time is None:
            self.last_updated = None
            return
        if current_time != self.last_updated:
            current_hash = self._get_file_hash(self.lnxlink.config_path)
            if current_hash is None:
                self.last_updated = None
                return
            self.last_updated = current_time
            if current_hash != self.last_hash:
                self.last_hash = current_hash
                self.lnxlink.restart_script()

    def _get_file_mtime(self, filepath):
        """Return the file modification time or None if the file is absent."""
        try:
            return os.path.getmtime(filepath)
        except FileNotFoundError:
            return None

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
