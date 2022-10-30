import psutil
from datetime import datetime


class Addon():
    name = 'Network Upload'
    icon = 'mdi:access-point-network'
    unit = 'Mbit/s'

    def __init__(self):
        self.timeOld = datetime.now()
        self.sentOld = psutil.net_io_counters().bytes_sent

    def getInfo(self):
        """ Returns Mbps"""
        timeNew = datetime.now()
        sentNew = psutil.net_io_counters().bytes_sent

        timeDiff = (timeNew - self.timeOld).total_seconds()
        sentDiff = sentNew - self.sentOld

        self.timeOld = timeNew
        self.sentOld = sentNew

        sentsSpeed = round(sentDiff * 8 / timeDiff / 1024 / 1024, 2)

        return sentsSpeed
