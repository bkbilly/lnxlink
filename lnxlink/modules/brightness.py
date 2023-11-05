"""Controls the brightness of the displays"""
import re
import logging
from .scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink=None):
        """Setup addon"""
        self.name = "Brightness"
        self.lnxlink = lnxlink

    def get_info(self):
        """Gather information from the system"""
        displays = self._get_displays()
        avg_brightness = sum(displays.values()) / max(1, len(displays.values()))

        info = {"status": avg_brightness}
        for display, brightness in displays.items():
            display = display.replace("-", "_")
            info[display] = brightness
        return info

    def exposed_controls(self):
        """Exposes to home assistant"""
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
            for display in self._get_displays():
                json_display = display.replace("-", "_")
                controls[f"Brightness {display}"] = {
                    "type": "number",
                    "icon": "mdi:brightness-7",
                    "min": 0.1,
                    "max": 1,
                    "step": 0.1,
                    "value_template": f"{{{{ value_json.{json_display} }}}}",
                    "enabled": False,
                }
        except Exception as err:
            logger.error(err)
        return controls

    def start_control(self, topic, data):
        """Control system"""
        if topic[1] == "Brightness":
            for display in self._get_displays():
                syscommand(f"xrandr --output {display} --brightness {data}")
        else:
            display = topic[1].replace("Brightness_", "")
            syscommand(f"xrandr --output {display} --brightness {data}")

    def _get_displays(self):
        """Get all the displays"""
        stdout, _, _ = syscommand(
            "xrandr --verbose --current",
        )
        pattern = re.compile(
            r"(\S+) \bconnected\b.*[\s\S]*?(?=Brightness)Brightness: ([\d\.\d]+)"
        )

        displays = {}
        for match in pattern.findall(stdout):
            displays[match[0]] = float(match[1])

        return displays
