import psutil

class Addon():
    service = 'memory'
    name = 'Memory Usage'
    icon = 'mdi:memory'
    unit = '%'

    def getInfo(self):
        return psutil.virtual_memory().percent
