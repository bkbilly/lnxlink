"""Controls Paired Bluetooth Devices"""
import re
import logging
from lnxlink.modules.scripts.helpers import syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Bluetooth"
        self.lnxlink = lnxlink
        _, _, returncode = syscommand("bluetoothctl show")
        if returncode != 0:
            raise SystemError("Can't run command bluetoothctl")
        self.bluetoothdata = self._get_bluetoothdata()

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
            attr_templ = f"{{{{ value_json.devices.get('{mac}', {{}}).get('attributes') | tojson }}}}"
            discovery_info[
                f"Bluetooth Device {blinfo['name'].replace('+', '')} {mac.replace(':', '')}"
            ] = {
                "type": "switch",
                "icon": "mdi:bluetooth",
                "value_template": f"{{{{ value_json.devices.get('{mac}', {{}}).get('power') }}}}",
                "attributes_template": attr_templ,
            }
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

    def _bytetogb(self, byte):
        return round(byte / 1024 / 1024 / 1024, 0)

    def _get_bluetoothdata(self):
        """Get a list of all bluetooth devices"""
        data = {
            "power": "OFF",
            "devices": {},
            "attributes": {
                "battery": None,
            },
        }
        stdout, _, _ = syscommand("bluetoothctl show | grep Powered")
        if "yes" in stdout:
            data["power"] = "ON"

        stdout, _, returncode = syscommand("bluetoothctl devices Paired")
        if returncode != 0:
            stdout, _, _ = syscommand("bluetoothctl paired-devices")
        if stdout == "":
            return data
        for device in stdout.split("\n"):
            try:
                device_type, mac, name = device.split(" ", maxsplit=2)
                if device_type != "Device":
                    continue
            except Exception:
                continue
            stdoutdevice, _, _ = syscommand(f"bluetoothctl info {mac}")
            power = "OFF"
            if re.search(r"Connected:\s*yes", stdoutdevice):
                power = "ON"
            battery = None
            match = re.search(r"Battery Percentage:.*\((\d+)\)", stdoutdevice)
            if match:
                battery = match.group(1)
            data["devices"][mac] = {
                "name": name,
                "power": power,
                "attributes": {
                    "battery": battery,
                },
            }

        return data

    def start_control(self, topic, data):
        """Control system"""
        if topic[1] == "bluetooth_power":
            syscommand(f"bluetoothctl power {data.lower()}")
        else:
            simple_mac = topic[1].split("_")[-1]
            mac = ":".join(re.findall("..?", simple_mac))
            if data == "ON":
                syscommand(f"bluetoothctl connect {mac}")
            elif data == "OFF":
                syscommand(f"bluetoothctl disconnect {mac}")
