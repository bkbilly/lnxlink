"""Reboot the system"""
import logging
from shutil import which
import jeepney
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
        try:
            with open_dbus_connection(bus="SYSTEM") as conn:
                msg = new_method_call(
                    DBusAddress(
                        object_path="/org/freedesktop/login1",
                        bus_name="org.freedesktop.login1",
                        interface="org.freedesktop.login1.Manager",
                    ),
                    method="Reboot",
                    signature="b",
                    body=(True,),
                )
                reply = conn.send_and_get_reply(msg, timeout=2.0)
                if (
                    getattr(reply.header, "message_type", None)
                    and reply.header.message_type.name == "ERROR"
                ):
                    error_name = reply.header.fields.get(
                        jeepney.HeaderFields.error_name, "Unknown"
                    )
                    logger.error("DBus Reboot failed: %s", error_name)
                    returncode = -1
                else:
                    logger.info("DBus Reboot succeeded")
                    returncode = 0
        except Exception as err:
            logger.error("DBus Reboot call failed: %s", err)
            returncode = -1

        if which("systemctl") is not None and returncode != 0:
            _, _, returncode = syscommand("systemctl reboot --ignore-inhibitors")
        if which("shutdown") is not None and returncode != 0:
            _, _, returncode = syscommand("shutdown -r now")
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
