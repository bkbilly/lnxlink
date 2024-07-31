"""Restarts the system"""
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Restart"
        self.lnxlink = lnxlink
        if which("systemctl") is None and which("shutdown") is None:
            self.dbus = import_install_package("dasbus", ">=1.7", "dasbus.connection")

    def start_control(self, topic, data):
        """Control system"""
        self.lnxlink.temp_connection_callback(True)
        if which("systemctl") is not None:
            syscommand("systemctl reboot")
        elif which("shutdown") is not None:
            syscommand("shutdown -r now")
        else:
            bus = self.dbus.connection.SystemMessageBus()
            proxy = bus.get_proxy(
                service_name="org.freedesktop.login1",
                object_path="/org/freedesktop/login1",
            )
            proxy.Reboot(True)

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Restart": {
                "type": "button",
                "icon": "mdi:restart",
            }
        }
