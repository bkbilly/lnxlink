import glob
import subprocess
import json
import re


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Microphone used'
        self.icon = 'mdi:microphone'
        self.sensor_type = 'binary_sensor'

        self.use_pactl = subprocess.run(
            f"which pactl && pactl -f json list short source-outputs",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).returncode == 0


    def getInfo(self):
        if self.use_pactl:
            stdout = subprocess.run(f"pactl -f json list short source-outputs", shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE).stdout.decode("UTF-8")
            # Replace 0,00 values with 0.00
            stdout = re.sub(r'(\s*[+-]?[0-9]+),([0-9]+\s*)',r'\1.\2', stdout)
            data = json.loads(stdout)
            if len(data) > 0:
                return 'ON'
            return "OFF"
        else:
            mics = glob.glob('/proc/asound/**/*c/sub*/status', recursive=True)
            for mic in mics:
                with open(mic) as mic_content:
                    mic_status = mic_content.read().strip().lower()
                    if mic_status != 'closed':
                        return "ON"
            return "OFF"
