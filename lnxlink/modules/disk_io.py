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
        self.disk_info = {disk: _disk_info(disk) for disk in self.disks}
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
                "attributes_template": (
                    f"{{{{ value_json.get('attributes', {{}}).get('{disk}', {{}})"
                    " | tojson }}"
                ),
            }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        disks = self._get_disks()
        if self.disks != disks:
            self.disks = disks
            self.disk_info = {disk: _disk_info(disk) for disk in self.disks}
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

        results["attributes"] = self.disk_info
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


def _read(path):
    """Read a sysfs text file with collapsed whitespace, or "" when missing"""
    try:
        with open(path, encoding="utf-8", errors="replace") as file:
            return " ".join(file.read().split())
    except OSError:
        return ""


def _vpd_serial(path):
    """Serial number from the SCSI VPD page 0x80 (4-byte header, then serial)"""
    try:
        with open(path, "rb") as file:
            data = file.read()
    except OSError:
        return ""
    if len(data) < 4:
        return ""
    serial = data[4 : 4 + data[3]].decode("ascii", errors="replace")
    return " ".join(serial.split())


def _format_size(num_bytes):
    """Format bytes using decimal units, as disk vendors do (e.g. 18 TB)"""
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1000 or unit == "PB":
            break
        size /= 1000
    size = round(size, 1)
    if size.is_integer():
        size = int(size)
    return f"{size} {unit}"


def _disk_info(disk):
    """Static information about a disk from /sys/block/{disk}

    Keys that are not available for the device are left out:
    NVMe has no vendor, SD cards use name/fwrev, SCSI/SATA disks
    expose the serial number only through the VPD page 0x80.
    """
    base = f"/sys/block/{disk}"
    device = f"{base}/device"
    try:
        # /sys/block/*/size is always in 512-byte sectors
        size_bytes = int(_read(f"{base}/size")) * 512
    except ValueError:
        size_bytes = 0
    info = {
        "Vendor": _read(f"{device}/vendor"),
        "Model": _read(f"{device}/model") or _read(f"{device}/name"),
        "Size": _format_size(size_bytes) if size_bytes > 0 else "",
        "Serial": _read(f"{device}/serial") or _vpd_serial(f"{device}/vpd_pg80"),
        "Firmware": (
            _read(f"{device}/firmware_rev")
            or _read(f"{device}/rev")
            or _read(f"{device}/fwrev")
        ),
    }
    return {key: value for key, value in info.items() if value}
