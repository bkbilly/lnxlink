import glob


class Addon():
    name = 'Microphone used'
    icon = 'mdi:microphone'
    sensor_type = 'binary_sensor'
    unit = ''

    def getInfo(self):
        mics = glob.glob('/proc/asound/**/*c/sub*/status', recursive=True)
        for mic in mics:
            with open(mic) as mic_content:
                mic_status = mic_content.read().strip().lower()
                if mic_status != 'closed':
                    return "ON"
        return "OFF"
