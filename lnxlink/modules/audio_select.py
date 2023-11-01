"""Information and control of pulseaudio devices"""
import logging
from .scripts.helpers import import_install_package

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Audio Select"
        self.lnxlink = lnxlink
        self.devices = {
            "speaker": {},
            "microphone": {},
            "defaults": {"microphone": "", "speaker": ""},
            "changed": False,
        }
        self._requirements()
        self._get_devices()

    def _requirements(self):
        self.lib = {
            "pulsectl": import_install_package("pulsectl", ">=23.5.2"),
        }

    def exposed_controls(self):
        """Exposes to home assistant"""
        discovery_info = {
            "Microphone Select": {
                "type": "select",
                "icon": "mdi:microphone-variant",
                "options": list(self.devices["microphone"].keys()),
                "value_template": "{{ value_json.microphone }}",
            },
            "Speaker Select": {
                "type": "select",
                "icon": "mdi:audio-input-rca",
                "options": list(self.devices["speaker"].keys()),
                "value_template": "{{ value_json.speaker }}",
            },
        }
        return discovery_info

    def get_info(self):
        """Gather information from the system"""
        self._get_devices()
        if self.devices["changed"]:
            self.lnxlink.setup_discovery()
        return self.devices["defaults"]

    def start_control(self, topic, data):
        """Control system"""
        if topic[1] == "microphone_select":
            with self.lib["pulsectl"].Pulse("lnxlink_ctl") as pulse:
                pulse.default_set(
                    pulse.get_source_by_name(self.devices["microphone"][data])
                )
        if topic[1] == "speaker_select":
            with self.lib["pulsectl"].Pulse("lnxlink_ctl") as pulse:
                pulse.default_set(pulse.get_sink_by_name(self.devices["speaker"][data]))

    def _get_devices(self):
        """Get a list of all audio devices"""
        devices = {
            "speaker": {},
            "microphone": {},
            "defaults": {"microphone": "", "speaker": ""},
            "changed": False,
        }

        try:
            with self.lib["pulsectl"].Pulse("lnxlink") as pulse:
                for sink in pulse.sink_list():
                    devices["speaker"][sink.description] = sink.name
                for source in pulse.source_list():
                    devices["microphone"][source.description] = source.name

                server_info = pulse.server_info()
                for description, name in devices["speaker"].items():
                    if name == server_info.default_sink_name:
                        devices["defaults"]["speaker"] = description
                for description, name in devices["microphone"].items():
                    if name == server_info.default_source_name:
                        devices["defaults"]["microphone"] = description
        except Exception as err:
            logger.error("Pulseaudio is not installed on your system: %s", err)

        if len(devices["defaults"]["speaker"]) != len(
            self.devices["defaults"].get("speaker", [])
        ):
            devices["changed"] = True
        if len(devices["defaults"]["microphone"]) != len(
            self.devices["defaults"].get("microphone", [])
        ):
            devices["changed"] = True
        self.devices = devices

        return devices
