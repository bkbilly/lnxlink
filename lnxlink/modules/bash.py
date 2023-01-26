import subprocess


class Addon():
    name = 'bash'

    def exposedControls(self):
        return {
            "Bash_Command": {
                "type": "text",
                "icon": "mdi:bash",
            }
        }

    def startControl(self, topic, data):
        subprocess.call(f"{data}", shell=True)
