import psutil
from datetime import datetime


class Addon():
    name = 'Network Download'
    icon = 'mdi:access-point-network'
    unit = 'Mbit/s'

    def __init__(self):
        self.timeOld = datetime.now()
        self.recvOld = psutil.net_io_counters().bytes_recv

    def getInfo(self):
        """ Returns Mbps"""
        timeNew = datetime.now()
        recvNew = psutil.net_io_counters().bytes_recv

        timeDiff = (timeNew - self.timeOld).total_seconds()
        recvDiff = recvNew - self.recvOld

        self.timeOld = timeNew
        self.recvOld = recvNew

        recvSpeed = round(recvDiff * 8 / timeDiff / 1024 / 1024, 2)

        return recvSpeed
