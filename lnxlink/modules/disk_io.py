"""Measure read/write throughput for each physical disk"""
import glob
from timeit import default_timer as timer


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "DiskIO"
        self.lnxlink = lnxlink
        self.lnxlink.add_settings(
            "disk_io",
            {
                "include_disks": [],
                "exclude_disks": [],
            },
        )
        self.disks = self._get_disks()
        self.last_stats = {}
        for disk in self.disks:
            ticks = self._read_io_ticks(disk)
            if ticks is not None:
                self.last_stats[disk] = (ticks, timer())

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for disk in self.disks:
            discovery_info[f"Disk IO {disk}"] = {
                "type": "sensor",
                "icon": "mdi:barcode-scan",
                "unit": "%",
                "entity_category": "diagnostic",
                "state_class": "measurement",
                "value_template": f"{{{{ value_json.get('{disk}') }}}}",
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        disks = self._get_disks()
        if self.disks != disks:
            self.disks = disks
            self.lnxlink.setup_discovery("disk_io")

        cur_time = timer()
        results = {}
        for disk in self.disks:
            cur_ticks = self._read_io_ticks(disk)
            if cur_ticks is None:
                continue
            if disk in self.last_stats:
                last_ticks, last_time = self.last_stats[disk]
                totaltime = cur_time - last_time
                if totaltime > 0:
                    utilization = (cur_ticks - last_ticks) / totaltime / 10
                    utilization = min(max(0, utilization), 100)
                    results[disk] = int(round(utilization, 0))
                else:
                    results[disk] = 0
            else:
                results[disk] = 0
            self.last_stats[disk] = (cur_ticks, cur_time)

        return results

    def _read_io_ticks(self, disk):
        """Read io_ticks from /sys/block/{disk}/stat"""
        try:
            with open(f"/sys/block/{disk}/stat", encoding="UTF-8") as file:
                parts = file.read().split()
                if len(parts) >= 10:
                    return int(parts[9])
        except (OSError, ValueError):
            pass
        return None

    def _get_disks(self):
        """Get a list of all disks"""
        disks = []
        disk_includes = (
            self.lnxlink.config["settings"].get("disk_io", {}).get("include_disks", [])
        )
        disk_excludes = (
            self.lnxlink.config["settings"].get("disk_io", {}).get("exclude_disks", [])
        )

        for disk in glob.glob("/sys/block/*", recursive=False):
            disk_name = disk.removeprefix("/sys/block/")

            # Built-in excludes for virtual/pseudo devices
            excludes = ["loop", "ram", "zram"]
            if any(disk_name.startswith(x) for x in excludes):
                continue

            # User-defined include filter
            if disk_includes:
                if not any(disk_name.startswith(x) for x in disk_includes):
                    continue

            # User-defined exclude filter
            if disk_excludes:
                if any(disk_name.startswith(x) for x in disk_excludes):
                    continue

            disks.append(disk_name)
        return disks
