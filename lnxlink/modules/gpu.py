import pyamdgpuinfo
import nvsmi
from shutil import which


class Addon():

    def __init__(self, lnxlink):
        self.name = 'GPU'
        self.gpu_ids = {
            "amd": pyamdgpuinfo.detect_gpus()
        }
        if which("nvidia-smi") is not None:
            self.gpu_ids["nvidia"] = len(list(nvsmi.get_gpus()))
        else:
            self.gpu_ids["nvidia"] = 0

    def getControlInfo(self):
        gpus = {}
        for gpu_id in range(self.gpu_ids['amd']):
            amd_gpu = pyamdgpuinfo.get_gpu(gpu_id)
            gpus[f"amd_{gpu_id}"] = {
                "name": amd_gpu.name,
                "VRAM usage": amd_gpu.query_vram_usage(),
                "GTT usage": amd_gpu.query_gtt_usage(),
                "Temperature": amd_gpu.query_temperature(),
                "load": min(100, amd_gpu.query_load() * 100),
                "Power": amd_gpu.query_power(),
                "Voltage": amd_gpu.query_graphics_voltage(),
            }
        for gpu_id in range(self.gpu_ids['nvidia']):
            nvidia_gpu = list(nvsmi.get_gpus())[gpu_id]
            gpus[f"nvidia_{gpu_id}"] = {
                "name": nvidia_gpu.name,
                "Memory usage": round(nvidia_gpu.mem_util, 1),
                "load": min(100, round(nvidia_gpu.gpu_util, 1)),
                "Temperature": nvidia_gpu.temperature,
            }
        return gpus

    def exposedControls(self):
        discovery_info = {}
        for gpu_id in range(self.gpu_ids['amd']):
            discovery_info[f"GPU AMD {gpu_id}"] = {
                "type": "sensor",
                "icon": "mdi:expansion-card-variant",
                "unit": "%",
                "state_class": "measurement",
                "value_template": f"{{{{ value_json.amd_{gpu_id}.load }}}}",
                "enabled": True,
            }
        for gpu_id in range(self.gpu_ids['nvidia']):
            discovery_info[f"GPU NVIDIA {gpu_id}"] = {
                "type": "sensor",
                "icon": "mdi:expansion-card-variant",
                "unit": "%",
                "state_class": "measurement",
                "value_template": f"{{{{ value_json.nvidia_{gpu_id}.load }}}}",
                "enabled": True,
            }
        return discovery_info
