"""Controls systemd services"""
import logging
from lnxlink.modules.scripts.helpers import syscommand, import_install_package

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
        self._requirements()

    def _requirements(self):
        dasbus = import_install_package("dasbus", ">=1.7", "dasbus.connection")
        self.bus = dasbus.connection.SystemMessageBus()

    def get_info(self):
        """Gather information from the system"""
        info = {}
        for service in self.services:
            dbus_service = (
                service.replace("-", "_2d")
                .replace(".", "_2e")
                .replace("\\", "_5c")
                .replace("@", "_40")
            )
            proxy = self.bus.get_proxy(
                service_name="org.freedesktop.systemd1",
                object_path=f"/org/freedesktop/systemd1/unit/{dbus_service}",
                interface_name="org.freedesktop.systemd1.Unit",
            )
            status = "OFF"
            if proxy.ActiveState == "active":
                status = "ON"
            name = service.replace(".service", "")
            info[name] = status
        return info

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for service in self.services:
            name = service.replace(".service", "")
            discovery_info[f"Systemd {name}"] = {
                "type": "switch",
                "icon": "mdi:application-cog",
                "value_template": f"{{{{ value_json.get('{name}') }}}}",
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        service = topic[1].replace("systemd_", "") + ".service"
        dbus_service = (
            service.replace("-", "_2d")
            .replace(".", "_2e")
            .replace("\\", "_5c")
            .replace("@", "_40")
        )
        proxy = self.bus.get_proxy(
            service_name="org.freedesktop.systemd1",
            object_path=f"/org/freedesktop/systemd1/unit/{dbus_service}",
            interface_name="org.freedesktop.systemd1.Unit",
        )
        if data.lower() == "off":
            try:
                proxy.Stop("replace")
            except Exception:
                syscommand(f"sudo -n systemctl stop {service} &")
        elif data.lower() == "on":
            try:
                proxy.Start("replace")
            except Exception:
                syscommand(f"sudo -n systemctl start {service} &")
