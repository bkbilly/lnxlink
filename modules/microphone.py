import glob


class Addon():
    service = 'microphone'
    name = 'Microphone used'
    icon = 'mdi:microphone'
    unit = ''

    def getInfo(self):
        mics = glob.glob('/proc/asound/**/*c/sub*/status', recursive=True)
        for mic in mics:
            with open(mic) as mic_content:
                mic_status = mic_content.read().strip().lower()
                if mic_status != 'closed':
                    return True
        return False
