import psutil
from datetime import datetime


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Network Download'
        self.sensor_type = 'sensor'
        self.icon = 'mdi:access-point-network'
        self.unit = 'Mbit/s'
        self.state_class = 'measurement'
        self.timeOld = datetime.now()
        self.recvOld = psutil.net_io_counters().bytes_recv

    def getInfo(self) -> int:
        """ Returns Mbps"""
        timeNew = datetime.now()
        recvNew = psutil.net_io_counters().bytes_recv

        timeDiff = (timeNew - self.timeOld).total_seconds()
        recvDiff = recvNew - self.recvOld

        self.timeOld = timeNew
        self.recvOld = recvNew

        recvSpeed = round(recvDiff * 8 / timeDiff / 1024 / 1024, 2)

        return recvSpeed
