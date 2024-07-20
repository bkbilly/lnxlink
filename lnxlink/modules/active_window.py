"""Gets the active window"""
from lnxlink.modules.scripts.helpers import import_install_package


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Active Window"
        self.lnxlink = lnxlink
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
        if self.lnxlink.display is None:
            return ""
        display = self.lib["xlib"].display.Display(self.lnxlink.display)
        ewmh = self.lib["ewmh"].EWMH(_display=display)
        win = ewmh.getActiveWindow()
        window_name = ewmh.getWmName(win)
        if window_name is None:
            return None
        return window_name.decode()
