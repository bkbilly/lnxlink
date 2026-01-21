"""Adjust display luminance for External and Laptop monitors"""
import logging
from lnxlink.modules.scripts.monitor_brightness import MonitorBrightness

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink=None):
        """Setup addon"""
        self.name = "Brightness"
        self.lnxlink = lnxlink
        self.monitors, issues = MonitorBrightness.list_displays()
        for issue in issues:
            logger.warning("Brightness Monitor Issue: %s", issue)
        self.lnxlink.add_settings("brightness", {"autodiscovery": False})

    def get_info(self):
        """Gather information from the system"""
        if self.lnxlink.config["settings"].get("brightness", {}).get("autodiscovery"):
            monitors, _ = MonitorBrightness.list_displays()
            if len(monitors) != len(self.monitors):
                print("Detected change in connected monitors, updating discovery.")
                self.monitors = monitors
                self.lnxlink.setup_discovery("brightness")

        info = {}
        for monitor in self.monitors:
            monitor.get_brightness()
            info[monitor.unique_name] = monitor.last_successful_read

        return info

    def exposed_controls(self):
        """Exposes to home assistant"""
        controls = {}
        for monitor in self.monitors:
            controls[f"Brightness {monitor.unique_name}"] = {
                "type": "number",
                "icon": "mdi:brightness-7",
                "min": 0,
                "max": 100,
                "step": 1,
                "value_template": f"{{{{ value_json.get('{monitor.unique_name}') }}}}",
            }
        return controls

    def start_control(self, topic, data):
        """Control system"""
        if topic[1] == "brightness":
            for monitor in self.monitors:
                monitor.set_brightness(int(data))
        else:
            for monitor in self.monitors:
                name_query = topic[1].replace("brightness_", "").replace("-", "_")
                monitor_unique_name = (
                    monitor.unique_name.lower().replace("-", "_").replace(" ", "_")
                )
                if monitor_unique_name == name_query:
                    logger.info(
                        "Changing Brightness to %d for %s",
                        int(data),
                        monitor.unique_name,
                    )
                    monitor.set_brightness(int(data))
                    break
