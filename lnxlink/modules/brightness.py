"""Controls the brightness of the displays"""
import re
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink=None):
        """Setup addon"""
        self.name = "Brightness"
        self.lnxlink = lnxlink
        if which("xrandr") is None:
            raise SystemError("System command 'xrandr' not found")
        self.displays = self._get_displays()

    def get_info(self):
        """Gather information from the system"""
        displays = self._get_displays()
        if displays != self.displays:
            self.displays = displays
            self.lnxlink.setup_discovery("brightness")
        values = [disp["brightness"] for disp in displays.values()]
        avg_brightness = sum(values) / max(1, len(values))
        avg_brightness = max(0.1, avg_brightness)

        info = {"status": avg_brightness}
        for display, values in displays.items():
            info[display] = max(0.1, values["brightness"])
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
        for display, values in self.displays.items():
            controls[f"Brightness {values['name']}"] = {
                "type": "number",
                "icon": "mdi:brightness-7",
                "min": 0.1,
                "max": 1,
                "step": 0.1,
                "value_template": f"{{{{ value_json.{display} }}}}",
                "enabled": False,
            }
        return controls

    def start_control(self, topic, data):
        """Control system"""
        disp_env_cmd = ""
        if self.lnxlink.display is not None:
            disp_env_cmd = f" --display {self.lnxlink.display}"

        if topic[1] == "brightness":
            for values in self.displays.values():
                syscommand(
                    f"xrandr --output {values['name']} --brightness {data} {disp_env_cmd}"
                )
        else:
            display = self.displays[
                topic[1].replace("brightness_", "").replace("-", "_")
            ]["name"]
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
            displays[match[0].replace("-", "_").lower()] = {
                "name": match[0],
                "brightness": float(match[1]),
            }

        return displays
