"""Turns on or off the screen"""
import re
import os
import logging
from shutil import which
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection
from lnxlink.modules.scripts.helpers import syscommand, get_display_variable

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Screen OnOff"
        self.display_variable = get_display_variable()
        session_type = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
        desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "unknown").lower()

        if session_type == "x11":
            if which("xset") is None:
                raise SystemError("System command 'xset' not found")
            self.control_screen = self._control_x11
            self.get_screen_status = self._get_x11_status
        elif session_type == "wayland" and "gnome" in desktop_env:
            self.bus = open_dbus_connection(bus="SESSION")
            self.ss_addr = DBusAddress(
                bus_name="org.gnome.ScreenSaver",
                object_path="/org/gnome/ScreenSaver",
                interface="org.gnome.ScreenSaver",
            )
            self.control_screen = self._control_wayland_gnome
            self.get_screen_status = self._get_wayland_gnome_status
        else:
            raise SystemError(f"Session type '{session_type}' not supported")

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Screen OnOff": {
                "type": "switch",
                "icon": "mdi:monitor",
            }
        }

    def get_info(self):
        """Gather information from the system"""
        return self.get_screen_status()

    def start_control(self, topic, data):
        """Control system"""
        command = data.lower()
        if command not in {"on", "off"}:
            logger.error("Expected `on` or `off`, received: `%s`", command)
            return
        self.control_screen(command)

    def _get_x11_status(self):
        status = "ON"
        if self.display_variable is not None:
            command = f"xset -display {self.display_variable} q"
            stdout, _, _ = syscommand(command)
            match = re.findall(r"Monitor is (\w*)", stdout)
            if match:
                status = match[0].upper()
        return status

    def _control_x11(self, command):
        maybe_display = (
            f"-display {self.display_variable}" if self.display_variable else ""
        )
        syscommand(f"xset {maybe_display} dpms force {command}")

    def _get_wayland_gnome_status(self):
        """Checks if the screen is active (on) or locked/blanked (off)"""
        try:
            msg = new_method_call(self.ss_addr, "GetActive")
            reply = self.bus.send_and_get_reply(msg, timeout=2.0)
            # GetActive returns True if the screensaver is active (Screen is OFF)
            return "OFF" if reply.body[0] else "ON"
        except Exception as err:
            logger.error("Error getting Wayland status: %s", err)
            return "ON"

    def _control_wayland_gnome(self, command):
        """Uses D-Bus to set the ScreenSaver state"""
        # SetActive(True) blanks the screen (OFF), SetActive(False) wakes it (ON)
        active_state = command == "off"
        try:
            msg = new_method_call(self.ss_addr, "SetActive", "b", (active_state,))
            self.bus.send_message(msg)
        except Exception as err:
            logger.error("Error controlling Wayland screen: %s", err)
