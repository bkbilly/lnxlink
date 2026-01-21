"""Control global Bluetooth power or connect/disconnect specific devices"""

import re
import logging
from typing import Optional, Dict, List, Any
from xml.etree import ElementTree
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection
from jeepney.wrappers import DBusErrorResponse

logger = logging.getLogger("lnxlink")

# D-Bus constants
BLUEZ_SERVICE = "org.bluez"
BLUEZ_ADAPTER_INTERFACE = "org.bluez.Adapter1"
BLUEZ_DEVICE_INTERFACE = "org.bluez.Device1"
BLUEZ_BATTERY_INTERFACE = "org.bluez.Battery1"
BLUEZ_GATT_CHARACTERISTIC_INTERFACE = "org.bluez.GattCharacteristic1"
DBUS_PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
DBUS_INTROSPECTABLE_INTERFACE = "org.freedesktop.DBus.Introspectable"
BATTERY_CHARACTERISTIC_UUID = "00002a19-0000-1000-8000-00805f9b34fb"


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Bluetooth"
        self.lnxlink = lnxlink
        self.conn = open_dbus_connection(bus="SYSTEM")
        self.adapter_path = self._get_adapter_path()
        if self.adapter_path is None:
            raise SystemError("No Bluetooth adapter found")
        self.bluetoothdata = self._get_bluetoothdata()

    @staticmethod
    def _battery_sensor(value_template: str) -> Dict[str, Any]:
        """Return common battery sensor configuration"""
        return {
            "type": "sensor",
            "icon": "mdi:battery-bluetooth",
            "unit": "%",
            "device_class": "battery",
            "state_class": "measurement",
            "value_template": value_template,
        }

    def exposed_controls(self) -> Dict[str, Dict[str, Any]]:
        """Expose controls and sensors to Home Assistant"""
        discovery_info = {
            "Bluetooth Power": {
                "type": "switch",
                "icon": "mdi:bluetooth-connect",
                "value_template": "{{ value_json.get('power') }}",
            }
        }

        for mac, device_info in self.bluetoothdata["devices"].items():
            # Clean device name and MAC for entity IDs
            device_name = device_info["name"].replace("+", "")
            mac_clean = mac.replace(":", "")

            # Device power switch
            attr_templ = f"{{{{ value_json.devices.get('{mac}', {{}}).get('attributes') | tojson }}}}"
            discovery_info[f"Bluetooth Device {device_name} {mac_clean}"] = {
                "type": "switch",
                "icon": "mdi:bluetooth",
                "value_template": f"{{{{ value_json.devices.get('{mac}', {{}}).get('power') }}}}",
                "attributes_template": attr_templ,
            }

            # GATT battery sensors (for multi-battery devices)
            batteries = device_info.get("batteries")
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
                battery = device_info.get("attributes", {}).get("battery")
                if battery is not None:
                    value_template = (
                        f"{{{{ value_json.devices.get('{mac}', {{}})"
                        f".get('attributes', {{}}).get('battery') }}}}"
                    )
                    discovery_info[
                        f"Bluetooth Device {device_name} {mac_clean} Battery"
                    ] = self._battery_sensor(value_template)

        return discovery_info

    def get_info(self) -> Dict[str, Any]:
        """Gather information from the system"""
        bluetoothdata = self._get_bluetoothdata()

        # Track newly loaded and unloaded devices
        loaded = set(bluetoothdata["devices"]) - set(self.bluetoothdata["devices"])
        unloaded = set(self.bluetoothdata["devices"]) - set(bluetoothdata["devices"])

        # Preserve data for unloaded devices
        for device in unloaded:
            if device in self.bluetoothdata:
                bluetoothdata["devices"][device] = self.bluetoothdata["devices"][device]

        self.bluetoothdata = bluetoothdata

        # Trigger discovery for newly loaded devices
        if loaded:
            logger.info("New devices detected: %s", loaded)
            self.lnxlink.setup_discovery("bluetooth")

        return self.bluetoothdata

    def start_control(self, topic: List[str], data: str) -> None:
        """Control system"""
        if topic[1] == "bluetooth_power":
            try:
                power_on = data.upper() == "ON"
                self._set_property(
                    interface=BLUEZ_ADAPTER_INTERFACE,
                    prop="Powered",
                    value=power_on,
                    signature="b",
                )
                logger.info("Bluetooth power set to %s", data.upper())
            except (OSError, DBusErrorResponse) as err:
                logger.error("Failed to set Bluetooth power: %s", err)
        else:
            # Extract MAC address from topic
            simple_mac = topic[1].split("_")[-1]
            mac = ":".join(re.findall("..", simple_mac))
            device_path = self._mac_to_path(mac)

            try:
                if data.upper() == "ON":
                    self._call_method(device_path, BLUEZ_DEVICE_INTERFACE, "Connect")
                    logger.info("Connecting to device %s", mac)
                elif data.upper() == "OFF":
                    self._call_method(device_path, BLUEZ_DEVICE_INTERFACE, "Disconnect")
                    logger.info("Disconnecting from device %s", mac)
            except (OSError, DBusErrorResponse) as err:
                logger.error("Failed to %s device %s: %s", data.lower(), mac, err)

    def _get_gatt_batteries(self, device_path: str) -> Dict[str, int]:
        """Get battery levels from GATT characteristics"""
        batteries = {}
        paths = self._dbus_paths(BLUEZ_SERVICE, device_path, [])

        battery_index = 0
        for path in paths:
            if not self._has_interface(path, BLUEZ_GATT_CHARACTERISTIC_INTERFACE):
                continue

            try:
                uuid = self._get_property(
                    object_path=path,
                    interface=BLUEZ_GATT_CHARACTERISTIC_INTERFACE,
                    prop="UUID",
                )
                if uuid.lower() != BATTERY_CHARACTERISTIC_UUID:
                    continue

                # Read the battery value (prevents reading cached value)
                addr = DBusAddress(
                    path,
                    bus_name=BLUEZ_SERVICE,
                    interface=BLUEZ_GATT_CHARACTERISTIC_INTERFACE,
                )
                msg = new_method_call(addr, "ReadValue", "a{sv}", ({},))
                reply = self.conn.send_and_get_reply(msg)
                value = reply.body[0]

                if value and len(value) > 0:
                    battery_level = value[0]
                    # Only add valid battery levels (0-100), skip invalid values
                    if isinstance(battery_level, int) and 0 <= battery_level <= 100:
                        batteries[f"battery_{battery_index}"] = battery_level
                        battery_index += 1
            except (OSError, DBusErrorResponse) as err:
                logger.debug("Failed to read GATT battery from %s: %s", path, err)
                continue

        return batteries

    def _get_bluetoothdata(self) -> Dict[str, Any]:
        """Get current state of all Bluetooth devices using BlueZ D-Bus API"""
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
                interface=BLUEZ_ADAPTER_INTERFACE,
                prop="Powered",
            )
            data["power"] = "ON" if powered else "OFF"
        except (OSError, DBusErrorResponse) as err:
            logger.debug("Failed to get adapter power state: %s", err)

        # Get all device paths
        paths = self._dbus_paths(BLUEZ_SERVICE, "/org/bluez", [])

        for path in paths:
            if not self._has_interface(path, BLUEZ_DEVICE_INTERFACE):
                continue

            try:
                # Only include paired devices
                paired = self._get_property(
                    object_path=path,
                    interface=BLUEZ_DEVICE_INTERFACE,
                    prop="Paired",
                )
                if not paired:
                    continue

                # Get device properties
                mac = self._get_property(
                    object_path=path,
                    interface=BLUEZ_DEVICE_INTERFACE,
                    prop="Address",
                )
                name = self._get_property(
                    object_path=path,
                    interface=BLUEZ_DEVICE_INTERFACE,
                    prop="Name",
                )
                connected = self._get_property(
                    object_path=path,
                    interface=BLUEZ_DEVICE_INTERFACE,
                    prop="Connected",
                )

                power = "ON" if connected else "OFF"

                # Try to get battery percentage from Battery1 interface
                battery = None
                if self._has_interface(path, BLUEZ_BATTERY_INTERFACE):
                    try:
                        battery = self._get_property(
                            object_path=path,
                            interface=BLUEZ_BATTERY_INTERFACE,
                            prop="Percentage",
                        )
                        battery = str(battery)
                    except (OSError, DBusErrorResponse):
                        pass

                # Get battery levels from GATT characteristics (for multi-battery devices)
                # Only attempt if device is connected
                batteries = {}
                if connected:
                    gatt_batteries = self._get_gatt_batteries(path)
                    # Convert empty dict to None
                    if gatt_batteries:
                        batteries = gatt_batteries

                data["devices"][mac] = {
                    "name": name,
                    "power": power,
                    "batteries": batteries,
                    "attributes": {
                        "battery": battery,
                    },
                }
            except (OSError, DBusErrorResponse) as err:
                logger.debug("Failed to get device info for %s: %s", path, err)
                continue

        return data

    def _mac_to_path(self, mac: str) -> str:
        """Convert MAC address to BlueZ device path"""
        mac_path = mac.upper().replace(":", "_")
        return f"{self.adapter_path}/dev_{mac_path}"

    def _get_adapter_path(self) -> Optional[str]:
        """Find the first available Bluetooth adapter"""
        paths = self._dbus_paths(BLUEZ_SERVICE, "/org/bluez", [])
        for path in paths:
            if self._has_interface(path, BLUEZ_ADAPTER_INTERFACE):
                logger.info("Found Bluetooth adapter at %s", path)
                return path
        logger.warning("No Bluetooth adapter found")
        return None

    def _dbus_paths(
        self, service: str, object_path: str, paths: List[str]
    ) -> List[str]:
        """Recursively discover all child object paths via introspection"""
        addr = DBusAddress(
            object_path, bus_name=service, interface=DBUS_INTROSPECTABLE_INTERFACE
        )
        msg = new_method_call(addr, "Introspect")

        try:
            reply = self.conn.send_and_get_reply(msg)
            xml_string = reply.body[0]
        except (OSError, DBusErrorResponse) as err:
            logger.debug("Failed to introspect %s: %s", object_path, err)
            return paths

        root = ElementTree.fromstring(xml_string)
        for child in root:
            if child.tag == "node" and "name" in child.attrib:
                name = child.attrib["name"]
                new_path = f"{object_path.rstrip('/')}/{name}"
                paths.append(new_path)
                self._dbus_paths(service, new_path, paths)

        return paths

    def _has_interface(self, object_path: str, interface: str) -> bool:
        """Check if an object implements a specific interface"""
        addr = DBusAddress(
            object_path, bus_name=BLUEZ_SERVICE, interface=DBUS_INTROSPECTABLE_INTERFACE
        )
        msg = new_method_call(addr, "Introspect")

        try:
            reply = self.conn.send_and_get_reply(msg)
            xml_string = reply.body[0]
            return interface in xml_string
        except (OSError, DBusErrorResponse) as err:
            logger.debug("Failed to check interface on %s: %s", object_path, err)
            return False

    def _get_property(self, object_path: str, interface: str, prop: str) -> Any:
        """Get a property from a D-Bus object"""
        addr = DBusAddress(
            object_path,
            bus_name=BLUEZ_SERVICE,
            interface=DBUS_PROPERTIES_INTERFACE,
        )
        msg = new_method_call(addr, "Get", "ss", (interface, prop))
        reply = self.conn.send_and_get_reply(msg)
        return reply.body[0][1]

    def _set_property(
        self, interface: str, prop: str, value: Any, signature: str
    ) -> None:
        """Set a property on a D-Bus object"""
        addr = DBusAddress(
            self.adapter_path,
            bus_name=BLUEZ_SERVICE,
            interface=DBUS_PROPERTIES_INTERFACE,
        )
        msg = new_method_call(addr, "Set", "ssv", (interface, prop, (signature, value)))
        self.conn.send_and_get_reply(msg)

    def _call_method(self, object_path: str, interface: str, method: str) -> None:
        """Call a method on a D-Bus object"""
        addr = DBusAddress(object_path, bus_name=BLUEZ_SERVICE, interface=interface)
        msg = new_method_call(addr, method)
        self.conn.send_and_get_reply(msg)
