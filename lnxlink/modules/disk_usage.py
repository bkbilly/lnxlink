import psutil


class Addon():
    name = 'Disk Usage'
    icon = 'mdi:harddisk'
    unit = 'json'

    def getInfo(self) -> dict:
        disks = {"status": False}
        for disk in psutil.disk_partitions():
            if disk.fstype == 'squashfs':
                continue
            disk_stats = psutil.disk_usage(disk.mountpoint)
            disks[f"total {disk.device}"] = self._bytetomb(disk_stats.total)
            disks[f"used {disk.device}"] = self._bytetomb(disk_stats.used)
            disks[f"free {disk.device}"] = self._bytetomb(disk_stats.free)
            disks[f"percent {disk.device}"] = disk_stats.percent
            if disk_stats.percent > 80:
                disks["status"] = True
        return disks

    def _bytetomb(self, byte):
        return round(byte / 1024 / 1024, 1)
