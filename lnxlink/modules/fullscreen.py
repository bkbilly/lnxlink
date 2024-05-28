"""Checks if a window is in fullscreen"""
from lnxlink.modules.scripts.helpers import import_install_package


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Fullscreen"
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
            "Fullscreen": {
                "type": "binary_sensor",
                "icon": "mdi:alert-octagon-outline",
                "value_template": "{{ value_json.is_fullscreen }}",
            },
        }

    def get_info(self):
        """Gather information from the system"""
        data = {
            "is_fullscreen": "OFF",
            "window": "",
        }
        if self.lnxlink.display is None:
            return data
        display = self.lib["xlib"].display.Display(self.lnxlink.display)
        ewmh = self.lib["ewmh"].EWMH(_display=display)
        windows = ewmh.getClientList()
        for win in windows:
            state = ewmh.getWmState(win, True)
            name = ewmh.getWmName(win)
            if "_NET_WM_STATE_FULLSCREEN" in state:
                data["is_fullscreen"] = "ON"
                data["window"] = name.decode()

        return data
