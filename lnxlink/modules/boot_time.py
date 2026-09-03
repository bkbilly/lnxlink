"""Report system boot time"""
from datetime import datetime

import psutil


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Boot Time"
        self.lnxlink = lnxlink

    def get_info(self):
        """Gather information from the system"""
        boot_time = psutil.boot_time()
        return {
            "boot_time": datetime.fromtimestamp(boot_time).astimezone().isoformat(),
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Boot Time": {
                "type": "sensor",
                "icon": "mdi:clock-start",
                "device_class": "timestamp",
                "value_template": "{{ value_json.boot_time }}",
            },
        }
