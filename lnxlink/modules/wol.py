"""WOL Status control"""
import re
import psutil
from lnxlink.modules.scripts.helpers import syscommand, text_to_topic


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "WOL"
        self.lnxlink = lnxlink
        self.interfaces = {}
        self._get_interfaces()
        if len(self.interfaces) == 0:
            raise SystemError(
                "Can't find any supported interface or ethtool doesn't has access to sudo."
            )

    def get_info(self):
        """Gather information from the system"""
        for interf in self.interfaces:
            cmd = f"sudo -n /usr/sbin/ethtool {interf}"
            stdout, _, _ = syscommand(cmd)
            self.interfaces[interf] = "OFF"
            match_wol = re.search(r"\tWake-on: (\S*)", stdout)
            if match_wol:
                if "g" in match_wol.group(1):
                    self.interfaces[interf] = "ON"

        return self.interfaces

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for interf in self.interfaces:
            discovery_info[f"WOL {interf}"] = {
                "type": "switch",
                "icon": "mdi:ethernet",
                "value_template": f"{{{{ value_json.get('{interf}') }}}}",
            }
        return discovery_info

    def start_control(self, topic, data):
        """Control system"""
        for interf in self.interfaces:
            if text_to_topic(topic[1]).replace("wol_", "") == interf:
                if data == "ON":
                    syscommand(f"sudo ethtool -s {interf} wol g")
                elif data == "OFF":
                    syscommand(f"sudo ethtool -s {interf} wol d")

    def _get_interfaces(self):
        """Get a list of all interfaces"""
        interfaces = []
        addrs = psutil.net_if_addrs()
        for interf, _ in addrs.items():
            if interf.startswith("veth"):
                continue
            interfaces.append(interf)

        self.interfaces = {}
        for interf in interfaces:
            cmd = f"sudo -n /usr/sbin/ethtool {interf}"
            stdout, _, errorcode = syscommand(cmd)
            if errorcode == 0:
                match = re.search(r"\tSupports Wake-on: (\S*)", stdout)
                if match:
                    if "g" in match.group(1):
                        self.interfaces[interf] = None


if __name__ == "__main__":
    Addon("").get_info()
