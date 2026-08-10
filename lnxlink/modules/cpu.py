"""Monitor real-time CPU load and performance"""
import psutil

from lnxlink.modules.scripts.helpers import syscommand


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "CPU Usage"
        self.lnxlink = lnxlink
        self.cpuinfo = self._cpuinfo()
        self.cores = psutil.cpu_count() or 1

    def get_info(self):
        """Gather information from the system"""
        raw_load = psutil.getloadavg()
        load = [round(x, 2) for x in raw_load]
        load_percent = round((load[0] / self.cores) * 100, 1)

        return {
            "percent": psutil.cpu_percent(),
            "load": load[0],
            "load_percent": load_percent,
            "attributes": {
                "CPU Info": self.cpuinfo,
                "Cores": self.cores,
                "Load 1m": load[0],
                "Load 5m": load[1],
                "Load 15m": load[2],
                "Load 1m %": f"{load_percent}%",
            },
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
            "CPU Load Average": {
                "type": "sensor",
                "icon": "mdi:cpu-64-bit",
                "unit": "%",
                "state_class": "measurement",
                "expire_after": update_interval * 5,
                "value_template": "{{ value_json.get('load_percent')}}",
                "attributes_template": "{{ value_json.get('attributes', {}) | tojson }}",
            },
        }

    def _cpuinfo(self):
        cmd = (
            "cat /proc/cpuinfo | grep -i 'model name' | uniq | awk -F ':' '{print $2}'"
        )
        stdout, _, _ = syscommand(cmd)
        return stdout
