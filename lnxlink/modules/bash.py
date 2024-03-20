"""Run a terminal command"""
from .scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "bash"
        self.lnxlink = lnxlink

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {
            "Bash_Command": {
                "type": "text",
                "icon": "mdi:bash",
            }
        }
        exposed = self.lnxlink.config["settings"]["bash"]["expose"]
        exposed = [] if exposed is None else exposed
        for expose in exposed:
            discovery_info[f"Bash {expose['name']}"] = {
                "type": "button",
                "icon": expose.get("icon", "mdi:script-text"),
                "payload_press": expose["command"],
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        stdout, _, _ = syscommand(data, timeout=120)
        return stdout
