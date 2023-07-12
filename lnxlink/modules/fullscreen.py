from ewmh import EWMH


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Fullscreen'

    def exposedControls(self):
        return {
            "Fullscreen": {
                "type": "binary_sensor",
                "icon": "mdi:alert-octagon-outline",
                "value_template": "{{ value_json.is_fullscreen }}",
            },
        }

    def getControlInfo(self):
        data = {
            "is_fullscreen": "OFF",
            "window": "",
        }
        ewmh = EWMH()
        wins = ewmh.getClientList()
        for w in wins:
            state = ewmh.getWmState(w, True)
            name = ewmh.getWmName(w)
            if "_NET_WM_STATE_FULLSCREEN" in state:
                data["is_fullscreen"] = "ON"
                data["window"] = name.decode()

        return data
