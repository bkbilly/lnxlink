import psutil

class Addon():
    name = 'CPU Usage'
    icon = 'mdi:speedometer'
    unit = '%'
    state_class = 'measurement'

    def getInfo(self):
        return psutil.cpu_percent()
