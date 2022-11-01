#!/usr/bin/env python3

import yaml
import os
import subprocess
import shutil
from pathlib import Path
from .consts import service_headless, service_user, config_temp


def setup_config(config_path):
    if not os.path.exists(config_path):
        print("Config file not found.")

        try:
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'wb') as config:
                config.write(config_temp.encode())
            print(f"Created new template: {config_path}")
        except IOError:
            print("Permision denied")
            return False
        userprompt_config(config_path)
    return True


def query_true_false(question, default="false"):
    valid = {"true": True, "t": True, "yes": True, True: True, "false": False, "f": False, "no": False, False:False}

    if default == True:
        prompt = "(True/False) [True]"
    elif default == False or default is None:
        prompt = "(True/False) [False]"
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        choice = input(f" {question} {prompt}: ").lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'true' or 'false' (or 't' or 'f').")


def userprompt_config(config_path):
    with open(config_path) as f:
        y = yaml.safe_load(f)

        # Print config
        print('This will update the MQTT credentials and topics, these are the default topics:')
        print(" MQTT Topic prefix for for monitoring: {}/{}/{}/...".format(
            y['mqtt']['prefix'],
            y['mqtt']['clientId'],
            y['mqtt']['statsPrefix']
        ))
        print(" MQTT Topic prefix for for commands: {}/{}/commands/...".format(
            y['mqtt']['prefix'],
            y['mqtt']['clientId']
        ))

        print("\nLeave empty for default")

        # Change default values
        y['mqtt']['discovery']['enabled'] = query_true_false("Enable MQTT automatic discovery", y['mqtt']['discovery']['enabled'])
        y['mqtt']['server'] = input(f" MQTT server [{y['mqtt']['server']}]: ") or y['mqtt']['server']
        y['mqtt']['port'] = input(f" MQTT port [{y['mqtt']['port']}]: ") or y['mqtt']['port']
        y['mqtt']['port'] = int(y['mqtt']['port'])
        y['mqtt']['auth']['user'] = input(f" MQTT username [{y['mqtt']['auth']['user']}]: ") or y['mqtt']['auth']['user']
        y['mqtt']['auth']['pass'] = input(f" MQTT password [{y['mqtt']['auth']['pass']}]: ") or y['mqtt']['auth']['pass']

        y['mqtt']['prefix'] = input(f" Change prefix [{y['mqtt']['prefix']}]: ") or y['mqtt']['prefix']
        y['mqtt']['clientId'] = input(f" Change clientId [{y['mqtt']['clientId']}]: ") or y['mqtt']['clientId']
        y['mqtt']['statsPrefix'] = input(f" Change statsPrefix [{y['mqtt']['statsPrefix']}]: ") or y['mqtt']['statsPrefix']


    with open(config_path, 'w') as fw:
        fw.write(yaml.dump(y, default_flow_style=False, sort_keys=False))

    print('\nAll changes have been saved.')
    print(" MQTT Topic prefix for for monitoring: {}/{}/{}/...".format(
        y['mqtt']['prefix'],
        y['mqtt']['clientId'],
        y['mqtt']['statsPrefix']
    ))
    print(" MQTT Topic prefix for for commands: {}/{}/commands/...".format(
        y['mqtt']['prefix'],
        y['mqtt']['clientId']
    ))


def get_service_user():
    installed_as = 0
    for num, cmd_user in enumerate(["--user", ""], start=1):
        cmd = f"systemctl {cmd_user} is-enabled lnxlink.service"
        stdout = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).stdout.decode("UTF-8")
        result = stdout.strip()
        if result in ['enabled']:
            _, _, _, service_location = get_service_vars(num)
            if os.path.exists(f"{service_location}/lnxlink.service"):
                installed_as = num
    return installed_as


def get_service_vars(user_service):
    if user_service == True or user_service == 1:
        sudo = ""
        cmd_user = "--user"
        systemd_service = service_user
        service_location = f"{os.path.expanduser('~')}/.config/systemd/user"
    else:
        sudo = "sudo"
        cmd_user = ""
        systemd_service = service_headless
        service_location = "/etc/systemd/system"
    return sudo, cmd_user, systemd_service, service_location


def setup_systemd(config_path):
    # Check how systemd is installed
    installed_as = get_service_user()

    if installed_as == 0:
        # Service not found or not running
        print("SystemD service not found or it's not running...")
        user_service = query_true_false("Install as a user service?", True)
        sudo, cmd_user, systemd_service, service_location = get_service_vars(user_service)

        # Install on SystemD
        Path(service_location).mkdir(parents=True, exist_ok=True)
        exec_cmd = f"{shutil.which('lnxlink')} -c {config_path}"
        with open(f"{service_location}/lnxlink.service", 'wb') as config:
            config.write(systemd_service.format(exec_cmd=exec_cmd).encode())

        cmd = f"{sudo} chmod +x {service_location}/lnxlink.service"
        subprocess.call(cmd, shell=True)
        cmd = f"{sudo} systemctl {cmd_user} enable lnxlink.service"
        subprocess.call(cmd, shell=True)
        cmd = f"{sudo} systemctl {cmd_user} daemon-reload"
        subprocess.call(cmd, shell=True)


if __name__ == '__main__':
    # config_path = sys.argv[1]
    # download_template(config_path)
    setup_systemd("lnxlink.yaml")
