import subprocess
import pyamdgpuinfo

class Addon():

    def __init__(self, lnxlink):
        self.name = 'AMD GPU'
        self.sensor_type = 'sensor'
        self.icon = 'mdi:expansion-card-variant'

    def getInfo(self) -> dict:
        first_gpu = pyamdgpuinfo.get_gpu(0)                        # we'll ignore extra GPUs
        
        gpu_status = {}

        gpu_status["VRAM usage"] = first_gpu.query_vram_usage()
        gpu_status["GTT usage"] = first_gpu.query_gtt_usage()
        gpu_status["Temperature"] = first_gpu.query_temperature()
        gpu_status["Load"] = first_gpu.query_load()*100            # pyamdgpuinfo returns value between 0 and 1
        gpu_status["Power"] = first_gpu.query_power()
        gpu_status["Voltage"] = first_gpu.query_graphics_voltage()

        gpu_status["status"] = first_gpu.name

        return gpu_status
