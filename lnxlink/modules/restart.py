"""Restarts the system"""
import logging
from shutil import which
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Restart"
        self.lnxlink = lnxlink

    def start_control(self, topic, data):
        """Control system"""
        self.lnxlink.temp_connection_callback(True)
        returncode = None
        if which("systemctl") is not None and returncode != 0:
            _, _, returncode = syscommand("systemctl reboot")
        if which("shutdown") is not None and returncode != 0:
            _, _, returncode = syscommand("shutdown -r now")
        if returncode != 0:
            try:
                conn = open_dbus_connection(bus="SYSTEM")
                conn.send(
                    new_method_call(
                        DBusAddress(
                            object_path="/org/freedesktop/login1",
                            bus_name="org.freedesktop.login1",
                            interface="org.freedesktop.login1.Manager",
                        ),
                        method="Reboot",
                        signature="b",
                        body=(True,),
                    )
                )
            except Exception:
                returncode = -1
        if returncode != 0:
            self.lnxlink.temp_connection_callback(False)

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Restart": {
                "type": "button",
                "icon": "mdi:restart",
            }
        }
