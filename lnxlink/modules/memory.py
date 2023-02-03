import psutil


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Memory Usage'
        self.sensor_type = 'sensor'
        self.icon = 'mdi:memory'
        self.unit = '%'
        self.state_class = 'measurement'

    def getInfo(self):
        return psutil.virtual_memory().percent
