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
            discovery_info[
                f"Bluetooth Device {blinfo['name']} {mac.replace(':', '')}"
            ] = {
                "type": "switch",
                "icon": "mdi:bluetooth",
                "value_template": f"{{{{ value_json.devices.get('{mac}', {{}}).get('power') }}}}",
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        bluetoothdata = self._get_bluetoothdata()
        loaded = set(bluetoothdata["devices"]) - set(self.bluetoothdata["devices"])
        unloaded = set(self.bluetoothdata["devices"]) - set(bluetoothdata["devices"])
        for device in unloaded:
            for addr in self.bluetoothdata.get(device):
                if addr is not None:
                    self.bluetoothdata[device][addr] = None
            bluetoothdata[device] = self.bluetoothdata[device]
        self.bluetoothdata = bluetoothdata
        if len(loaded) > 0:
            self.lnxlink.setup_discovery()
        return self.bluetoothdata

    def _bytetogb(self, byte):
        return round(byte / 1024 / 1024 / 1024, 0)

    def _get_bluetoothdata(self):
        """Get a list of all bluetooth devices"""
        data = {
            "power": "OFF",
            "devices": {},
        }
        stdout, _, _ = syscommand("bluetoothctl show | grep Powered")
        if "yes" in stdout:
            data["power"] = "ON"

        stdout, _, returncode = syscommand("bluetoothctl devices Paired")
        if returncode != 0:
            stdout, _, _ = syscommand("bluetoothctl paired-devices")
        if stdout != "":
            for device in stdout.split("\n"):
                _, mac, name = device.split(" ", maxsplit=2)
                stdoutdevice, _, _ = syscommand(
                    f"bluetoothctl info {mac} | grep Connected"
                )
                power = "OFF"
                if "yes" in stdoutdevice:
                    power = "ON"
                data["devices"][mac] = {
                    "name": name,
                    "power": power,
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
