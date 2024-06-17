"""Run a terminal command"""
import logging
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


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
            elif discovery.get("type") == "binary_sensor":
                stdout, _, returncode = syscommand(discovery["local_command"])
                status = stdout.lower() not in ["false", "no", "0", ""]
                senddata = {
                    "status": "ON" if status else "OFF",
                    "attributes": {"raw": stdout.split("\n")},
                }
                self.lnxlink.run_module(f"{self.name}/{expose_name}", senddata)

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
            elif expose_type == "binary_sensor":
                self.discovery_info[expose_name] = {
                    "type": expose_type,
                    "icon": icon,
                    "value_template": "{{ value_json.status }}",
                    "attributes_template": "{{ value_json.attributes | tojson }}",
                    "local_command": expose.get("command"),
                    "subtopic": True,
                }
            if expose.get("entity_category") in ["diagnostic", "config"]:
                self.discovery_info[expose_name]["entity_category"] = expose[
                    "entity_category"
                ]

        return self.discovery_info

    def start_control(self, topic, data):
        """Control system"""
        allow_any_command = self.lnxlink.config["settings"]["bash"]["allow_any_command"]
        if allow_any_command:
            stdout, _, _ = syscommand(data, timeout=120)
            return stdout
        exposed = self.lnxlink.config["settings"]["bash"]["expose"]
        exposed = [] if exposed is None else exposed
        for expose in exposed:
            if data.strip() == expose.get("command", "").strip():
                stdout, _, _ = syscommand(data, timeout=120)
                return stdout
        logger.error(
            "Check bash configuration option allow_any_command to run this command: %s",
            data,
        )
        return None
