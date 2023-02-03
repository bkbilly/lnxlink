import glob


class Addon():

    def __init__(self, lnxlink):
        self.name = 'Microphone used'
        self.icon = 'mdi:microphone'
        self.sensor_type = 'binary_sensor'

    def getInfo(self):
        mics = glob.glob('/proc/asound/**/*c/sub*/status', recursive=True)
        for mic in mics:
            with open(mic) as mic_content:
                mic_status = mic_content.read().strip().lower()
                if mic_status != 'closed':
                    return "ON"
        return "OFF"
