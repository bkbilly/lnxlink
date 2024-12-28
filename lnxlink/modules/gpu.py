"""Gets GPU information"""
import re
import math
import logging
from shutil import which
from lnxlink.modules.scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "GPU"
        self.lnxlink = lnxlink
        self._requirements()
        self.gpu_ids = {"amd": 0}
        self.nvitop_devices = []
        try:
            self.gpu_ids["amd"] = self.lib["amd"].detect_gpus()
        except Exception as err:
            logger.error("Can't get AMD GPU: %s", err)
        if which("nvidia-smi") is not None:
            try:
                self.gpu_ids["nvidia"] = len(list(self.lib["nvidia"].get_gpus()))
            except Exception as err:
                logger.error("Found nvidia-smi, but there was an error: %s", err)
                self.gpu_ids["nvidia"] = 0
        else:
            self.gpu_ids["nvidia"] = 0
        if self.gpu_ids["amd"] == 0 and self.gpu_ids["nvidia"] == 0:
            self.nvitop_devices = self.lib["nvitop"].Device.all()
            if len(self.nvitop_devices) == 0:
                raise SystemError("No GPU found")

    def _requirements(self):
        self.lib = {
            "amd": import_install_package("pyamdgpuinfo", ">=2.1.4"),
            "nvidia": import_install_package("nvsmi", ">=0.4.2"),
            "nvitop": import_install_package("nvitop", ">=1.3.2"),
        }

    def get_info(self):
        """Gather information from the system"""
        gpus = {}
        for gpu_id in range(self.gpu_ids["amd"]):
            amd_gpu = self.lib["amd"].get_gpu(gpu_id)
            gpus[f"amd_{gpu_id}"] = {
                "load": min(100, amd_gpu.query_load() * 100),
                "attributes": {
                    "Name": amd_gpu.name,
                    "VRAM usage": amd_gpu.query_vram_usage(),
                    "GTT usage": amd_gpu.query_gtt_usage(),
                    "Temperature": amd_gpu.query_temperature(),
                    "Power": amd_gpu.query_power(),
                    "Voltage": amd_gpu.query_graphics_voltage(),
                },
            }
        for gpu_id in range(self.gpu_ids["nvidia"]):
            nvidia_gpu = list(self.lib["nvidia"].get_gpus())[gpu_id]
            gpu_util = nvidia_gpu.gpu_util
            gpu_util = self._older_gpu_load(gpu_id, gpu_util)
            gpus[f"nvidia_{gpu_id}"] = {
                "load": gpu_util,
                "memory": round(nvidia_gpu.mem_util, 0),
                "temperature": nvidia_gpu.temperature,
                "attributes": {
                    "Name": nvidia_gpu.name,
                },
            }
        for device in self.nvitop_devices:
            gpus[f"gpu_{device.index}"] = {
                "load": device.gpu_utilization(),
                "memory": device.memory_utilization(),
                "temperature": device.temperature(),
                "attributes": {
                    "Name": device.name(),
                },
            }

        return gpus

    def _older_gpu_load(self, gpu_id, gpu_util):
        """For older GPUs, use nvidia-settings to get gpu usage"""
        if math.isnan(gpu_util):
            gpu_util = None
            display = self.lnxlink.display
            if display:
                if which("nvidia-settings") is not None:
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
                "attributes_template": f"{{{{ value_json.amd_{gpu_id}.attributes | tojson }}}}",
                "enabled": True,
            }
        for gpu_id in range(self.gpu_ids["nvidia"]):
            for expose, unit in (("load", "%"), ("memory", "%"), ("temperature", "°C")):
                discovery_info[f"GPU NVIDIA {gpu_id} {expose}"] = {
                    "type": "sensor",
                    "icon": "mdi:expansion-card-variant",
                    "unit": unit,
                    "state_class": "measurement",
                    "value_template": f"{{{{ value_json.nvidia_{gpu_id}.{expose} }}}}",
                    "attributes_template": f"{{{{ value_json.nvidia_{gpu_id}.attributes | tojson }}}}",
                    "enabled": True,
                }
        for device in self.nvitop_devices:
            index = device.index
            for expose, unit in (("load", "%"), ("memory", "%"), ("temperature", "°C")):
                discovery_info[f"GPU {index} {expose}"] = {
                    "type": "sensor",
                    "icon": "mdi:expansion-card-variant",
                    "unit": unit,
                    "state_class": "measurement",
                    "value_template": f"{{{{ value_json.gpu_{index}.{expose} }}}}",
                    "attributes_template": f"{{{{ value_json.gpu_{index}.attributes | tojson }}}}",
                    "enabled": True,
                }

        return discovery_info
