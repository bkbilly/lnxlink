"""Monitor user inactivity duration"""
import logging
import threading

from lnxlink.modules.scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Idle"
        self.lnxlink = lnxlink
        self.idle_sec = None
        self._requirements()
        if self.lib["dbus_idle"] is None:
            raise SystemError("Python package 'dbus_idle' can't be installed")
        self.idle_monitor = self.lib["dbus_idle"].IdleMonitor()
        self.lnxlink.add_settings(
            "idle",
            {
                "inactive_time": 10,
                "wait_inactive": 0.6,
                "wait_active": 3,
            },
        )

        self.stop_event = threading.Event()
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _requirements(self):
        self.lib = {
            "dbus_idle": import_install_package("dbus-idle", ">=2026.9.0", "dbus_idle"),
        }

    def _monitor_loop(self):
        """Background thread loop to check idle time dynamically."""
        while not self.stop_event.is_set():
            try:
                idle_ms = self.idle_monitor.get_dbus_idle()
                if idle_ms is not None:
                    self.idle_sec = round(idle_ms / 1000, 0)
            except Exception as e:
                logger.error("Error reading DBus idle time: %s", e)
                self.idle_sec = None

            self.lnxlink.run_module(self.name, self.idle_sec)
            inactive_sec = self.lnxlink.config["settings"]["idle"]["inactive_time"]
            if self.idle_sec is not None and self.idle_sec >= inactive_sec:
                sleep_time = self.lnxlink.config["settings"]["idle"]["wait_inactive"]
            else:
                sleep_time = self.lnxlink.config["settings"]["idle"]["wait_active"]

            self.stop_event.wait(sleep_time)

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
