"""Gets disk usage from all disks"""
import logging

import psutil

logger = logging.getLogger("lnxlink")


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
            att_temp = f"{{{{ value_json.get('{device}', {{}}).get('attributes', {{}}) | tojson }}}}"
            discovery_info[f"Disk {device}"] = {
                "type": "sensor",
                "icon": "mdi:harddisk",
                "unit": "%",
                "state_class": "measurement",
                "value_template": f"{{{{ value_json.get('{device}', {{}}).get('percent') }}}}",
                "attributes_template": att_temp,
                "enabled": True,
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        disks = self._get_disks()
        mounted = set(disks) - set(self.disks)
        unmounted = set(self.disks) - set(disks)
        for disk_name in unmounted:
            disks[disk_name] = self.disks[disk_name]
            self.disks[disk_name]["attributes"]["connected"] = False
            self.disks[disk_name]["percent"] = None
        self.disks = disks
        if len(mounted) > 0:
            self.lnxlink.setup_discovery()
        return self.disks

    def _bytetomb(self, byte):
        return round(byte / 1024 / 1024, 0)

    def _get_disks(self):
        """Get a list of all disks"""
        disks = {}
        for disk in psutil.disk_partitions():
            matches = [
                "/snap/",
                "/docker/overlay",
                "/docker/btrfs",
            ]
            if any(x in disk.mountpoint for x in matches):
                continue
            if disk.fstype == "squashfs":
                continue

            try:
                disk_stats = psutil.disk_usage(disk.mountpoint)
                device = disk.device.replace("/", "_").strip("_")
                disks[device] = {}
                disks[device]["percent"] = disk_stats.percent
                disks[device]["attributes"] = {}
                disks[device]["attributes"]["total"] = self._bytetomb(disk_stats.total)
                disks[device]["attributes"]["used"] = self._bytetomb(disk_stats.used)
                disks[device]["attributes"]["free"] = self._bytetomb(disk_stats.free)
                disks[device]["attributes"]["connected"] = True
                disks[device]["attributes"]["mountpoint"] = disk.mountpoint
            except Exception as err:
                logger.error(
                    "Error with disk usage [fstype: %s, device: %s, mountpoint: %s]: %s",
                    disk.fstype,
                    disk.device,
                    disk.mountpoint,
                    err,
                )
        return disks
