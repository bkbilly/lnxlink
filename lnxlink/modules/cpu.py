import psutil


class Addon():

    def __init__(self, lnxlink):
        self.name = 'CPU Usage'
        self.sensor_type = 'sensor'
        self.icon = 'mdi:speedometer'
        self.unit = '%'
        self.state_class = 'measurement'

    def getInfo(self):
        return psutil.cpu_percent()
