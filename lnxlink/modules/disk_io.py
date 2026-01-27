"""Measure read/write throughput for each physical disk"""
import glob
import asyncio
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

        self.stat_items = [
            "read IOs",
            "read merges",
            "read sectors",
            "read ticks",
            "write IOs",
            "write merges",
            "write sectors",
            "write ticks",
            "in_flight",
            "io_ticks",
            "time_in_queue",
            "discard IOs",
            "discard merges",
            "discard sectors",
            "discard ticks",
            "flush IOs",
            "flush ticks",
        ]

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
        results = asyncio.run(self._get_info_async())
        return results

    async def _get_info_async(self):
        features = []
        for disk in self.disks:
            features.append(self._run_check(disk))
        gathers = await asyncio.gather(*features)
        results = {}
        for disk, utilization in gathers:
            results[disk] = utilization
        return results

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
            if len(disk_includes) != 0:
                if not any(disk_name.startswith(x) for x in disk_includes):
                    continue

            # User-defined exclude filter
            if len(disk_excludes) != 0:
                if any(disk_name.startswith(x) for x in disk_excludes):
                    continue

            disks.append(disk_name)
        return disks

    async def _run_check(self, disk):
        with open(f"/sys/block/{disk}/stat", encoding="UTF-8") as file:
            pout1 = file.read()
        start = timer()
        await asyncio.sleep(0.1)
        with open(f"/sys/block/{disk}/stat", encoding="UTF-8") as file:
            pout2 = file.read()
        totaltime = timer() - start

        stats1 = dict(zip(self.stat_items, map(int, pout1.split())))
        stats2 = dict(zip(self.stat_items, map(int, pout2.split())))

        utilization = (stats2["io_ticks"] - stats1["io_ticks"]) / totaltime / 10
        utilization = min(utilization, 100)
        utilization = int(round(utilization, 0))
        return disk, utilization
