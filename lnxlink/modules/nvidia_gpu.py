import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Nvidia GPU'
        self.sensor_type = 'sensor'
        self.icon = 'mdi:expansion-card-variant'

    def getInfo(self) -> dict:
        stdout = subprocess.run(
            ['nvidia-smi',
             '--query-gpu=driver_version,name,fan.speed,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,temperature.gpu,power.draw,clocks.current.graphics',
             '--format=csv,nounits'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8").strip().split('\n')
        # stdout = map(int, stdout.split(','))
        headers = stdout[0].split(', ')
        values = stdout[1].split(', ')

        gpu_status = {}
        for num, header in enumerate(headers):
            gpu_status[header] = values[num]
        gpu_status['status'] = gpu_status['name']
        return gpu_status
