"""Toggle between performance, balanced, or power-saver profiles"""
import logging
import re
from shutil import which

from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection

from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink=None):
        """Setup addon"""
        self.name = "Power Profile"
        self.lnxlink = lnxlink
        self.use_dbus = False
        self.conn = None

        try:
            profiles_data = self._dbus("Profiles")
            self.options = [p["Profile"][1] for p in profiles_data if "Profile" in p]
            self.use_dbus = True
        except Exception as err:
            if which("powerprofilesctl") is None:
                raise SystemError(
                    "Power profiles service or 'powerprofilesctl' not found"
                ) from err
            self.options = self._get_power_profiles_cli()

    def get_info(self):
        """Gather information from the system"""
        if self.use_dbus:
            return self._dbus("ActiveProfile")
        stdout, _, _ = syscommand(["powerprofilesctl", "get"])
        return stdout

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        if len(self.options) > 0:
            discovery_info = {
                "Power Profile": {
                    "type": "select",
                    "icon": "mdi:leaf",
                    "options": self.options,
                }
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        if data in self.options:
            if self.use_dbus:
                self._dbus("ActiveProfile", data)
            else:
                syscommand(["powerprofilesctl", "set", str(data)])
        else:
            logger.error(
                "Invalid power profile '%s'. Allowed options: %s",
                data,
                self.options,
            )

    def _get_power_profiles_cli(self):
        """Get the power profiles in the correct order via CLI"""
        profiles_pattern = re.compile(r"([\w-]+):\n")
        stdout, _, _ = syscommand(["powerprofilesctl", "list"])
        return re.findall(profiles_pattern, stdout)

    def _dbus(self, prop="ActiveProfile", value=None):
        """Interact with PowerProfiles D-Bus service"""
        if self.conn is None:
            self.conn = open_dbus_connection(bus="SYSTEM")

        addr = DBusAddress(
            "/net/hadess/PowerProfiles",
            bus_name="net.hadess.PowerProfiles",
            interface="org.freedesktop.DBus.Properties",
        )
        if value is None:
            msg = new_method_call(
                addr,
                "Get",
                "ss",
                ("net.hadess.PowerProfiles", prop),
            )
            reply = self.conn.send_and_get_reply(msg)
            return reply.body[0][1]

        msg = new_method_call(
            addr,
            "Set",
            "ssv",
            ("net.hadess.PowerProfiles", prop, ("s", str(value))),
        )
        self.conn.send_and_get_reply(msg)
        return None
