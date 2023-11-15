"""Gets GPU information"""
import re
import math
import logging
from shutil import which
from .scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "GPU"
        self.lnxlink = lnxlink
        self._requirements()
        self.gpu_ids = {"amd": self.lib["amd"].detect_gpus()}
        if which("nvidia-smi") is not None:
            try:
                self.gpu_ids["nvidia"] = len(list(self.lib["nvidia"].get_gpus()))
            except Exception as err:
                logger.error("Found nvidia-smi, but there was an error: %s", err)
                self.gpu_ids["nvidia"] = 0
        else:
            self.gpu_ids["nvidia"] = 0

    def _requirements(self):
        self.lib = {
            "amd": import_install_package("pyamdgpuinfo", ">=2.1.4"),
            "nvidia": import_install_package("nvsmi", ">=0.4.2"),
        }

    def get_info(self):
        """Gather information from the system"""
        gpus = {}
        for gpu_id in range(self.gpu_ids["amd"]):
            amd_gpu = self.lib["amd"].get_gpu(gpu_id)
            gpus[f"amd_{gpu_id}"] = {
                "Name": amd_gpu.name,
                "VRAM usage": amd_gpu.query_vram_usage(),
                "GTT usage": amd_gpu.query_gtt_usage(),
                "Temperature": amd_gpu.query_temperature(),
                "load": min(100, amd_gpu.query_load() * 100),
                "Power": amd_gpu.query_power(),
                "Voltage": amd_gpu.query_graphics_voltage(),
            }
        for gpu_id in range(self.gpu_ids["nvidia"]):
            nvidia_gpu = list(self.lib["nvidia"].get_gpus())[gpu_id]
            gpu_util = nvidia_gpu.gpu_util
            gpu_util = self._older_gpu_load(gpu_id, gpu_util)
            gpus[f"nvidia_{gpu_id}"] = {
                "Name": nvidia_gpu.name,
                "Memory usage": round(nvidia_gpu.mem_util, 1),
                "load": gpu_util,
                "Temperature": nvidia_gpu.temperature,
            }
        return gpus

    def _older_gpu_load(self, gpu_id, gpu_util):
        """For older GPUs, use nvidia-settings to get gpu usage"""
        if math.isnan(gpu_util):
            gpu_util = None
            if which("nvidia-settings") is not None:
                display = self.lnxlink.display
                if display:
                    settings_out, _, _ = syscommand(
                        f"nvidia-settings -q '[gpu:{gpu_id}]/GPUUtilization' --display {display}"
                    )
                    match = re.findall(r"graphics=(\d+)", settings_out)
                    if match:
                        gpu_util = int(match[0])
            else:
                logger.error(
                    "Older NVIDIA GPUs need nvidia-settings which is not installed."
                )
        return gpu_util

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
