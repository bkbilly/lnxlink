import psutil

class Addon():
    name = 'Memory Usage'
    icon = 'mdi:memory'
    unit = '%'

    def getInfo(self):
        return psutil.virtual_memory().percent
