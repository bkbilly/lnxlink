"""Gets Interface names with their IP information"""
import logging
import psutil

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Interfaces"
        self.lnxlink = lnxlink
        self.interfaces = self._get_interfaces()

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for device in self.interfaces:
            discovery_info[f"Interface {device}"] = {
                "type": "sensor",
                "icon": "mdi:lan-connect",
                "value_template": f"{{{{ value_json.get('{device}', {{}}).get('ipv4') }}}}",
                "attributes_template": f"{{{{ value_json.get('{device}', {{}}) | tojson }}}}",
                "enabled": True,
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        interfaces = self._get_interfaces()
        loaded = set(interfaces) - set(self.interfaces)
        unloaded = set(self.interfaces) - set(interfaces)
        for interface in unloaded:
            for addr in self.interfaces[interface]:
                self.interfaces[interface][addr] = None
            interfaces[interface] = self.interfaces[interface]
        self.interfaces = interfaces
        if len(loaded) > 0:
            self.lnxlink.setup_discovery("interfaces")
        return self.interfaces

    def _bytetogb(self, byte):
        return round(byte / 1024 / 1024 / 1024, 0)

    def _get_interfaces(self):
        """Get a list of all interfaces"""
        interfaces = {}
        addrs = psutil.net_if_addrs()
        for interf, addr in addrs.items():
            if interf.startswith("veth"):
                continue
            for addr_item in addr:
                if addr_item.address not in ["127.0.0.1", "::1"]:
                    afinet = {
                        "AF_INET": "ipv4",
                        "AF_INET6": "ipv6",
                    }.get(addr_item.family.name)
                    if afinet is not None:
                        address = addr_item.address.replace(f"%{interf}", "")
                        interfaces.setdefault(interf, {})[afinet] = address
                        interfaces[interf][f"{afinet} NetMask"] = addr_item.netmask
        return interfaces
