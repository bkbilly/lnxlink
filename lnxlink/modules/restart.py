"""Reboot the system"""
import logging
from shutil import which
from jeepney import DBusAddress, new_method_call, HeaderFields, MessageType
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
                if getattr(reply.header, "message_type", None) == MessageType.error:
                    error_name = reply.header.fields.get(
                        HeaderFields.error_name, "Unknown"
                    )
                    error_reason = reply.body[0] if reply.body else "No reason given"
                    logger.error(
                        "DBus Reboot failed: %s (%s)", error_name, error_reason
                    )
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
