"""Controls systemd services"""
import logging
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "SystemD"
        self.lnxlink = lnxlink
        self.services = self.lnxlink.config["settings"].get("systemd", [])
        self.services = [] if self.services is None else self.services
        if not self.services:
            logger.info("No systemd settings found on configuration.")
        self.bus = open_dbus_connection(bus="SYSTEM")

    def get_info(self):
        """Gather information from the system"""
        info = {}
        for service in self.services:
            try:
                # Construct a message to get the 'ActiveState' property
                dbus_service = (
                    service.replace("-", "_2d")
                    .replace(".", "_2e")
                    .replace("\\", "_5c")
                    .replace("@", "_40")
                )

                msg = new_method_call(
                    DBusAddress(
                        object_path=f"/org/freedesktop/systemd1/unit/{dbus_service}",
                        bus_name="org.freedesktop.systemd1",
                        interface="org.freedesktop.DBus.Properties",
                    ),
                    "Get",
                    "ss",
                    ("org.freedesktop.systemd1.Unit", "ActiveState"),
                )

                # Send the message and get the reply
                reply = self.bus.send_and_get_reply(msg)

                # The actual state is wrapped in a variant 'v'
                state = reply.body[0][1]
                status = "ON" if state == "active" else "OFF"
            except Exception as e:
                logger.error("Error getting status for %s: %s", service, e)
                status = "OFF"

            name = service.replace(".service", "")
            info[name] = status
        return info

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for service in self.services:
            name = service.replace(".service", "")
            discovery_info[f"Systemd {name}"] = {
                "type": "switch",
                "icon": "mdi:application-cog",
                "value_template": f"{{{{ value_json.get('{name}') }}}}",
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        service_name = topic[1].replace("systemd_", "") + ".service"
        action = "StartUnit" if data.lower() == "on" else "StopUnit"

        try:
            # Create a new method call message
            msg = new_method_call(
                DBusAddress(
                    object_path="/org/freedesktop/systemd1",
                    bus_name="org.freedesktop.systemd1",
                    interface="org.freedesktop.systemd1.Manager",
                ),
                action,
                "ss",  # signature for two strings
                (service_name, "replace"),
            )
            # Send the message
            self.bus.send(msg)
        except Exception as err:
            logger.error("Error %sing %s: %s", action, service_name, err)
            fallback_command = "start" if data.lower() == "on" else "stop"
            syscommand(f"sudo -n systemctl {fallback_command} {service_name} &")

    def __del__(self):
        """Close the connection"""
        if hasattr(self, "bus"):
            self.bus.close()
