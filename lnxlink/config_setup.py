#!/usr/bin/env python3
"""Setup the configuration file"""

import os
import subprocess
import logging
import shutil
from pathlib import Path

import yaml
from .consts import SERVICEHEADLESS, SERVICEUSER, CONFIGTEMP

logger = logging.getLogger("lnxlink")


def setup_config(config_path):
    """Setup and create config file"""
    if not os.path.exists(config_path):
        logger.info("Config file not found.")

        try:
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "wb") as config:
                config.write(CONFIGTEMP.encode())
            logger.info("Created new template: %s", config_path)
        except IOError:
            logger.info("Permision denied")
            return False
        userprompt_config(config_path)
    return True


def query_true_false(question, default="false"):
    """Force user to answer yes or no questions"""
    valid = {
        "true": True,
        "t": True,
        "yes": True,
        True: True,
        "false": False,
        "f": False,
        "no": False,
        False: False,
    }

    if default is True:
        prompt = "(True/False) [True]"
    elif default is False or default is None:
        prompt = "(True/False) [False]"
    else:
        raise ValueError(f"invalid default answer: {default}")

    while True:
        choice = input(f" {question} {prompt}: ").lower()
        if default is not None and choice == "":
            return valid[default]
        if choice in valid:
            return valid[choice]
        logger.info("Please respond with 'true' or 'false' (or 't' or 'f').")


def userprompt_config(config_path):
    """Ask users questions to setup config file"""
    with open(config_path, encoding="UTF-8") as file:
        config = yaml.safe_load(file)

        # logger.info config
        logger.info(
            "This will update the MQTT credentials and topics, these are the default topics:"
        )
        logger.info(
            " MQTT Topic prefix for for monitoring: %s/%s/...",
            config["mqtt"]["prefix"],
            config["mqtt"]["clientId"],
        )
        logger.info(
            " MQTT Topic prefix for for commands: %s/%s/commands/...",
            config["mqtt"]["prefix"],
            config["mqtt"]["clientId"],
        )

        logger.info("\nLeave empty for default")

        # Change default values
        config["mqtt"]["discovery"]["enabled"] = query_true_false(
            "Enable MQTT automatic discovery", config["mqtt"]["discovery"]["enabled"]
        )
        config["mqtt"]["server"] = (
            input(f" MQTT server [{config['mqtt']['server']}]: ")
            or config["mqtt"]["server"]
        )
        config["mqtt"]["port"] = (
            input(f" MQTT port [{config['mqtt']['port']}]: ") or config["mqtt"]["port"]
        )
        config["mqtt"]["port"] = int(config["mqtt"]["port"])
        config["mqtt"]["auth"]["tls"] = query_true_false(
            "Enable TLS", config["mqtt"]["auth"]["tls"]
        )
        config["mqtt"]["auth"]["user"] = (
            input(f" MQTT username [{config['mqtt']['auth']['user']}]: ")
            or config["mqtt"]["auth"]["user"]
        )
        config["mqtt"]["auth"]["pass"] = (
            input(f" MQTT password [{config['mqtt']['auth']['pass']}]: ")
            or config["mqtt"]["auth"]["pass"]
        )

        config["mqtt"]["prefix"] = (
            input(f" Change prefix [{config['mqtt']['prefix']}]: ")
            or config["mqtt"]["prefix"]
        )
        config["mqtt"]["clientId"] = (
            input(f" Change clientId [{config['mqtt']['clientId']}]: ")
            or config["mqtt"]["clientId"]
        )

    with open(config_path, "w", encoding="UTF-8") as file:
        file.write(yaml.dump(config, default_flow_style=False, sort_keys=False))

    logger.info("\nAll changes have been saved.")
    logger.info(
        " MQTT Topic prefix for for monitoring: %s/%s/...",
        config["mqtt"]["prefix"],
        config["mqtt"]["clientId"],
    )
    logger.info(
        " MQTT Topic prefix for for commands: %s/%s/commands/...",
        config["mqtt"]["prefix"],
        config["mqtt"]["clientId"],
    )


def get_service_user():
    """Install as a user service"""
    installed_as = 0
    for num, cmd_user in enumerate(["--user", ""], start=1):
        cmd = f"systemctl {cmd_user} is-enabled lnxlink.service"
        stdout = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        ).stdout.decode("UTF-8")
        result = stdout.strip()
        if result in ["enabled"]:
            _, _, _, service_location = get_service_vars(num)
            if os.path.exists(f"{service_location}/lnxlink.service"):
                installed_as = num
    return installed_as


def get_service_vars(user_service):
    """Return service commands based on installation type"""
    if user_service is True or user_service == 1:
        sudo = ""
        cmd_user = "--user"
        systemd_service = SERVICEUSER
        service_location = f"{os.path.expanduser('~')}/.config/systemd/user"
    else:
        sudo = "sudo"
        cmd_user = ""
        systemd_service = SERVICEHEADLESS
        service_location = "/etc/systemd/system"
    return sudo, cmd_user, systemd_service, service_location


def setup_systemd(config_path):
    """Install as a system service"""
    # Check how systemd is installed
    installed_as = get_service_user()

    if installed_as == 0:
        # Service not found or not running
        logger.info("SystemD service not found or it's not running...")
        user_service = query_true_false("Install as a user service?", True)
        sudo, cmd_user, systemd_service, service_location = get_service_vars(
            user_service
        )

        # Install on SystemD
        Path(service_location).mkdir(parents=True, exist_ok=True)
        exec_cmd = f"{shutil.which('lnxlink')} -c {config_path}"
        with open(f"{service_location}/lnxlink.service", "wb") as config:
            config.write(systemd_service.format(exec_cmd=exec_cmd).encode())

        cmd = f"{sudo} chmod +x {service_location}/lnxlink.service"
        subprocess.call(cmd, shell=True)
        cmd = f"{sudo} systemctl {cmd_user} enable lnxlink.service"
        subprocess.call(cmd, shell=True)
        cmd = f"{sudo} systemctl {cmd_user} daemon-reload"
        subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    # config_path = sys.argv[1]
    # download_template(config_path)
    setup_systemd("lnxlink.yaml")
