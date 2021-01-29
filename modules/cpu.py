import psutil

class Addon():
    service = 'cpu'
    name = 'CPU Usage'
    icon = 'mdi:cpu'
    unit = '%'

    def getInfo(self):
        return psutil.cpu_percent()
