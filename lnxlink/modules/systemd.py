"""Controls systemd services"""
import logging
from .scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "SystemD"
        self.lnxlink = lnxlink
        self.services = self.lnxlink.config["settings"].get("systemd", [])
        self.services = [] if self.services is None else self.services
        if len(self.services) == 0:
            logger.info("No systemd settings found on configuration.")

    def get_info(self):
        """Gather information from the system"""
        info = {}
        for service in self.services:
            stdout, _, _ = syscommand(
                f"systemctl show {service} --no-pager | grep ActiveState"
            )
            status = "OFF"
            if "=active" in stdout:
                status = "ON"
            name = service.replace(".service", "")
            info[name] = status
        return info

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for service in self.services:
            name = service.replace(".service", "")
            discovery_info[f"systemd_{name}"] = {
                "type": "switch",
                "icon": "mdi:application-cog",
                "value_template": f"{{{{ value_json.get('{name}') }}}}",
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        service = topic[1].replace("systemd_", "")
        if data.lower() == "off":
            syscommand(f"sudo systemctl stop {service}.service &")
        elif data.lower() == "on":
            syscommand(f"sudo systemctl start {service}.service &")
