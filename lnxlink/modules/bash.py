"""Run a terminal command"""
from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "bash"
        self.lnxlink = lnxlink
        self.discovery_info = {}

    def get_info(self):
        """Gather information from the system"""
        for expose_name, discovery in self.discovery_info.items():
            if discovery.get("type") == "sensor":
                stdout, _, returncode = syscommand(discovery["local_command"])
                if returncode == 0:
                    self.lnxlink.run_module(f"{self.name}/{expose_name}", stdout)

    def exposed_controls(self):
        """Exposes to home assistant"""
        self.discovery_info = {
            "Bash Command": {
                "type": "text",
                "icon": "mdi:bash",
            }
        }
        exposed = self.lnxlink.config["settings"]["bash"]["expose"]
        exposed = [] if exposed is None else exposed
        for expose in exposed:
            expose_type = expose.get("type", "button")
            expose_name = f"Bash {expose['name']}"
            icon = expose.get("icon", "mdi:script-text")
            if expose_type == "button":
                self.discovery_info[expose_name] = {
                    "type": expose_type,
                    "icon": icon,
                    "payload_press": expose["command"],
                }
            elif expose_type == "sensor":
                self.discovery_info[expose_name] = {
                    "type": expose_type,
                    "icon": icon,
                    "unit": expose.get("unit"),
                    "local_command": expose.get("command"),
                    "subtopic": True,
                }
        return self.discovery_info

    def start_control(self, topic, data):
        """Control system"""
        stdout, _, _ = syscommand(data, timeout=120)
        return stdout
