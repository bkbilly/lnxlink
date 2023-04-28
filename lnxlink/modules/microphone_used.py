import glob
import subprocess
import json


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Microphone used'
        self.icon = 'mdi:microphone'
        self.sensor_type = 'binary_sensor'

        self.use_pactl = subprocess.run(
            f"which pactl && pactl -f json list",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).returncode == 0


    def getInfo(self):
        if self.use_pactl:
            stdout = subprocess.run(f"pactl -f json list", shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE).stdout.decode("UTF-8")
            data = json.loads(stdout)
            if 'source_outputs' in data and len(data['source_outputs']) > 0:
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
