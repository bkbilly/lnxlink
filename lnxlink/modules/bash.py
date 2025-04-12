"""Run a terminal command"""
import logging
import time
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
                cur_time = time.time()
                if cur_time - discovery["last_time"] > discovery["update_interval"]:
                    discovery["last_time"] = cur_time
                    stdout, _, returncode = syscommand(
                        discovery["local_command"],
                        timeout=discovery.get("sensor_timeout", 3),
                    )
                    if returncode == 0:
                        self.lnxlink.run_module(f"{self.name}/{expose_name}", stdout)
            elif discovery.get("type") == "binary_sensor":
                cur_time = time.time()
                if cur_time - discovery["last_time"] > discovery["update_interval"]:
                    discovery["last_time"] = cur_time
                    stdout, _, _ = syscommand(
                        discovery["local_command"],
                        timeout=discovery.get("sensor_timeout", 3),
                    )
                    status = stdout.lower() not in ["false", "no", "0", "off", ""]
                    senddata = {
                        "status": "ON" if status else "OFF",
                        "attributes": {"raw": stdout.split("\n")},
                    }
                    self.lnxlink.run_module(f"{self.name}/{expose_name}", senddata)
            elif discovery.get("type") == "switch":
                stdout, _, _ = syscommand(
                    discovery["local_command"],
                    ignore_errors=True,
                    timeout=discovery.get("sensor_timeout", 3),
                )
                status = stdout.lower() not in ["false", "no", "0", "off", ""]
                self.lnxlink.run_module(f"{self.name}/{expose_name}", status)

    def exposed_controls(self):
        """Exposes to home assistant"""
        self.discovery_info = {}
        if self.lnxlink.config["settings"]["bash"]["allow_any_command"]:
            self.discovery_info["Bash Command"] = {
                "type": "text",
                "icon": "mdi:bash",
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
                    "update_interval": expose.get("update_interval", 0),
                    "last_time": 0,
                    "sensor_timeout": expose.get("sensor_timeout", 3),
                }
            elif expose_type == "binary_sensor":
                self.discovery_info[expose_name] = {
                    "type": expose_type,
                    "icon": icon,
                    "value_template": "{{ value_json.status }}",
                    "attributes_template": "{{ value_json.attributes | tojson }}",
                    "local_command": expose.get("command"),
                    "subtopic": True,
                    "update_interval": expose.get("update_interval", 0),
                    "last_time": 0,
                    "sensor_timeout": expose.get("sensor_timeout", 3),
                }
            elif expose_type == "switch":
                self.discovery_info[expose_name] = {
                    "type": expose_type,
                    "icon": icon,
                    "local_command": expose.get("command"),
                    "command_on": expose.get("command_on"),
                    "command_off": expose.get("command_off"),
                    "subtopic": True,
                    "sensor_timeout": expose.get("sensor_timeout", 3),
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
            command_list = [
                expose.get("command", "").strip(),
                expose.get("command_on", "").strip(),
                expose.get("command_off", "").strip(),
            ]
            if data.strip() in command_list:
                stdout, _, _ = syscommand(
                    data,
                    timeout=expose.get("command_timeout", 120),
                )
                return stdout
        logger.error(
            "Check bash configuration option allow_any_command to run this command: %s",
            data,
        )
        return None
