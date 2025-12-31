"""Monitor the name and title of the currently focused window"""

import os
import json
import logging
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection
from lnxlink.modules.scripts.helpers import import_install_package, get_display_variable

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Active Window"
        display_variable = get_display_variable()
        session_type = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
        desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "unknown").lower()

        if session_type == "x11":
            self._requirements()
            if display_variable is None:
                raise SystemError("Display variable not found for X11")
            display = self.lib["xlib"].display.Display(display_variable)
            self.ewmh = self.lib["ewmh"].EWMH(_display=display)
            self.get_window = self._get_x11_window

        elif session_type == "wayland" and "gnome" in desktop_env:
            self.bus = open_dbus_connection(bus="SESSION")
            self.wqt_addr = DBusAddress(
                bus_name="org.gnome.Shell",
                object_path="/org/gnome/Shell/Extensions/WindowQueryTool",
                interface="org.gnome.Shell.Extensions.WindowQueryTool",
            )
            # Verify that the extension is available
            try:
                msg = new_method_call(self.wqt_addr, "GetWindowInfo")
                reply = self.bus.send_and_get_reply(msg, timeout=2.0)
                if not reply or not reply.body:
                    raise SystemError("Received empty response from WindowQueryTool")
                data = json.loads(reply.body[0])
                if "focused_window_title" not in data:
                    raise SystemError("WindowQueryTool returned unexpected data format")
            except SystemError as err:
                raise SystemError(
                    "Wayland extension 'WindowQueryTool' not found. "
                    "Please install: https://extensions.gnome.org/extension/8763/window-query-tool"
                ) from err

            self.get_window = self._get_wayland_gnome

        else:
            raise SystemError(f"Session type '{session_type}' not supported")

    def _requirements(self):
        self.lib = {
            "ewmh": import_install_package("ewmh", ">=0.1.6"),
            "xlib": import_install_package("python-xlib", ">=0.33", "Xlib.display"),
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "Active Window": {
                "type": "sensor",
                "icon": "mdi:book-open-page-variant",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        return self.get_window()

    def _get_x11_window(self):
        try:
            win = self.ewmh.getActiveWindow()
            if win:
                window_name = self.ewmh.getWmName(win)
                if window_name:
                    return window_name.decode()
        except Exception as err:
            logger.debug("Error getting X11 window: %s", err)
        return None

    def _get_wayland_gnome(self):
        try:
            msg = new_method_call(self.wqt_addr, "GetWindowInfo")
            reply = self.bus.send_and_get_reply(msg, timeout=2.0)
            if reply and reply.body:
                json_str = reply.body[0]
                data = json.loads(json_str)
                return data.get("focused_window_title")
        except Exception as err:
            logger.debug("Error getting Wayland window: %s", err)
        return None
