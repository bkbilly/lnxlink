import psutil
from datetime import datetime


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Network'
        self.timeOld = datetime.now()
        self.recvOld = psutil.net_io_counters().bytes_recv
        self.sentOld = psutil.net_io_counters().bytes_sent

    def exposedControls(self):
        return {
            "Network Upload": {
                "type": "sensor",
                "icon": "mdi:access-point-network",
                "unit": "Mbit/s",
                "state_class": "measurement",
                "device_class": "data_rate",
                "value_template": "{{ value_json.upload }}",
            },
            "Network Download": {
                "type": "sensor",
                "icon": "mdi:access-point-network",
                "unit": "Mbit/s",
                "state_class": "measurement",
                "device_class": "data_rate",
                "value_template": "{{ value_json.download }}",
            },
        }

    def getControlInfo(self):
        """ Returns Mbps"""
        timeNew = datetime.now()
        netio = psutil.net_io_counters()
        recvNew = netio.bytes_recv
        sentNew = netio.bytes_sent

        timeDiff = (timeNew - self.timeOld).total_seconds()
        self.timeOld = timeNew

        recvDiff = recvNew - self.recvOld
        sentDiff = sentNew - self.sentOld
        self.recvOld = recvNew
        self.sentOld = sentNew

        recvSpeed = round(recvDiff * 8 / timeDiff / 1024 / 1024, 2)
        sentSpeed = round(sentDiff * 8 / timeDiff / 1024 / 1024, 2)

        return {
            "upload": recvSpeed,
            "download": sentSpeed,
        }
