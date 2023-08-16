"""Checks if a window is in fullscreen"""
from ewmh import EWMH


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Fullscreen"

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
        ewmh = EWMH()
        windows = ewmh.getClientList()
        for win in windows:
            state = ewmh.getWmState(win, True)
            name = ewmh.getWmName(win)
            if "_NET_WM_STATE_FULLSCREEN" in state:
                data["is_fullscreen"] = "ON"
                data["window"] = name.decode()

        return data
