import subprocess
import re


class Addon():

    def __init__(self, lnxlink=None):
        self.name = 'Brightness'

    def getControlInfo(self):
        displays = self._get_displays()
        avg_brightness = sum(displays.values()) / len(displays.values())

        info = {"status": avg_brightness}
        for display, brightness in displays.items():
            display = display.replace("-", "_")
            info[display] = brightness
        return info

    def exposedControls(self):
        controls = {
            "Brightness": {
                "type": "number",
                "icon": "mdi:brightness-7",
                "min": 0.1,
                "max": 1,
                "step": 0.1,
                "value_template": "{{ value_json.status }}",
            }
        }
        try:
            for display in self._get_displays().keys():
                json_display = display.replace("-", "_")
                controls[f"Brightness {display}"] = {
                    "type": "number",
                    "icon": "mdi:brightness-7",
                    "min": 0.1,
                    "max": 1,
                    "step": 0.1,
                    "value_template": "{{ value_json." + json_display + " }}",
                    "enabled": False,
                }
        except Exception as e:
            print(e)
        return controls

    def startControl(self, topic, data):
        if topic[1] == 'Brightness':
            for display in self._get_displays().keys():
                subprocess.call(f"xrandr --output {display} --brightness {data}", shell=True)
        else:
            display = topic[1].replace('Brightness_', '')
            subprocess.call(f"xrandr --output {display} --brightness {data}", shell=True)

    def _get_displays(self):
        stdout = subprocess.run(
            'xrandr --verbose --current',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        pattern = re.compile(r"(\S+) \bconnected\b.*[\s\S]*?(?=Brightness)Brightness: ([\d\.\d]+)")

        displays = {}
        for match in pattern.findall(stdout):
            displays[match[0]] = float(match[1])

        return displays
