"""Gets the battery information of connected devices"""
from xml.etree import ElementTree
from lnxlink.modules.scripts.helpers import import_install_package


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Battery"
        self.lnxlink = lnxlink
        self._requirements()
        self.devices = self._get_devices()

    def _requirements(self):
        dasbus = import_install_package("dasbus", ">=1.7", "dasbus.connection")
        self.bus = dasbus.connection.SystemMessageBus()

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for device in self.devices:
            att_temp = f"{{{{ value_json.get('{device}', {{}}).get('attributes', {{}}) | tojson }}}}"
            discovery_info[f"Battery {device}"] = {
                "type": "sensor",
                "unit": "%",
                "device_class": "battery",
                "value_template": f"{{{{ value_json.get('{device}', {{}}).get('percent') }}}}",
                "attributes_template": att_temp,
                "enabled": True,
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        devices = self._get_devices()
        new_devices = set(devices) - set(self.devices)
        disconnected_devices = set(self.devices) - set(devices)
        for device_name in disconnected_devices:
            devices[device_name] = self.devices[device_name]
            self.devices[device_name]["percent"] = None
        self.devices = devices
        if len(new_devices) > 0:
            self.lnxlink.setup_discovery()

        return devices

    def _get_devices(self):
        devices = {}
        for device in self.get_batteries():
            native_path = device["NativePath"].split("/")[-1]
            name = (
                " ".join(
                    [
                        device["Vendor"],
                        device["Model"],
                        device["Serial"].replace(":", ""),
                    ]
                )
                .strip()
                .replace("'", "_")
            )
            if name == "":
                name = native_path
            if name != "":
                devices[name] = {
                    "percent": device["Percentage"],
                    "attributes": {
                        "vendor": device["Vendor"],
                        "model": device["Model"],
                        "serial": device["Serial"],
                        "native_path": native_path,
                        "rechargeable": device["IsRechargeable"],
                    },
                }
        return devices

    def dbus_paths(self, service, object_path, paths):
        """Recursive method to read the list of paths from the service"""
        obj = self.bus.get_proxy(
            service, object_path, "org.freedesktop.DBus.Introspectable"
        )
        xml_string = obj.Introspect()
        for child in ElementTree.fromstring(xml_string):
            if child.tag == "node":
                if object_path == "/":
                    object_path = ""
                new_path = "/".join((object_path, child.attrib["name"]))
                paths.append(new_path)
                self.dbus_paths(service, new_path, paths)
        return paths

    def get_batteries(self):
        """Gets a list of all devices and their status"""
        batteries = []
        for dbus_path in self.dbus_paths(
            "org.freedesktop.UPower", "/org/freedesktop/UPower", []
        ):
            proxy = self.bus.get_proxy(
                service_name="org.freedesktop.UPower",
                object_path=dbus_path,
                interface_name="org.freedesktop.UPower.Device",
            )
            # pylint: disable=protected-access
            if (
                "org.freedesktop.UPower.Device"
                in proxy._handler.specification.interfaces
            ):
                if proxy.Model + proxy.NativePath != "":
                    batteries.append(
                        {
                            "Model": proxy.Model,
                            "NativePath": proxy.NativePath,
                            "Percentage": proxy.Percentage,
                            "Serial": proxy.Serial,
                            "IconName": proxy.IconName,
                            "IsRechargeable": proxy.IsRechargeable,
                            "Vendor": proxy.Vendor,
                        }
                    )
        return batteries
