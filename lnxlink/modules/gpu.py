"""Monitor load and usage for NVIDIA, AMD, or Intel graphics cards"""
import json
import logging
import math
import os
import re
import subprocess
import threading
import time
from shutil import which

from lnxlink.modules.scripts.helpers import (
    get_display_variable,
    import_install_package,
    syscommand,
)

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "GPU"
        self.lnxlink = lnxlink
        self._requirements()
        self.gpu_ids = {"amd": 0, "nvidia": 0, "intel": 0}
        self.nvitop_devices = []
        self.intel_gpu_data = {}
        self.intel_process = None

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

        if which("intel_gpu_top") is not None:
            # pylint: disable=consider-using-with
            self.intel_process = subprocess.Popen(
                ["sudo", "-n", "intel_gpu_top", "-s", "1000", "-J"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            time.sleep(0.2)
            if (
                self.intel_process.poll() is not None
                and self.intel_process.returncode != 0
            ):
                stderr_out = ""
                if self.intel_process.stderr:
                    stderr_out = self.intel_process.stderr.read().strip()
                err_msg = (
                    f"Intel GPU permission issue: {stderr_out}\n"
                    "Please add the following to /etc/sudoers using 'sudo visudo':\n"
                    f"{self._get_username()} ALL=(ALL) NOPASSWD: {which('intel_gpu_top')}"
                )
                logger.error(err_msg)
                self.gpu_ids["intel"] = 0
            else:
                threading.Thread(target=self._read_intel_gpu_top, daemon=True).start()
                self.gpu_ids["intel"] = 1

        if (
            self.gpu_ids["amd"] == 0
            and self.gpu_ids["nvidia"] == 0
            and self.gpu_ids["intel"] == 0
        ):
            self.nvitop_devices = self.lib["nvitop"].Device.all()
            if len(self.nvitop_devices) == 0:
                raise SystemError("No GPU found")

    def _requirements(self):
        self.lib = {
            "amd": import_install_package("pyamdgpuinfo", ">=2.1.4"),
            "nvidia": import_install_package("nvsmi", ">=0.4.2"),
            "nvitop": import_install_package("nvitop", ">=1.3.2"),
        }

    def _get_username(self):
        """Get the current username"""
        return os.getenv("USER", os.getenv("USERNAME", "user"))

    def _read_intel_gpu_top(self):
        """Continuously read JSON stream from intel_gpu_top"""
        buffer = ""
        if self.intel_process.stdout is None:
            return

        for line in self.intel_process.stdout:
            line_str = line.strip()
            if line_str in ("[", "]"):
                continue
            buffer += line_str
            cleaned = buffer.rstrip(",")
            try:
                data = json.loads(cleaned)
                self.intel_gpu_data = data
                buffer = ""
            except json.JSONDecodeError:
                if len(buffer) > 10000:
                    buffer = ""

    def _get_intel_info(self, gpu_id):
        """Get information for Intel GPU"""
        engines = self.intel_gpu_data.get("engines", {})
        engine_busy = [
            val.get("busy", 0)
            for val in engines.values()
            if isinstance(val, dict) and "busy" in val
        ]
        load = max(engine_busy, default=0)

        attributes = {"Name": "Intel GPU"}
        frequency = self.intel_gpu_data.get("frequency", {})
        if "actual" in frequency:
            attributes["Frequency"] = f"{round(frequency['actual'], 1)} MHz"

        power = self.intel_gpu_data.get("power", {})
        if "GPU" in power:
            attributes["Power GPU"] = f"{round(power['GPU'], 2)} W"
        if "Package" in power:
            attributes["Power Package"] = f"{round(power['Package'], 2)} W"

        rc6 = self.intel_gpu_data.get("rc6", {})
        if "value" in rc6:
            attributes["RC6"] = f"{round(rc6['value'], 1)} %"

        imc = self.intel_gpu_data.get("imc-bandwidth", {})
        if "reads" in imc:
            attributes["IMC Reads"] = f"{round(imc['reads'], 1)} MiB/s"
        if "writes" in imc:
            attributes["IMC Writes"] = f"{round(imc['writes'], 1)} MiB/s"

        for engine_name, engine_val in engines.items():
            if isinstance(engine_val, dict) and "busy" in engine_val:
                attributes[
                    f"Engine {engine_name}"
                ] = f"{round(engine_val['busy'], 1)} %"

        return f"intel_{gpu_id}", {
            "load": round(load, 1),
            "attributes": attributes,
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
        for gpu_id in range(self.gpu_ids["intel"]):
            key, val = self._get_intel_info(gpu_id)
            gpus[key] = val
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
            display = get_display_variable()
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
        for gpu_id in range(self.gpu_ids["intel"]):
            discovery_info[f"GPU Intel {gpu_id}"] = {
                "type": "sensor",
                "icon": "mdi:expansion-card-variant",
                "unit": "%",
                "state_class": "measurement",
                "value_template": f"{{{{ value_json.intel_{gpu_id}.load }}}}",
                "attributes_template": f"{{{{ value_json.intel_{gpu_id}.attributes | tojson }}}}",
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
