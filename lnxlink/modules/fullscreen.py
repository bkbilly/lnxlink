"""Detect if a window is currently in fullscreen mode and view its name"""

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
        self.name = "Fullscreen"
        display_variable = get_display_variable()
        session_type = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
        desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "unknown").lower()

        if session_type == "x11":
            self._requirements()
            if display_variable is None:
                raise SystemError("Display variable not found for X11")
            display = self.lib["xlib"].display.Display(display_variable)
            self.ewmh = self.lib["ewmh"].EWMH(_display=display)
            self.get_fullscreen_info = self._get_x11_info

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
                if "is_any_window_fullscreen" not in data:
                    raise SystemError("WindowQueryTool returned unexpected data format")
            except SystemError as err:
                raise SystemError(
                    "Wayland extension 'WindowQueryTool' not found. "
                    "Please install: https://extensions.gnome.org/extension/8763/window-query-tool"
                ) from err

            self.get_fullscreen_info = self._get_wayland_gnome

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
            "Fullscreen": {
                "type": "binary_sensor",
                "icon": "mdi:alert-octagon-outline",
                "value_template": "{{ value_json.is_fullscreen }}",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        return self.get_fullscreen_info()

    def _get_x11_info(self):
        data = {
            "is_fullscreen": "OFF",
            "window": "",
        }
        try:
            windows = self.ewmh.getClientList()
            for win in windows:
                state = self.ewmh.getWmState(win, True)
                if "_NET_WM_STATE_FULLSCREEN" in state:
                    name = self.ewmh.getWmName(win)
                    data["is_fullscreen"] = "ON"
                    data["window"] = name.decode() if name else ""
                    break
        except SystemError as err:
            logger.debug("Error getting X11 fullscreen info: %s", err)

        return data

    def _get_wayland_gnome(self):
        data = {
            "is_fullscreen": "OFF",
            "window": "",
        }
        try:
            msg = new_method_call(self.wqt_addr, "GetWindowInfo")
            reply = self.bus.send_and_get_reply(msg, timeout=2.0)
            if reply and reply.body:
                json_str = reply.body[0]
                if "Object does not exist" in str(reply.body[0]):
                    logger.debug(
                        "WindowQueryTool D-Bus path not found. Is the extension enabled?"
                    )
                    return data
                info = json.loads(json_str)

                is_fullscreen = info.get("is_any_window_fullscreen", False)
                if is_fullscreen:
                    data["is_fullscreen"] = "ON"
                    data["window"] = info.get("fullscreen_window_title", "")
        except SystemError as err:
            logger.debug("Error getting Wayland fullscreen info: %s", err)

        return data
