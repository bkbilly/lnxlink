"""Control global Bluetooth power or connect/disconnect specific devices"""

import re
import logging
from xml.etree import ElementTree
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection
from jeepney.wrappers import DBusErrorResponse

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Bluetooth"
        self.lnxlink = lnxlink
        self.adapter_path = self._get_adapter_path()
        if self.adapter_path is None:
            raise SystemError("No Bluetooth adapter found")
        self.bluetoothdata = self._get_bluetoothdata()

    def _get_connection(self):
        """Get a fresh D-Bus connection"""
        return open_dbus_connection(bus="SYSTEM")

    def _get_adapter_path(self):
        """Find the first available Bluetooth adapter"""
        paths = self._dbus_paths("org.bluez", "/org/bluez", [])
        for path in paths:
            if self._has_interface(path, "org.bluez.Adapter1"):
                return path
        return None

    def _dbus_paths(self, service, object_path, paths, conn=None):
        """Recursively get all child object paths via introspection"""
        if conn is None:
            conn = self._get_connection()
        introspect_iface = "org.freedesktop.DBus.Introspectable"
        addr = DBusAddress(object_path, bus_name=service, interface=introspect_iface)
        msg = new_method_call(addr, "Introspect")
        try:
            reply = conn.send_and_get_reply(msg)
            xml_string = reply.body[0]
        except (OSError, DBusErrorResponse):
            return paths

        for child in ElementTree.fromstring(xml_string):
            if child.tag == "node":
                name = child.attrib["name"]
                new_path = object_path.rstrip("/") + "/" + name
                paths.append(new_path)
                self._dbus_paths(service, new_path, paths, conn)
        return paths

    def _has_interface(self, object_path, interface, conn=None):
        """Check if an object implements a specific interface"""
        if conn is None:
            conn = self._get_connection()
        introspect_iface = "org.freedesktop.DBus.Introspectable"
        addr = DBusAddress(object_path, bus_name="org.bluez", interface=introspect_iface)
        msg = new_method_call(addr, "Introspect")
        try:
            reply = conn.send_and_get_reply(msg)
            xml_string = reply.body[0]
            return interface in xml_string
        except (OSError, DBusErrorResponse):
            return False

    def _get_property(self, *, object_path, interface, prop, conn=None):
        """Get a property from a D-Bus object"""
        if conn is None:
            conn = self._get_connection()
        addr = DBusAddress(
            object_path,
            bus_name="org.bluez",
            interface="org.freedesktop.DBus.Properties",
        )
        msg = new_method_call(addr, "Get", "ss", (interface, prop))
        reply = conn.send_and_get_reply(msg)
        return reply.body[0][1]

    # pylint: disable=too-many-arguments
    def _set_property(self, *, object_path, interface, prop, value, signature):
        """Set a property on a D-Bus object"""
        conn = self._get_connection()
        addr = DBusAddress(
            object_path,
            bus_name="org.bluez",
            interface="org.freedesktop.DBus.Properties",
        )
        msg = new_method_call(addr, "Set", "ssv", (interface, prop, (signature, value)))
        conn.send_and_get_reply(msg)

    def _call_method(self, object_path, interface, method):
        """Call a method on a D-Bus object"""
        conn = self._get_connection()
        addr = DBusAddress(object_path, bus_name="org.bluez", interface=interface)
        msg = new_method_call(addr, method)
        conn.send_and_get_reply(msg)

    @staticmethod
    def _battery_sensor(value_template):
        """Return common battery sensor configuration"""
        return {
            "type": "sensor",
            "icon": "mdi:battery-bluetooth",
            "unit": "%",
            "device_class": "battery",
            "state_class": "measurement",
            "value_template": value_template,
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {
            "Bluetooth Power": {
                "type": "switch",
                "icon": "mdi:bluetooth-connect",
                "value_template": "{{ value_json.get('power') }}",
            }
        }
        for mac, blinfo in self.bluetoothdata["devices"].items():
            attr_templ = (
                f"{{{{ value_json.devices.get('{mac}', {{}}).get('attributes') | tojson }}}}"
            )
            device_name = blinfo["name"].replace("+", "")
            mac_clean = mac.replace(":", "")
            discovery_info[f"Bluetooth Device {device_name} {mac_clean}"] = {
                "type": "switch",
                "icon": "mdi:bluetooth",
                "value_template": f"{{{{ value_json.devices.get('{mac}', {{}}).get('power') }}}}",
                "attributes_template": attr_templ,
            }
            # Expose battery sensors - prefer GATT batteries, fallback to Battery1
            batteries = blinfo.get("batteries")
            if batteries:
                for battery_key in batteries:
                    battery_num = battery_key.replace("battery_", "")
                    value_template = (
                        f"{{{{ value_json.devices.get('{mac}', {{}})"
                        f".get('batteries', {{}}).get('{battery_key}') }}}}"
                    )
                    discovery_info[
                        f"Bluetooth Device {device_name} {mac_clean} Battery {battery_num}"
                    ] = self._battery_sensor(value_template)
            else:
                # Fallback to single battery from Battery1 interface
                battery = blinfo.get("attributes", {}).get("battery")
                if battery is not None:
                    value_template = (
                        f"{{{{ value_json.devices.get('{mac}', {{}})"
                        f".get('attributes', {{}}).get('battery') }}}}"
                    )
                    discovery_info[f"Bluetooth Device {device_name} {mac_clean} Battery"] = (
                        self._battery_sensor(value_template)
                    )
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        bluetoothdata = self._get_bluetoothdata()
        loaded = set(bluetoothdata["devices"]) - set(self.bluetoothdata["devices"])
        unloaded = set(self.bluetoothdata["devices"]) - set(bluetoothdata["devices"])
        for device in unloaded:
            bluetoothdevices = self.bluetoothdata.get(device)
            if bluetoothdevices is not None:
                for addr in bluetoothdevices:
                    if addr is not None:
                        self.bluetoothdata[device][addr] = None
            if device in self.bluetoothdata:
                bluetoothdata[device] = self.bluetoothdata[device]
        self.bluetoothdata = bluetoothdata
        if len(loaded) > 0:
            self.lnxlink.setup_discovery("bluetooth")
        return self.bluetoothdata

    def _get_gatt_batteries(self, device_path, conn=None):
        """Get battery levels from GATT characteristics.

        Useful for multi-battery devices like split keyboards.
        """
        if conn is None:
            conn = self._get_connection()

        battery_uuid = "00002a19-0000-1000-8000-00805f9b34fb"
        batteries = {}

        # Find all child paths under the device
        paths = self._dbus_paths("org.bluez", device_path, [], conn)

        battery_index = 0
        for path in paths:
            if not self._has_interface(path, "org.bluez.GattCharacteristic1", conn):
                continue

            try:
                uuid = self._get_property(
                    object_path=path,
                    interface="org.bluez.GattCharacteristic1",
                    prop="UUID",
                    conn=conn,
                )
                if uuid.lower() != battery_uuid:
                    continue

                # Read the battery value
                addr = DBusAddress(
                    path,
                    bus_name="org.bluez",
                    interface="org.bluez.GattCharacteristic1",
                )

                # Prevents reading cached value
                msg = new_method_call(addr, "ReadValue", "a{sv}", ({},))
                reply = conn.send_and_get_reply(msg)
                value = reply.body[0]
                if value and len(value) > 0:
                    battery_level = value[0]
                    batteries[f"battery_{battery_index}"] = battery_level
                    battery_index += 1
            except (OSError, DBusErrorResponse) as err:
                logger.debug("Failed to read GATT battery from %s: %s", path, err)
                continue

        return batteries

    def _get_bluetoothdata(self):
        """Get a list of all bluetooth devices using BlueZ D-Bus API"""
        conn = self._get_connection()
        data = {
            "power": "OFF",
            "devices": {},
            "attributes": {
                "battery": None,
            },
        }

        # Get adapter power state
        try:
            powered = self._get_property(
                object_path=self.adapter_path,
                interface="org.bluez.Adapter1",
                prop="Powered",
                conn=conn,
            )
            if powered:
                data["power"] = "ON"
        except (OSError, DBusErrorResponse) as err:
            logger.debug("Failed to get adapter power state: %s", err)

        # Get all device paths
        paths = self._dbus_paths("org.bluez", "/org/bluez", [], conn)

        for path in paths:
            if not self._has_interface(path, "org.bluez.Device1", conn):
                continue

            try:
                # Check if device is paired
                paired = self._get_property(
                    object_path=path, interface="org.bluez.Device1", prop="Paired", conn=conn
                )
                if not paired:
                    continue

                # Get device properties
                mac = self._get_property(
                    object_path=path, interface="org.bluez.Device1", prop="Address", conn=conn
                )
                name = self._get_property(
                    object_path=path, interface="org.bluez.Device1", prop="Name", conn=conn
                )
                connected = self._get_property(
                    object_path=path, interface="org.bluez.Device1", prop="Connected", conn=conn
                )

                # Get device name
                power = "ON" if connected else "OFF"

                # Try to get battery percentage from Battery1 interface
                battery = None
                if self._has_interface(path, "org.bluez.Battery1", conn):
                    try:
                        battery = self._get_property(
                            object_path=path,
                            interface="org.bluez.Battery1",
                            prop="Percentage",
                            conn=conn,
                        )
                        battery = str(battery)
                    except (OSError, DBusErrorResponse):
                        pass

                # Get battery levels from GATT characteristics (for multi-battery devices)
                batteries = self._get_gatt_batteries(path, conn)

                data["devices"][mac] = {
                    "name": name,
                    "power": power,
                    "batteries": batteries if batteries else None,
                    "attributes": {
                        "battery": battery,
                    },
                }
            except (OSError, DBusErrorResponse) as err:
                logger.debug("Failed to get device info for %s: %s", path, err)
                continue

        return data

    def _mac_to_path(self, mac):
        """Convert MAC address to BlueZ device path"""
        mac_path = mac.upper().replace(":", "_")
        return f"{self.adapter_path}/dev_{mac_path}"

    def start_control(self, topic, data):
        """Control system"""
        if topic[1] == "bluetooth_power":
            try:
                power_on = data.upper() == "ON"
                self._set_property(
                    object_path=self.adapter_path,
                    interface="org.bluez.Adapter1",
                    prop="Powered",
                    value=power_on,
                    signature="b",
                )
            except (OSError, DBusErrorResponse) as err:
                logger.error("Failed to set Bluetooth power: %s", err)
        else:
            simple_mac = topic[1].split("_")[-1]
            mac = ":".join(re.findall("..?", simple_mac))
            device_path = self._mac_to_path(mac)
            try:
                if data == "ON":
                    self._call_method(device_path, "org.bluez.Device1", "Connect")
                elif data == "OFF":
                    self._call_method(device_path, "org.bluez.Device1", "Disconnect")
            except (OSError, DBusErrorResponse) as err:
                logger.error("Failed to %s device %s: %s", data.lower(), mac, err)
