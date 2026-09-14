"""Track battery levels for all connected devices"""
import time
from xml.etree import ElementTree

from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection

from lnxlink.modules.scripts import hidpp

UPOWER_DEVICE_TYPE_LINE_POWER = 1
UPOWER_DEVICE_TYPE_BATTERY = 2
UPOWER_DEVICE_TYPE_MOUSE = 5
UPOWER_DEVICE_TYPE_KEYBOARD = 6

# HID++ device type code -> UPower device type
HIDPP_DEVICE_TYPES = {
    0: UPOWER_DEVICE_TYPE_KEYBOARD,
    2: UPOWER_DEVICE_TYPE_KEYBOARD,  # numpad
    3: UPOWER_DEVICE_TYPE_MOUSE,
    4: UPOWER_DEVICE_TYPE_MOUSE,  # touchpad
    5: UPOWER_DEVICE_TYPE_MOUSE,  # trackball
}
# HID++ charge state code -> UPower battery state
HIDPP_CHARGE_STATES = {
    0: 2,  # discharging
    1: 1,  # charging
    2: 1,  # charging slowly
    3: 4,  # fully charged
}


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Battery"
        self.lnxlink = lnxlink
        self.conn = open_dbus_connection(bus="SYSTEM")
        self.lnxlink.add_settings(
            "battery",
            {
                "include_batteries": [],
                "exclude_batteries": [],
                "hidpp": True,
                "hidpp_interval": 300,
            },
        )
        self.hidpp_batteries = []
        self.hidpp_checked = 0
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
            devices[device_name] = dict(self.devices[device_name])
            devices[device_name]["percent"] = None
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

        for device in self.get_batteries() + self.get_hidpp_batteries():
            if battery_includes:
                if not any(device["Model"].startswith(x) for x in battery_includes):
                    continue
            if battery_excludes:
                if any(device["Model"].startswith(x) for x in battery_excludes):
                    continue

            native_path = device["NativePath"].split("/")[-1]
            name = (
                " ".join(
                    [
                        device["Vendor"],
                        device["Model"],
                        device["Serial"].replace(":", "").replace("/", ""),
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

    def get_hidpp_batteries(self):
        """Gets the Logitech devices which the kernel doesn't report to UPower

        Their battery is read straight from /dev/hidraw, and a receiver answers
        for up to six slots, which is slow enough that this gets an interval of
        its own instead of running on every update.
        """
        settings = self.lnxlink.config["settings"].get("battery", {})
        if not settings.get("hidpp", True):
            return []
        if time.time() - self.hidpp_checked < settings.get("hidpp_interval", 300):
            return self.hidpp_batteries
        self.hidpp_checked = time.time()

        batteries = []
        for device in hidpp.get_batteries():
            name = device["name"] or f"{device['node']} slot {device['slot']}"
            batteries.append(
                {
                    "Model": name,
                    "NativePath": f"hidpp_{device['node']}_{device['slot']}",
                    "Percentage": float(device["percent"]),
                    "Serial": "",
                    "Type": HIDPP_DEVICE_TYPES.get(
                        device["device_type"], UPOWER_DEVICE_TYPE_BATTERY
                    ),
                    "IconName": "battery",
                    "IsRechargeable": True,
                    "Vendor": "Logitech",
                    "State": HIDPP_CHARGE_STATES.get(device["charge_state"], 0),
                    "TimeToEmpty": 0,
                    "TimeToFull": 0,
                }
            )
        self.hidpp_batteries = batteries
        return batteries

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
                    "Type": self.get_property(path, device_iface, "Type"),
                    "IconName": self.get_property(path, device_iface, "IconName"),
                    "IsRechargeable": self.get_property(
                        path, device_iface, "IsRechargeable"
                    ),
                    "Vendor": self.get_property(path, device_iface, "Vendor"),
                    "State": self.get_property(path, device_iface, "State"),
                    "TimeToEmpty": self.get_property(path, device_iface, "TimeToEmpty"),
                    "TimeToFull": self.get_property(path, device_iface, "TimeToFull"),
                }
                if props["Type"] == UPOWER_DEVICE_TYPE_LINE_POWER:
                    continue
                if props["Model"] + props["NativePath"] not in ["bb", "b", ""]:
                    if isinstance(props["Percentage"], float):
                        batteries.append(props)
            except Exception:
                # Not a UPower.Device or missing properties
                continue

        return batteries
