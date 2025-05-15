"""Gets the idle time of the system"""
import logging
from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Idle"
        self._requirements()
        if self.lib["dbus_idle"] is None:
            raise SystemError("Python package 'dbus_idle' can't be installed")
        self.idle_monitor = self.lib["dbus_idle"].IdleMonitor()

    def _requirements(self):
        self.lib = {
            "dbus_idle": import_install_package("dbus-idle", ">=2025.5.1", "dbus_idle"),
        }

    def get_info(self):
        """Gather information from the system"""
        idle_ms = self.idle_monitor.get_dbus_idle()
        if idle_ms is None:
            return None
        idle_sec = round(idle_ms / 1000, 0)
        return idle_sec

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Idle": {
                "type": "sensor",
                "icon": "mdi:timer-sand",
                "unit": "s",
                "state_class": "total_increasing",
                "device_class": "duration",
            },
        }
