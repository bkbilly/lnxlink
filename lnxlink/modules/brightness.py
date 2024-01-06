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
        self.displays = self._get_displays()

    def get_info(self):
        """Gather information from the system"""
        displays = self._get_displays()
        if displays != self.displays:
            self.displays = displays
            self.lnxlink.setup_discovery()
        avg_brightness = sum(displays.values()) / max(1, len(displays.values()))
        avg_brightness = max(0.1, avg_brightness)

        info = {"status": avg_brightness}
        for display, brightness in displays.items():
            display = display.replace("-", "_")
            info[display] = max(0.1, brightness)
        return info

    def exposed_controls(self):
        """Exposes to home assistant"""
        controls = {}
        if len(self.displays) > 0:
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
            for display in self.displays:
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
        disp_env_cmd = ""
        if self.lnxlink.display is not None:
            disp_env_cmd = f" --display {self.lnxlink.display}"

        if topic[1] == "brightness":
            for display in self.displays:
                syscommand(
                    f"xrandr --output {display} --brightness {data} {disp_env_cmd}"
                )
        else:
            display = topic[1].replace("brightness_", "").upper()
            syscommand(f"xrandr --output {display} --brightness {data} {disp_env_cmd}")

    def _get_displays(self):
        """Get all the displays"""
        displays = {}
        disp_env_cmd = ""
        if self.lnxlink.display is not None:
            disp_env_cmd = f" --display {self.lnxlink.display}"

        stdout, _, _ = syscommand(
            f"xrandr --verbose --current {disp_env_cmd}",
        )
        pattern = re.compile(
            r"(\S+) \bconnected\b.*[\s\S]*?(?=Brightness)Brightness: ([\d\.\d]+)"
        )

        for match in pattern.findall(stdout):
            displays[match[0]] = float(match[1])

        return displays
