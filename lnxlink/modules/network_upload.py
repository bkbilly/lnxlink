import psutil
from datetime import datetime


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Network Upload'
        self.sensor_type = 'sensor'
        self.icon = 'mdi:access-point-network'
        self.unit = 'Mbit/s'
        self.state_class = 'measurement'
        self.timeOld = datetime.now()
        self.sentOld = psutil.net_io_counters().bytes_sent

    def getInfo(self) -> int:
        """ Returns Mbps"""
        timeNew = datetime.now()
        sentNew = psutil.net_io_counters().bytes_sent

        timeDiff = (timeNew - self.timeOld).total_seconds()
        sentDiff = sentNew - self.sentOld

        self.timeOld = timeNew
        self.sentOld = sentNew

        sentsSpeed = round(sentDiff * 8 / timeDiff / 1024 / 1024, 2)

        return sentsSpeed
