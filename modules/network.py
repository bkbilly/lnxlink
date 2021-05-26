import psutil
from datetime import datetime

class Addon():
    service = 'network'
    name = 'Network'
    icon = 'mdi:speedometer'
    unit = 'Mbps'

    def __init__(self):
        self.timeOld = datetime.now()
        self.sentOld = psutil.net_io_counters().bytes_sent
        self.recvOld = psutil.net_io_counters().bytes_recv

    def getInfo(self):
        """ Returns Mbps"""
        timeNew = datetime.now()
        sentNew = psutil.net_io_counters().bytes_sent
        recvNew = psutil.net_io_counters().bytes_recv


        timeDiff = (timeNew - self.timeOld).total_seconds()
        sentDiff = sentNew - self.sentOld
        recvDiff = recvNew - self.recvOld
        
        self.timeOld = timeNew
        self.sentOld = sentNew
        self.recvOld = recvNew

        sentsSpeed = round(sentDiff * 8 / timeDiff / 1024 / 1024, 2)
        recvSpeed = round(recvDiff * 8 / timeDiff / 1024 / 1024, 2)

        return {'download': recvSpeed, 'upload': sentsSpeed}
