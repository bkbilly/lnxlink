"""Gets CPU usage information"""
import psutil
from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "CPU Usage"
        self.lnxlink = lnxlink
        self.cpuinfo = self._cpuinfo()

    def get_info(self):
        """Gather information from the system"""
        return {
            "percent": psutil.cpu_percent(),
            "attributes": {"CPU Info": self.cpuinfo},
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        update_interval = self.lnxlink.config.get("update_interval", 5)
        return {
            "CPU Usage": {
                "type": "sensor",
                "icon": "mdi:speedometer",
                "unit": "%",
                "state_class": "measurement",
                "expire_after": update_interval * 5,
                "value_template": "{{ value_json.get('percent')}}",
                "attributes_template": "{{ value_json.get('attributes', {}) | tojson }}",
            },
        }

    def _cpuinfo(self):
        cmd = (
            "cat /proc/cpuinfo | grep -i 'model name' | uniq | awk -F ':' '{print $2}'"
        )
        stdout, _, _ = syscommand(cmd)
        return stdout
