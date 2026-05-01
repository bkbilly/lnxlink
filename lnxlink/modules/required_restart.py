"""Detect if a system reboot is needed"""
import os
import time
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand
import logging
logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Required Restart"
        self.last_time = 0
        self.update_interval = 360  # Check for updates every 6 minutes
        self.value = {
            "needs_restart": "OFF",
            "attributes": {
                "details": "",
            },
        }

        self.restart_checker = None
        if which("needrestart") is not None:
            self.restart_checker = {
                "command": "needrestart -p",
            }
        elif which("dnf") is not None:
            self.restart_checker = {
                "command": "dnf needs-restarting -r",
            }
        elif which("yum") is not None:
            self.restart_checker = {
                "command": "yum needs-restarting -r",
            }
        else:
            logger.warning(
                "No Required_Restart command detected, consider installing package 'needrestart'."
            )
            logger.warning("Falling back to checking /var/run/reboot-required")

        if self.restart_checker is not None:
            logger.info(
                "Required_Restart command found, using '%s'",
                self.restart_checker["command"],
            )

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Required Restart": {
                "type": "binary_sensor",
                "icon": "mdi:alert-octagon-outline",
                "entity_category": "diagnostic",
                "value_template": "{{ value_json.needs_restart }}",
                "attributes_template": "{{ value_json.attributes | tojson }}",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        cur_time = time.time()
        if cur_time - self.last_time > self.update_interval:
            self.last_time = cur_time

            self.value["needs_restart"] = "OFF"
            self.value["attributes"]["details"] = ""
            if self.restart_checker is not None:
                stdout, stderr, returncode = syscommand(
                    self.restart_checker["command"], ignore_errors=True, timeout=30
                )
                if returncode != 0:
                    self.value["needs_restart"] = "ON"
                self.value["attributes"]["details"] = stdout
                if stderr:
                    logger.warning("Required_restart command stderr: %s", stderr)
            else:
                if os.path.exists("/var/run/reboot-required"):
                    self.value["needs_restart"] = "ON"
                    if os.path.exists("/var/run/reboot-required.pkgs"):
                        with open("/var/run/reboot-required.pkgs", "r") as f:
                            self.value["attributes"]["details"] = f.read().strip()
        return self.value
