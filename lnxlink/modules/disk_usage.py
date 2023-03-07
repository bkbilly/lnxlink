import psutil


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Disk Usage'
        self.sensor_type = 'sensor'
        self.icon = 'mdi:harddisk'

    def getInfo(self) -> dict:
        disks = {"status": False}
        for disk in psutil.disk_partitions():
            if disk.fstype == 'squashfs':
                continue
            disks[disk.device] = {}
            disk_stats = psutil.disk_usage(disk.mountpoint)
            disks[disk.device]["total"] = self._bytetomb(disk_stats.total)
            disks[disk.device]["used"] = self._bytetomb(disk_stats.used)
            disks[disk.device]["free"] = self._bytetomb(disk_stats.free)
            disks[disk.device]["percent"] = disk_stats.percent
            if disk_stats.percent > 80:
                disks["status"] = True
        return disks

    def _bytetomb(self, byte):
        return round(byte / 1024 / 1024, 1)
