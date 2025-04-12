"""Shutdown the system"""
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Shutdown"
        self.lnxlink = lnxlink
        if which("systemctl") is None and which("shutdown") is None:
            self.jeepney = import_install_package(
                "jeepney",
                ">=0.9.0",
                (
                    "jeepney",
                    [
                        "DBusAddress",
                        "new_method_call",
                        "io.blocking.open_dbus_connection",
                    ],
                ),
            )

    def start_control(self, topic, data):
        """Control system"""
        self.lnxlink.temp_connection_callback(True)
        returncode = None
        if which("systemctl") is not None and returncode != 0:
            _, _, returncode = syscommand("systemctl poweroff")
        if which("shutdown") is not None and returncode != 0:
            _, _, returncode = syscommand("shutdown now")
        if returncode != 0:
            try:
                conn = self.jeepney.io.blocking.open_dbus_connection(bus="SYSTEM")
                conn.send(
                    self.jeepney.new_method_call(
                        self.jeepney.DBusAddress(
                            object_path="/org/freedesktop/login1",
                            bus_name="org.freedesktop.login1",
                            interface="org.freedesktop.login1.Manager",
                        ),
                        method="PowerOff",
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
            "Shutdown": {
                "type": "button",
                "icon": "mdi:power",
            }
        }
