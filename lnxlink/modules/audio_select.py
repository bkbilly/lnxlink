"""Information and control of pulseaudio devices"""
import json
import logging
from lnxlink.modules.scripts.helpers import import_install_package, syscommand

logger = logging.getLogger("lnxlink")


class Addon:
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "Audio Select"
        self.lnxlink = lnxlink
        self.audio_system = self._get_audio_system()
        if self.audio_system is None:
            raise SystemError("Can't find any supported audio system")
        self.devices = {
            "speaker": {},
            "microphone": {},
            "defaults": {"microphone": "", "speaker": ""},
            "changed": False,
        }
        self._get_devices()

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
            self.lnxlink.setup_discovery("audio_select")
        return self.devices["defaults"]

    def start_control(self, topic, data):
        """Control system"""
        if topic[1] == "microphone_select":
            if self.audio_system == "pactl":
                syscommand(
                    f"pactl set-default-source {self.devices['microphone'][data]}"
                )
            elif self.audio_system == "pulsectl":
                with self.pulsectl.Pulse("lnxlink_ctl") as pulse:
                    pulse.default_set(
                        pulse.get_source_by_name(self.devices["microphone"][data])
                    )
        if topic[1] == "speaker_select":
            if self.audio_system == "pactl":
                syscommand(f"pactl set-default-sink {self.devices['speaker'][data]}")
            elif self.audio_system == "pulsectl":
                with self.pulsectl.Pulse("lnxlink_ctl") as pulse:
                    pulse.default_set(
                        pulse.get_sink_by_name(self.devices["speaker"][data])
                    )

    def _get_audio_system(self):
        """Get system volume type"""
        _, _, returncode = syscommand(
            "pactl get-sink-volume @DEFAULT_SINK@", ignore_errors=True
        )
        if returncode == 0:
            return "pactl"

        self.pulsectl = import_install_package("pulsectl", ">=23.5.2")
        if self.pulsectl is not None:
            return "pulsectl"

        return None

    # pylint: disable=too-many-branches
    def _get_devices(self):
        """Get a list of all audio devices"""
        devices = {
            "speaker": {},
            "microphone": {},
            "defaults": {"microphone": "", "speaker": ""},
            "changed": False,
        }

        if self.audio_system == "pactl":
            stdout, _, _ = syscommand("pactl -f json list sinks")
            for sink in json.loads(stdout):
                devices["speaker"][sink["description"]] = sink["name"]
            stdout, _, _ = syscommand("pactl -f json list sources")
            for source in json.loads(stdout):
                devices["microphone"][source["description"]] = source["name"]
            stdout, _, _ = syscommand("pactl get-default-sink")
            for description, name in devices["speaker"].items():
                if name == stdout:
                    devices["defaults"]["speaker"] = description
            stdout, _, _ = syscommand("pactl get-default-source")
            for description, name in devices["microphone"].items():
                if name == stdout:
                    devices["defaults"]["microphone"] = description
        elif self.audio_system == "pulsectl":
            try:
                with self.pulsectl.Pulse("lnxlink") as pulse:
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
                logger.error("Error with Pulseaudio: %s", err)

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
