"""Gets GPU information"""
import logging
from shutil import which
import pyamdgpuinfo
import nvsmi

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "GPU"
        self.gpu_ids = {"amd": pyamdgpuinfo.detect_gpus()}
        if which("nvidia-smi") is not None:
            try:
                self.gpu_ids["nvidia"] = len(list(nvsmi.get_gpus()))
            except Exception as err:
                logger.error("Found nvidia-smi, but there was an error: %s", err)
                self.gpu_ids["nvidia"] = 0
        else:
            self.gpu_ids["nvidia"] = 0

    def get_info(self):
        """Gather information from the system"""
        gpus = {}
        for gpu_id in range(self.gpu_ids["amd"]):
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
        for gpu_id in range(self.gpu_ids["nvidia"]):
            nvidia_gpu = list(nvsmi.get_gpus())[gpu_id]
            gpus[f"nvidia_{gpu_id}"] = {
                "name": nvidia_gpu.name,
                "Memory usage": round(nvidia_gpu.mem_util, 1),
                "load": min(100, round(nvidia_gpu.gpu_util, 1)),
                "Temperature": nvidia_gpu.temperature,
            }
        return gpus

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {}
        for gpu_id in range(self.gpu_ids["amd"]):
            discovery_info[f"GPU AMD {gpu_id}"] = {
                "type": "sensor",
                "icon": "mdi:expansion-card-variant",
                "unit": "%",
                "state_class": "measurement",
                "value_template": f"{{{{ value_json.amd_{gpu_id}.load }}}}",
                "attributes_template": f"{{{{ value_json.amd_{gpu_id} | tojson }}}}",
                "enabled": True,
            }
        for gpu_id in range(self.gpu_ids["nvidia"]):
            discovery_info[f"GPU NVIDIA {gpu_id}"] = {
                "type": "sensor",
                "icon": "mdi:expansion-card-variant",
                "unit": "%",
                "state_class": "measurement",
                "value_template": f"{{{{ value_json.nvidia_{gpu_id}.load }}}}",
                "attributes_template": f"{{{{ value_json.nvidia_{gpu_id} | tojson }}}}",
                "enabled": True,
            }
        return discovery_info
