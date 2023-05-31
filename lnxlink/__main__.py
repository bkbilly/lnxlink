#!/usr/bin/env python3

import os
import yaml
import time
import json
import distro
import threading
import traceback
import importlib.metadata
import platform
import argparse
import paho.mqtt.client as mqtt
from . import modules
from . import config
from .system_monitor import MonitorSuspend, GracefulKiller

version = importlib.metadata.version(__package__ or __name__)


class LNXlink():

    def __init__(self, config_path):
        print(f"LNXlink {version} started: {platform.python_version()}")

        # Read configuration from yaml file
        self.pref_topic = 'lnxlink'
        self.config = self.read_config(config_path)

        # Run each addon included in the modules folder
        self.Addons = {}
        for service, addon in modules.parse_modules(self.config['modules']).items():
            try:
                tmp_addon = addon(self)
                self.Addons[addon.service] = tmp_addon
            except Exception as e:
                print(f"Error with addon {addon.service}, please remove it from your config")
                traceback.print_exc()

        # Setup MQTT
        self.client = mqtt.Client()
        self.setup_mqtt()

    def publish_monitor_data(self, topic, pub_data):
        # print(topic, pub_data, type(pub_data))
        if pub_data is None:
            return
        if isinstance(pub_data, bool):
            if pub_data is True:
                pub_data = 'ON'
            if pub_data is False:
                pub_data = 'OFF'
        if type(pub_data) == dict:
            if all(v is None for v in pub_data.values()):
                return
        if type(pub_data) == list:
            if all(v is None for v in pub_data):
                return
        if pub_data is None:
            return
        if type(pub_data) in [dict, list]:
            pub_data = json.dumps(pub_data)
        self.client.publish(
            topic,
            payload=pub_data,
            retain=self.config['mqtt']['lwt']['retain']
        )

    def monitor_run(self):
        '''Gets information from each Addon and sends it to MQTT'''
        for service, addon in self.Addons.items():
            if hasattr(addon, 'getInfo') or hasattr(addon, 'getControlInfo'):
                try:
                    subtopic = addon.name.lower().replace(' ', '/')
                    if hasattr(addon, 'getInfo'):
                        topic = f"{self.pref_topic}/{self.config['mqtt']['statsPrefix']}/{subtopic}"
                        pub_data = addon.getInfo()
                        self.publish_monitor_data(topic, pub_data)
                    if hasattr(addon, 'getControlInfo'):
                        topic = f"{self.pref_topic}/monitor_controls/{subtopic}"
                        pub_data = addon.getControlInfo()
                        self.publish_monitor_data(topic, pub_data)
                except Exception as e:
                    print(f"Can't load addon: {service}")
                    traceback.print_exc()

    def monitor_run_thread(self):
        '''Runs method to get sensor information every prespecified interval'''
        self.monitor_run()

        interval = self.config.get('update_interval', 1)
        self.monitor = threading.Timer(interval, self.monitor_run_thread)
        self.monitor.start()

    def setup_mqtt(self):
        '''Creates the mqtt object'''
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.username_pw_set(self.config['mqtt']['auth']['user'], self.config['mqtt']['auth']['pass'])
        self.client.connect(self.config['mqtt']['server'], self.config['mqtt']['port'], 60)
        self.client.loop_start()

    def read_config(self, config_path):
        '''Reads the config file and prepares module names for import'''
        with open(config_path) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)

        if 'prefix' in config['mqtt'] and 'clientId' in config['mqtt']:
            self.pref_topic = f"{config['mqtt']['prefix']}/{config['mqtt']['clientId']}"
        self.pref_topic = self.pref_topic.lower()

        modules = config.get('modules')
        if modules is not None:
            modules = [x.lower().replace('-', '_') for x in config['modules']]
        config['modules'] = modules
        return config

    def on_connect(self, client, userdata, flags, rc):
        '''Callback for MQTT connect which reports the connection status
        back to MQTT server'''
        print(f"Connected to MQTT with code {rc}")
        client.subscribe(f"{self.pref_topic}/commands/#")
        if self.config['mqtt']['lwt']['enabled']:
            self.client.publish(
                f"{self.pref_topic}/lwt",
                payload=self.config['mqtt']['lwt']['connectMsg'],
                qos=self.config['mqtt']['lwt']['qos'],
                retain=self.config['mqtt']['lwt']['retain']
            )
        if self.config['mqtt']['discovery']['enabled']:
            self.setup_discovery()

    def disconnect(self, *args):
        '''Reports to MQTT server that the service has stopped'''
        print("Disconnected from MQTT.")
        if self.config['mqtt']['lwt']['enabled']:
            self.client.publish(
                f"{self.pref_topic}/lwt",
                payload=self.config['mqtt']['lwt']['disconnectMsg'],
                qos=self.config['mqtt']['lwt']['qos'],
                retain=self.config['mqtt']['lwt']['retain']
            )
        try:
            self.monitor.cancel()
        except Exception as e:
            pass
        self.client.disconnect()

    def temp_connection_callback(self, status):
        '''Report the connection status to MQTT server'''
        if self.config['mqtt']['lwt']['enabled']:
            if status:
                self.client.publish(
                    f"{self.pref_topic}/lwt",
                    payload=self.config['mqtt']['lwt']['disconnectMsg'],
                    qos=self.config['mqtt']['lwt']['qos'],
                    retain=self.config['mqtt']['lwt']['retain']
                )
            else:
                self.client.publish(
                    f"{self.pref_topic}/lwt",
                    payload=self.config['mqtt']['lwt']['connectMsg'],
                    qos=self.config['mqtt']['lwt']['qos'],
                    retain=self.config['mqtt']['lwt']['retain']
                )

    def on_message(self, client, userdata, msg):
        '''MQTT message is received with a module command to excecute'''
        topic = msg.topic.replace(f"{self.pref_topic}/commands/", "")
        message = msg.payload
        print(f"Message received {topic}: {message}")
        try:
            message = json.loads(message)
        except Exception as e:
            message = message.decode()
            # print("String could not be converted to JSON")
            # traceback.print_exc()

        select_service = topic.split('/')
        addon = self.Addons.get(select_service[0])
        if addon is not None:
            if hasattr(addon, 'startControl'):
                try:
                    addon.startControl(select_service, message)
                    self.monitor_run()
                except Exception as e:
                    traceback.print_exc()

    def setup_discovery_monitoring(self, discovery_template, addon, service):
        '''Send discovery information on Home Assistant for sensors'''
        subtopic = addon.name.lower().replace(' ', '/')
        state_topic = f"{self.pref_topic}/{self.config['mqtt']['statsPrefix']}/{subtopic}"

        discovery = discovery_template.copy()
        discovery['name'] = f"{self.config['mqtt']['clientId']} {addon.name}"
        discovery['unique_id'] = f"{self.config['mqtt']['clientId']}_{service}"
        discovery['state_topic'] = state_topic
        discovery['topic'] = state_topic
        if addon.getInfo.__annotations__.get('return') == dict:
            discovery['value_template'] = "{{ value_json.status }}"
            discovery['json_attributes_topic'] = state_topic
            discovery['json_attributes_template'] = "{{ value_json | tojson }}"
        if hasattr(addon, 'icon'):
            discovery['icon'] = addon.icon
        if hasattr(addon, 'unit'):
            discovery['unit_of_measurement'] = addon.unit
        if hasattr(addon, 'title'):
            discovery['title'] = addon.title
        if hasattr(addon, 'entity_picture'):
            discovery['entity_picture'] = addon.entity_picture
        if hasattr(addon, 'device_class'):
            discovery['device_class'] = addon.device_class
        if hasattr(addon, 'state_class'):
            discovery['state_class'] = addon.state_class

        sensor_type = getattr(addon, 'sensor_type', None)
        if sensor_type in ['sensor', 'binary_sensor']:
            discovery['expire_after'] = self.config.get('update_interval', 5) * 2
        if sensor_type is not None:
            self.client.publish(
                f"homeassistant/{sensor_type}/lnxlink/{discovery['unique_id']}/config",
                payload=json.dumps(discovery),
                retain=self.config['mqtt']['lwt']['retain'])

    def setup_discovery_control(self, discovery_template, addon, service, control_name, options):
        '''Send discovery information on Home Assistant for controls'''
        subtopic = addon.name.lower().replace(' ', '/')
        state_topic = f"{self.pref_topic}/monitor_controls/{subtopic}"
        command_topic = f"{self.pref_topic}/commands/{service}/{control_name.replace(' ', '_')}/"
        discovery = discovery_template.copy()
        discovery['name'] = f"{self.config['mqtt']['clientId']} {control_name}"
        discovery['unique_id'] = f"{self.config['mqtt']['clientId']}_{control_name.lower().replace(' ', '_')}"
        discovery['enabled_by_default'] = options.get('enabled', True)
        if 'value_template' in options:
            discovery["value_template"] = options['value_template']
            if options['type'] != 'camera':
                discovery['json_attributes_topic'] = state_topic
                discovery['json_attributes_template'] = "{{ value_json | tojson }}"
        if 'icon' in options:
            discovery['icon'] = options.get('icon', '')
        if 'unit' in options:
            discovery['unit_of_measurement'] = options.get('unit', '')
        if 'title' in options:
            discovery['title'] = options.get('title', '')
        if 'entity_picture' in options:
            discovery['entity_picture'] = options.get('entity_picture', '')
        if 'device_class' in options:
            discovery['device_class'] = options.get('device_class', '')
        if 'state_class' in options:
            discovery['state_class'] = options.get('state_class', '')
        if 'entity_category' in options:
            discovery['entity_category'] = options.get('entity_category', '')

        if options['type'] in ['sensor', 'binary_sensor']:
            discovery['state_topic'] = state_topic
            discovery['expire_after'] = self.config.get('update_interval', 5) * 2
        elif options['type'] in ['camera', 'update']:
            discovery['state_topic'] = state_topic
        elif options['type'] == 'button':
            discovery["command_topic"] = command_topic
            discovery['state_topic'] = f"{self.pref_topic}/lwt"
        elif options['type'] == 'switch':
            discovery["command_topic"] = command_topic
            discovery["state_topic"] = state_topic
            discovery["payload_off"] = "OFF"
            discovery["payload_on"] = "ON"
        elif options['type'] == 'text':
            discovery["command_topic"] = command_topic
            discovery["state_topic"] = state_topic
        elif options['type'] == 'number':
            discovery["command_topic"] = command_topic
            discovery["state_topic"] = state_topic
            discovery["min"] = options.get('min', 1)
            discovery["max"] = options.get('max', 100)
            discovery["step"] = options.get('step', 1)
        elif options['type'] == 'select':
            discovery["command_topic"] = command_topic
            discovery["state_topic"] = state_topic
            discovery["options"] = addon.options
        else:
            print("Not supported:", options['type'])
            return
        self.client.publish(
            f"homeassistant/{options['type']}/lnxlink/{discovery['unique_id']}/config",
            payload=json.dumps(discovery),
            retain=self.config['mqtt']['lwt']['retain'])

    def setup_discovery(self):
        '''First time setup of discovery for Home Assistant'''
        discovery_template = {
            "availability": {
                "topic": f"{self.pref_topic}/lwt",
                "payload_available": "ON",
                "payload_not_available": "OFF",
            },
            "device": {
                "identifiers": [self.config['mqtt']['clientId']],
                "name": self.config['mqtt']['clientId'],
                "model": f"{distro.name()} {distro.version()}",
                "manufacturer": f"LNXlink",
                "sw_version": version,
            },
        }
        for service, addon in self.Addons.items():
            addon = self.Addons[service]
            if hasattr(addon, 'getInfo'):
                try:
                    self.setup_discovery_monitoring(discovery_template, addon, service)
                except Exception as e:
                    traceback.print_exc()
            if hasattr(addon, 'exposedControls'):
                for control_name, options in addon.exposedControls().items():
                    try:
                        self.setup_discovery_control(discovery_template, addon, service, control_name, options)
                    except Exception as e:
                        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        prog="LNXlink",
        description="Send system information to MQTT broker")
    parser.add_argument(
        "-c", "--config",
        help="Configuration file",
        default="/etc/config.yaml",
        required=True)
    args = parser.parse_args()

    config_file = os.path.abspath(args.config)
    config.setup_config(config_file)
    config.setup_systemd(config_file)
    lnxlink = LNXlink(config_file)
    lnxlink.monitor_run_thread()

    # Monitor for system changes (Shutdown/Suspend/Sleep)
    monitor_suspend = MonitorSuspend(lnxlink.temp_connection_callback)
    monitor_suspend.start()
    monitor_gracefulkiller = GracefulKiller(lnxlink.temp_connection_callback)
    while not monitor_gracefulkiller.kill_now:
        time.sleep(0.2)
    monitor_suspend.stop()
    lnxlink.disconnect()


if __name__ == '__main__':
    main()
