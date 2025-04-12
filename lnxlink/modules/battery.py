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
        self.jeepney = import_install_package(
            "jeepney",
            ">=0.9.0",
            (
                "jeepney",
                [
                    "DBusAddress",
                    "new_method_call",
                    "io.blocking.open_dbus_connection",
                ],
            ),
        )
        self.conn = self.jeepney.io.blocking.open_dbus_connection(bus="SYSTEM")

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
        """Recursively get all child object paths via introspection"""
        introspect_iface = "org.freedesktop.DBus.Introspectable"
        addr = self.jeepney.DBusAddress(
            object_path, bus_name=service, interface=introspect_iface
        )
        msg = self.jeepney.new_method_call(addr, "Introspect")
        reply = self.conn.send_and_get_reply(msg)
        xml_string = reply.body[0]

        for child in ElementTree.fromstring(xml_string):
            if child.tag == "node":
                name = child.attrib["name"]
                new_path = object_path.rstrip("/") + "/" + name
                paths.append(new_path)
                self.dbus_paths(service, new_path, paths)
        return paths

    def get_property(self, object_path, interface, prop):
        """Gets the device property"""
        addr = self.jeepney.DBusAddress(
            object_path,
            bus_name="org.freedesktop.UPower",
            interface="org.freedesktop.DBus.Properties",
        )
        msg = self.jeepney.new_method_call(addr, "Get", "ss", (interface, prop))
        reply = self.conn.send_and_get_reply(msg)
        return reply.body[0][1]

    def get_batteries(self):
        """Gets a list of all devices and their status"""
        device_iface = "org.freedesktop.UPower.Device"
        batteries = []
        paths = self.dbus_paths("org.freedesktop.UPower", "/org/freedesktop/UPower", [])

        for path in paths:
            try:
                # Check if it's a UPower.Device
                props = {
                    "Model": self.get_property(path, device_iface, "Model"),
                    "NativePath": self.get_property(path, device_iface, "NativePath"),
                    "Percentage": self.get_property(path, device_iface, "Percentage"),
                    "Serial": self.get_property(path, device_iface, "Serial"),
                    "IconName": self.get_property(path, device_iface, "IconName"),
                    "IsRechargeable": self.get_property(
                        path, device_iface, "IsRechargeable"
                    ),
                    "Vendor": self.get_property(path, device_iface, "Vendor"),
                }
                if props["Model"] + props["NativePath"] not in ["bb", "b", ""]:
                    if isinstance(props["Percentage"], float):
                        batteries.append(props)
            except Exception:
                # Not a UPower.Device or missing properties
                continue

        return batteries
