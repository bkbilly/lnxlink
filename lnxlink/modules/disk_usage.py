"""Gets disk usage from all disks"""
import psutil


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Disk Usage"
        self.lnxlink = lnxlink
        self.disks = self._get_disks()

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for device in self.disks:
            discovery_info[f"Disk {device}"] = {
                "type": "sensor",
                "icon": "mdi:harddisk",
                "unit": "%",
                "state_class": "measurement",
                "value_template": f"{{{{ value_json.{device}.percent }}}}",
                "attributes_template": f"{{{{ value_json.{device} | tojson }}}}",
                "enabled": True,
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        disks = self._get_disks()
        mounted = set(disks) - set(self.disks)
        unmounted = set(self.disks) - set(disks)
        # print(mounted, unmounted)
        for disk_name in unmounted:
            disks[disk_name] = self.disks[disk_name]
            self.disks[disk_name]['connected'] = False
        self.disks = disks
        for disk_name in mounted:
            self.lnxlink.setup_discovery()
        return self.disks

    def _bytetomb(self, byte):
        return round(byte / 1024 / 1024, 1)

    def _get_disks(self):
        """Get a list of all disks"""
        disks = {}
        for disk in psutil.disk_partitions():
            if disk.fstype == "squashfs":
                continue
            if "docker/overlay" in disk.mountpoint:
                continue
            device = disk.device.replace("/", "_").strip("_")
            disks[device] = {}
            disk_stats = psutil.disk_usage(disk.mountpoint)
            disks[device]["total"] = self._bytetomb(disk_stats.total)
            disks[device]["used"] = self._bytetomb(disk_stats.used)
            disks[device]["free"] = self._bytetomb(disk_stats.free)
            disks[device]["percent"] = disk_stats.percent
            disks[device]["connected"] = True
        return disks
