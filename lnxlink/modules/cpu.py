"""Monitor real-time CPU load and performance"""
import glob
import json
import os

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
        self.physical_cores = psutil.cpu_count(logical=False)
        self.numa_nodes = self._numa_nodes()

    @staticmethod
    def _numa_nodes():
        """Return the number of NUMA nodes

        Kernels built without NUMA support have no node directory, the whole
        memory is then a single node.
        """
        try:
            nodes = os.listdir("/sys/devices/system/node")
        except OSError:
            return 1
        return (
            len([node for node in nodes if node[:4] == "node" and node[4:].isdigit()])
            or 1
        )

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
                "Physical Cores": self.physical_cores,
                "NUMA Nodes": self.numa_nodes,
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
        """Return a human readable CPU name"""
        return get_cpu_name()


def _read(path):
    """Read a text file, returning an empty string when it is missing"""
    try:
        with open(path, encoding="utf-8", errors="replace") as file:
            return file.read()
    except OSError:
        return ""


def _unique(values):
    """Remove duplicates and empty values, keeping the order"""
    result = []
    for value in values:
        value = value.strip()
        if value and value != "-" and value not in result:
            result.append(value)
    return result


def _cpuinfo_values(cpuinfo, key):
    """Return the unique values of a /proc/cpuinfo key"""
    values = []
    for line in cpuinfo.splitlines():
        name, sep, value = line.partition(":")
        if sep and name.strip().lower() == key:
            values.append(value)
    return _unique(values)


def _compatible_name(compatible):
    """Format a device tree compatible string, e.g. arm,cortex-a76 -> ARM Cortex-A76"""
    vendor, _, model = compatible.partition(",")
    if not model:
        return compatible
    first, *rest = model.split("-")
    model = "-".join([first.capitalize()] + [part.upper() for part in rest])
    vendor = vendor.upper() if len(vendor) <= 4 else vendor.capitalize()
    return f"{vendor} {model}"


def _sysfs_cores(cpu_path):
    """Core names from the device tree, as exposed in /sys/devices/system/cpu/cpu*/uevent

    Unlike /proc/device-tree (a link to /sys/firmware), this is visible inside
    Docker containers too.
    """
    names = []
    paths = glob.glob(os.path.join(cpu_path, "cpu[0-9]*", "uevent"))
    for path in sorted(paths, key=lambda p: int(os.path.basename(os.path.dirname(p))[3:])):
        for line in _read(path).splitlines():
            if line.startswith("OF_COMPATIBLE_0="):
                names.append(_compatible_name(line.split("=", 1)[1]))
    return _unique(names)


def _lscpu_models():
    """Model names reported by lscpu (e.g. from SMBIOS on ACPI based ARM servers)"""
    stdout, _, returncode = syscommand("LC_ALL=C lscpu -J", ignore_errors=True)
    if returncode != 0 or not stdout:
        return []
    try:
        fields = json.loads(stdout).get("lscpu", [])
    except ValueError:
        return []
    models = []
    while fields:
        field = fields.pop(0)
        fields.extend(field.get("children", []))
        if field.get("field") == "Model name:":
            models.append(field.get("data") or "")
    return _unique(models)


def get_cpu_name(cpuinfo_path="/proc/cpuinfo", cpu_path="/sys/devices/system/cpu", lscpu=True):
    """Get a human readable CPU name, or an empty string if it is unknown

    x86 exposes "model name" in /proc/cpuinfo, but ARM64 kernels don't,
    so the core names are taken from the device tree, then from lscpu.
    """
    cpuinfo = _read(cpuinfo_path)
    names = (
        _cpuinfo_values(cpuinfo, "model name")
        or _sysfs_cores(cpu_path)
        or (_lscpu_models() if lscpu else [])
        or _cpuinfo_values(cpuinfo, "hardware")
        or _cpuinfo_values(cpuinfo, "model")
    )
    return ", ".join(names)
