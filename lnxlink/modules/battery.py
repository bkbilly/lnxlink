"""Gets the battery information of connected devices"""
from xml.etree import ElementTree
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Battery"
        self.lnxlink = lnxlink
        self.conn = open_dbus_connection(bus="SYSTEM")
        self.devices = self._get_devices()

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
            self.lnxlink.setup_discovery("battery")

        return devices

    def _get_devices(self):
        devices = {}
        battery_includes = (
            self.lnxlink.config["settings"]
            .get("battery", {})
            .get("include_batteries", [])
        )
        battery_excludes = (
            self.lnxlink.config["settings"]
            .get("battery", {})
            .get("exclude_batteries", [])
        )

        u_power_states = {
            0: "unknown",
            1: "charging",
            2: "discharging",
            3: "empty",
            4: "fully charged",
            5: "pending charge",
            6: "pending discharge",
        }

        for device in self.get_batteries():
            if len(battery_includes) != 0:
                if not any(device["Model"].startswith(x) for x in battery_includes):
                    continue
            if len(battery_excludes) != 0:
                if any(device["Model"].startswith(x) for x in battery_excludes):
                    continue

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
                        "status": u_power_states[device["State"]],
                        "time_to_empty": device["TimeToEmpty"],
                        "time_to_full": device["TimeToFull"],
                    },
                }
        return devices

    def dbus_paths(self, service, object_path, paths):
        """Recursively get all child object paths via introspection"""
        introspect_iface = "org.freedesktop.DBus.Introspectable"
        addr = DBusAddress(object_path, bus_name=service, interface=introspect_iface)
        msg = new_method_call(addr, "Introspect")
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
        addr = DBusAddress(
            object_path,
            bus_name="org.freedesktop.UPower",
            interface="org.freedesktop.DBus.Properties",
        )
        msg = new_method_call(addr, "Get", "ss", (interface, prop))
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
                    "State": self.get_property(path, device_iface, "State"),
                    "TimeToEmpty": self.get_property(path, device_iface, "TimeToEmpty"),
                    "TimeToFull": self.get_property(path, device_iface, "TimeToFull"),
                }
                if props["Model"] + props["NativePath"] not in ["bb", "b", ""]:
                    if isinstance(props["Percentage"], float):
                        batteries.append(props)
            except Exception:
                # Not a UPower.Device or missing properties
                continue

        return batteries
