#!/usr/bin/env python3
"""Start the LNXlink service"""

import os
import sys
import time
import json
import threading
import logging
import argparse
import platform
import traceback

import distro
from lnxlink import modules
from lnxlink import config_setup
from lnxlink import files_setup
from lnxlink.mqtt import MQTT
from lnxlink.system_monitor import MonitorSuspend, GracefulKiller
from lnxlink.modules.scripts import helpers

version, path = files_setup.get_version()
logger = logging.getLogger("lnxlink")


# pylint: disable=too-many-instance-attributes
class LNXlink:
    """Start LNXlink service that loads all modules and connects to MQTT"""

    version = version
    path = path

    def __init__(self, config):
        logger.info("LNXlink %s, Python %s", self.version, platform.python_version())
        logger.debug("Path=%s", self.path)
        self.config = config
        self.config_path = config["config_path"]
        self.kill = None
        self.display = None
        self.inference_times = {}
        self.addons = {}
        self.prev_publish = {}
        self.saved_publish = {}
        self.update_change_interval = 900

        # Read configuration from yaml file
        self.publ_queue = files_setup.UniqueQueue()
        self.mqtt = MQTT(self.config)
        self.stop_event = threading.Event()

    def start(self, exclude_modules_arg):
        """Run each addon included in the modules folder"""
        conf_exclude = self.config["exclude"]
        conf_exclude = [] if conf_exclude is None else conf_exclude
        conf_exclude.extend(exclude_modules_arg)
        loaded_modules = modules.parse_modules(
            self.config["modules"], self.config["custom_modules"], conf_exclude
        )
        for _, addon in loaded_modules.items():
            try:
                tmp_addon = addon(self)
                self.addons[addon.service] = tmp_addon
            except Exception as err:
                logger.error(
                    "Error with addon %s, please remove it from your config: %s",
                    addon.service,
                    err,
                )
                logger.debug(
                    traceback.format_exc(),
                )
        loaded = list(self.addons.keys())
        loaded.sort()
        logger.info("Loaded addons: %s", ", ".join(loaded))

        mqtt_status = self.mqtt.setup_mqtt(self.on_connect, self.on_message)
        threading.Thread(target=self.monitor_run, daemon=True).start()
        threading.Thread(target=self.monitor_queue, daemon=True).start()
        return mqtt_status

    def add_settings(self, name, settings):
        """Adds missing configuration under settings"""
        self.config = config_setup.add_settings(self.config, name, settings)

    def publish_monitor_data(self, name, pub_data):
        """Publish info data to mqtt in the correct format"""
        subtopic = helpers.text_to_topic(name)
        topic = f"{self.config['pref_topic']}/monitor_controls/{subtopic}"
        if pub_data is None:
            return
        if isinstance(pub_data, bool):
            if pub_data is True:
                pub_data = "ON"
            if pub_data is False:
                pub_data = "OFF"
        if isinstance(pub_data, dict):
            if all(v is None for v in pub_data.values()):
                return
        if isinstance(pub_data, list):
            if all(v is None for v in pub_data):
                return
        if isinstance(pub_data, (dict, list)):
            pub_data = json.dumps(pub_data)

        # User option that checks and sends only the updated sensors
        update_change_time = time.time() - self.prev_publish.get("last_update", 0)
        if update_change_time > self.update_change_interval:
            self.prev_publish = {"last_update": time.time()}
        if (
            self.config["update_on_change"] or isinstance(pub_data, bytes)
        ) and self.prev_publish.get(topic) == pub_data:
            return

        self.prev_publish[topic] = pub_data
        self.saved_publish[subtopic.replace("/", "_")] = pub_data
        self.mqtt.publish(topic, pub_data)

    def run_module(self, name, method):
        """Runs the method of a module"""
        try:
            start_time = time.time()
            if isinstance(method, (dict, list, bool, bytes, int, str, float)):
                pub_data = method
            else:
                pub_data = method()
                diff_time = round(time.time() - start_time, 5)
                self.inference_times[name] = diff_time
            self.publ_queue.add_item(name, pub_data)
        except Exception as err:
            logger.error(
                "Error with addon %s: %s, %s",
                name,
                err,
                traceback.format_exc(),
            )

    def monitor_run(self):
        """Gets information from each Addon and adds it to the queue"""
        while not self.stop_event.is_set():
            methods_to_run = []
            if not self.kill:
                for _, addon in self.addons.items():
                    if hasattr(addon, "get_info"):
                        methods_to_run.append(
                            {
                                "name": addon.name,
                                "method": addon.get_info,
                            }
                        )
                for method in methods_to_run:
                    self.run_module(method["name"], method["method"])
            if self.stop_event.wait(timeout=self.config["update_interval"]):
                break
        logger.info("Stopped monitor_run")

    def monitor_queue(self):
        """Loop through the queue list and publish data to MQTT broker"""
        while not self.stop_event.is_set():
            if not self.kill:
                self.mqtt.send_lwt("ON")
                time.sleep(0.01)
                for name, pub_data in self.publ_queue:
                    self.publish_monitor_data(name, pub_data)
                    time.sleep(0.01)
            if self.stop_event.wait(timeout=0.2):
                self.mqtt.send_lwt("OFF")
                break
        logger.info("Stopped monitor_queue")

    def on_connect(self, client, userdata, flags, rcode, *args):
        """Callback for MQTT connect which reports the connection status
        back to MQTT server"""
        logger.info("MQTT connection: %s", self.mqtt.get_rcode_name(rcode))
        client.subscribe(f"{self.config['pref_topic']}/commands/#")
        if self.config["mqtt"]["lwt"]["enabled"]:
            self.mqtt.send_lwt("ON")
        if self.config["mqtt"]["discovery"]["enabled"]:
            self.setup_discovery()
        if self.kill is None:
            self.kill = False

    def disconnect(self, *args):
        """Service has stopped"""
        self.kill = True
        self.mqtt.disconnect()
        self.stop_event.set()

    def replace_values_with_none(self, data):
        """Replaces specified values with None recursively"""
        if isinstance(data, (str, bool, float, int)):
            return None
        if isinstance(data, dict):
            return {
                key: self.replace_values_with_none(value) for key, value in data.items()
            }
        return data

    def temp_connection_callback(self, status):
        """Report the connection status to MQTT server"""
        logger.info("Got Temp Connection Callback with status %s", status)
        self.kill = True
        if status:
            logger.info("Power Down detected.")
            self.mqtt.send_lwt("OFF")
            for topic, message in self.prev_publish.items():
                message = self.replace_values_with_none(message)
                self.mqtt.publish(topic, message)
        else:
            logger.info("Power Up detected.")
            if self.kill:
                self.kill = False
            self.mqtt.send_lwt("ON")

    def on_message(self, client, userdata, msg):
        """MQTT message is received with a module command to execute"""
        topic = msg.topic.replace(f"{self.config['pref_topic']}/commands/", "")
        message = msg.payload
        logger.info("Message received %s: %s", topic, message)
        try:
            message = json.loads(message)
        except json.decoder.JSONDecodeError:
            message = message.decode()
        except Exception as err:
            logger.debug("Error reading message: %s", err)

        service = topic.split("/")
        addon = self.addons.get(service[0])
        if addon is not None:
            if hasattr(addon, "start_control"):
                threading.Thread(
                    target=self.start_control_bg,
                    args=(addon, topic, service, message),
                    daemon=True,
                ).start()

    def start_control_bg(self, addon, topic, service, message):
        """Starts the start_control method of a module in the background"""
        try:
            result = addon.start_control(service, message)
            if result is not None:
                result_topic = (
                    f"{self.config['pref_topic']}/command_result/{topic.strip('/')}"
                )
                self.mqtt.publish(result_topic, result)
        except Exception as err:
            logger.error(
                "Couldn't run command for module %s: %s, %s",
                addon,
                err,
                traceback.format_exc(),
            )

    def setup_discovery_entities(self, addon, service, exp_name, options):
        """Send discovery information on Home Assistant for controls"""
        discovery_template = {
            "availability": {
                "topic": f"{self.config['pref_topic']}/lwt",
                "payload_available": "ON",
                "payload_not_available": "OFF",
            },
            "device": {
                "identifiers": [self.config["mqtt"]["clientId"]],
                "name": self.config["mqtt"]["clientId"],
                "model": f"{distro.name()} {distro.version()}",
                "manufacturer": "LNXlink",
                "sw_version": version,
            },
        }
        subtopic = helpers.text_to_topic(addon.name)
        if "method" in options or options.get("subtopic", False):
            subcontrol = helpers.text_to_topic(exp_name)
            subtopic = f"{subtopic}/{subcontrol}"
        state_topic = f"{self.config['pref_topic']}/monitor_controls/{subtopic}"
        control_name_topic = helpers.text_to_topic(exp_name)
        command_topic = (
            f"{self.config['pref_topic']}/commands/{service}/{control_name_topic}"
        )

        lookup_options = {
            "value_template": {
                "value_template": options.get("value_template", ""),
            },
            "attributes_template": {
                "json_attributes_topic": state_topic,
                "json_attributes_template": options.get(
                    "attributes_template", "{{ value_json | tojson }}"
                ),
            },
            "icon": {"icon": options.get("icon", "")},
            "unit": {"unit_of_measurement": options.get("unit", "")},
            "title": {"title": options.get("title", "")},
            "entity_picture": {"entity_picture": options.get("entity_picture", "")},
            "device_class": {"device_class": options.get("device_class", "")},
            "state_class": {"state_class": options.get("state_class", "")},
            "entity_category": {"entity_category": options.get("entity_category", "")},
            "enabled": {"enabled_by_default": options.get("enabled", True)},
            "expire_after": {"expire_after": options.get("expire_after", "")},
            "install": {
                "command_topic": command_topic,
                "payload_install": options.get("install", ""),
            },
        }
        lookup_entities = {
            "sensor": {
                "state_topic": state_topic,
            },
            "binary_sensor": {
                "state_topic": state_topic,
            },
            "camera": {
                "topic": state_topic,
                "image_encoding": options.get("encoding"),
            },
            "image": {
                "image_topic": state_topic,
                "image_encoding": options.get("encoding"),
            },
            "update": {"state_topic": state_topic},
            "button": {
                "command_topic": command_topic,
                "payload_press": options.get("payload_press", "PRESS"),
            },
            "switch": {
                "state_topic": state_topic,
                "command_topic": command_topic,
                "payload_off": options.get("command_off", "OFF"),
                "payload_on": options.get("command_on", "ON"),
                "state_off": "OFF",
                "state_on": "ON",
            },
            "text": {
                "state_topic": state_topic,
                "command_topic": command_topic,
                "min": options.get("min", 0),
                "max": options.get("max", 255),
            },
            "number": {
                "state_topic": state_topic,
                "command_topic": command_topic,
                "min": options.get("min", 1),
                "max": options.get("max", 100),
                "step": options.get("step", 1),
            },
            "select": {
                "state_topic": state_topic,
                "command_topic": command_topic,
                "options": options.get("options", []),
            },
            "device_tracker": {
                "json_attributes_topic": state_topic,
            },
            "media_player": {
                "name": self.config["mqtt"]["clientId"],
                "state_state_topic": f"{state_topic}/state",
                "state_title_topic": f"{state_topic}/title",
                "state_artist_topic": f"{state_topic}/artist",
                "state_album_topic": f"{state_topic}/album",
                "state_duration_topic": f"{state_topic}/duration",
                "state_position_topic": f"{state_topic}/position",
                "state_volume_topic": f"{state_topic}/volume",
                "state_albumart_topic": f"{state_topic}/albumart",
                "state_mediatype_topic": f"{state_topic}/mediatype",
                "command_volume_topic": f"{command_topic}/set_volume",
                "command_play_topic": f"{command_topic}/play",
                "command_play_payload": "Play",
                "command_pause_topic": f"{command_topic}/pause",
                "command_pause_payload": "Pause",
                "command_playpause_topic": f"{command_topic}/playpause",
                "command_playpause_payload": "PlayPause",
                "command_next_topic": f"{command_topic}/next",
                "command_next_payload": "Next",
                "command_previous_topic": f"{command_topic}/previous",
                "command_previous_payload": "Previous",
                "command_playmedia_topic": f"{command_topic}/play_media",
            },
        }
        discovery = discovery_template.copy()
        discovery["name"] = exp_name
        discovery[
            "unique_id"
        ] = f"{self.config['mqtt']['clientId']}_{control_name_topic}"
        discovery.update(lookup_entities.get(options["type"], {}))
        for option in options:
            discovery.update(lookup_options.get(option, {}))

        if options["type"] not in lookup_entities:
            logger.error("Not supported: %s", options["type"])
            return
        if "value_template" in discovery and options["type"] in ["camera", "image"]:
            del discovery["json_attributes_topic"]
            del discovery["json_attributes_template"]
        self.mqtt.publish(
            f"homeassistant/{options['type']}/lnxlink/{discovery['unique_id']}/config",
            payload=json.dumps(discovery),
        )
        if options["type"] == "media_player":
            logger.info(
                "MQTT Media Player configuration name: lnxlink/%s",
                discovery["unique_id"],
            )

    def setup_discovery(self, filter_name=None):
        """First time setup of discovery for Home Assistant"""
        for service, addon in self.addons.items():
            if filter_name is not None and filter_name != service:
                continue
            if hasattr(addon, "exposed_controls"):
                for exp_name, options in addon.exposed_controls().items():
                    try:
                        self.setup_discovery_entities(addon, service, exp_name, options)
                    except Exception as err:
                        logger.error(
                            "%s: %s, %s", exp_name, err, traceback.format_exc()
                        )

    def restart_script(self):
        """Restarts itself"""
        logger.info("Restarting LNXlink...")
        os.execv(sys.executable, ["python"] + sys.argv)


def main():
    """Starts the app with some arguments"""
    description = (
        f"LNXlink {version} bridges this OS with Home Assistant through an MQTT broker."
    )
    parser = argparse.ArgumentParser(prog="lnxlink", description=description)
    parser.add_argument(
        "-c",
        "--config",
        help="Configuration file",
    )
    parser.add_argument(
        "-i",
        "--ignore-systemd",
        help="Runs without setting up SystemD service",
        action="store_true",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help="Exclude modules from running",
        default=[],
        type=lambda t: [s.strip() for s in t.split(",")],
    )
    parser.add_argument(
        "-l",
        "--logging",
        help="Set the logging level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "-s",
        "--setup",
        help="Runs only the setup configuration workflow",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Shows current version of LNXlink",
        action="store_true",
    )
    args = parser.parse_args()

    if args.version:
        print(version)
        sys.exit()
    if args.config is None:
        parser.print_help()
        parser.exit("\nSomething went wrong, --config condition was not set")
    config_path = os.path.abspath(args.config)
    files_setup.setup_logger(config_path, args.logging)
    config_setup.setup_config(config_path)
    if args.setup:
        logger.info("The configuration exists under the file: %s", config_path)
        sys.exit()
    if not args.ignore_systemd:
        config_setup.setup_systemd(config_path)
    else:
        logger.info(
            "By not setting up the SystemD, LNXlink won't be able to start on boot..."
        )

    config = files_setup.read_config(config_path)
    lnxlink = LNXlink(config)

    # Monitor for system changes (Shutdown/Suspend/Sleep)
    monitor_suspend = MonitorSuspend(lnxlink.temp_connection_callback)
    monitor_suspend.start()
    monitor_gracefulkiller = GracefulKiller(lnxlink.temp_connection_callback)

    # Starts the main app
    start_status = lnxlink.start(args.exclude)
    if start_status:
        while not monitor_gracefulkiller.kill_now:
            time.sleep(1.0)
        monitor_suspend.stop()
        lnxlink.disconnect()
    else:
        monitor_suspend.stop()


if __name__ == "__main__":
    main()
