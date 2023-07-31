import subprocess


class Addon():

    def __init__(self, lnxlink):
        self.name = 'bash'

    def exposedControls(self):
        return {
            "Bash_Command": {
                "type": "text",
                "icon": "mdi:bash",
            }
        }

    def startControl(self, topic, data):
        stdout = subprocess.run(
            data,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        return stdout
