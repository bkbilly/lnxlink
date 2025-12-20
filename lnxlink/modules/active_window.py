"""Gets the active window"""
# Wayland requires either of the extensions
# - [flexagoon/focused-window-dbus](https://github.com/flexagoon/focused-window-dbus)
# - [bkbilly/GnomeShell-WindowQueryTool](https://github.com/bkbilly/GnomeShell-WindowQueryTool)
import os
import subprocess
import json
import logging
from lnxlink.modules.scripts.helpers import import_install_package, get_display_variable


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Active Window"
        self._requirements()

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
        display_variable = get_display_variable()
        # Detect session type
        session_type = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()

        logger = logging.getLogger("lnxlink")
        logger.debug("Session type: %s", session_type)

        if "x11" == session_type:
            # X11
            if display_variable is None:
                return ""
            display = self.lib["xlib"].display.Display(display_variable)
            ewmh = self.lib["ewmh"].EWMH(_display=display)
            win = ewmh.getActiveWindow()
            window_name = ewmh.getWmName(win)

            if window_name is None:
                return None
            return window_name.decode()

        if "wayland" == session_type:
            window_name = None

            # Wayland: GNOME WindowQueryTool extension
            try:
                method = "org.gnome.Shell.Extensions.WindowQueryTool.GetWindowInfo"
                result = subprocess.run(
                    [
                        "gdbus",
                        "call",
                        "--session",
                        "--dest",
                        "org.gnome.Shell",
                        "--object-path",
                        "/org/gnome/Shell/Extensions/WindowQueryTool",
                        "--method",
                        method,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=True,
                )

                if result.returncode == 0 and result.stdout.strip():
                    json_str = result.stdout.strip("()',\n")
                    data = json.loads(json_str)
                    window_name = data.get("focused_window_title", None)
                    return window_name
                logger.debug("Method not found: %s", method)
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                pass

            # Wayland: GNOME FocusedWindow extension
            try:
                method = "org.gnome.shell.extensions.FocusedWindow.Get"
                result = subprocess.run(
                    [
                        "gdbus",
                        "call",
                        "--session",
                        "--dest",
                        "org.gnome.Shell",
                        "--object-path",
                        "/org/gnome/shell/extensions/FocusedWindow",
                        "--method",
                        method,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=True,
                )

                if result.returncode == 0 and result.stdout.strip():
                    json_str = result.stdout.strip("()',\n")
                    data = json.loads(json_str)
                    window_name = data.get("title", None)
                    return window_name
                logger.debug("Method not found: %s", method)
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                pass

        return None
