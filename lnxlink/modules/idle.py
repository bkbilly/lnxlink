"""Gets the idle time of the system"""
import logging
from dbus_idle import IdleMonitor

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Idle"

    def get_info(self):
        """Gather information from the system"""
        monitor = IdleMonitor.get_monitor()
        idle_ms = monitor.get_dbus_idle()
        try:
            idle_sec = round(idle_ms / 1000, 0)
        except Exception as err:
            logging.debug(err)
            return 0
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
