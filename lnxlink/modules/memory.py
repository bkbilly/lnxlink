import psutil

class Addon():
    name = 'Memory Usage'
    icon = 'mdi:memory'
    unit = '%'
    state_class = 'measurement'

    def getInfo(self):
        return psutil.virtual_memory().percent
