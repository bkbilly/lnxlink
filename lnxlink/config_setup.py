#!/usr/bin/env python3
"""Setup the configuration file"""

import copy
import errno
import logging
import os
import shutil
import subprocess
import traceback
from pathlib import Path

import beaupy
import yaml

from lnxlink.consts import CONFIGTEMP, SERVICEHEADLESS, SERVICEUSER
from lnxlink.modules import get_modules_info

logger = logging.getLogger("lnxlink")


def _write_config(config_path, config):
    """Write config changes to disk and report permission issues clearly."""
    try:
        with open(config_path, "w", encoding="UTF-8") as file:
            file.write(yaml.dump(config, default_flow_style=False, sort_keys=False))
        return True
    except OSError as err:
        if err.errno in {errno.EACCES, errno.EPERM, errno.EROFS}:
            logger.error(
                "Could not update configuration file %s because of permission issues.",
                config_path,
            )
        else:
            logger.error("Could not update configuration file %s: %s", config_path, err)
    return False


def setup_config(config_path):
    """Setup and create config file"""
    if not os.path.exists(config_path):
        logger.info("Config file not found.")

        try:
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "wb") as config:
                config.write(CONFIGTEMP.encode())
            logger.info("Created new template: %s", config_path)
        except OSError as err:
            if err.errno in {errno.EACCES, errno.EPERM, errno.EROFS}:
                logger.error(
                    "Could not create configuration file %s because of permission "
                    "issues.",
                    config_path,
                )
            else:
                logger.error(
                    "Could not create configuration file %s: %s", config_path, err
                )
            return False
        userprompt_config(config_path)
    validate_config(config_path)
    return True


def add_settings(config, name, settings, replace_empty=False):
    """Add missing configuration to yaml file"""
    if not isinstance(config.get("settings"), dict):
        config["settings"] = {}
    sys_conf = copy.deepcopy(config)
    sys_conf["settings"][name] = settings
    missing_keys = check_missing(sys_conf, config, [], [], replace_empty)

    if len(missing_keys) > 0:
        try:
            with open(config["config_path"], encoding="utf8") as file:
                new_config = yaml.load(file, Loader=yaml.FullLoader)
            for keys, value in missing_keys:
                new_config = add_nested(new_config, keys, value, replace_empty)
                config = add_nested(config, keys, value, replace_empty)
                key_path = ".".join(keys)
                logger.info("Adding missing configuration option: %s", key_path)
            success_write = _write_config(config["config_path"], new_config)
            if not success_write:
                manual_insert = {}
                for keys, value in missing_keys:
                    manual_insert = add_nested(manual_insert, keys, value)
                manual_yaml = yaml.dump(
                    manual_insert,
                    default_flow_style=False,
                    sort_keys=False,
                ).rstrip()
                logger.error(
                    "Can't write to config file, manual add this: \n%s", manual_yaml
                )

        except Exception as err:
            logger.error(
                "Couldn't edit configuration (%s): %s",
                err,
                traceback.format_exc(),
            )
    return config


def validate_config(config_path):
    """Inform user of missing configuration values"""
    with open(config_path, encoding="utf8") as file:
        user_conf = yaml.load(file, Loader=yaml.FullLoader)
    sys_conf = yaml.safe_load(CONFIGTEMP)

    missing_keys = check_missing(sys_conf, user_conf, [], [])
    for keys, value in missing_keys:
        key_path = ".".join(keys)
        user_conf = add_nested(user_conf, keys, value)
        logger.info("Adding missing configuration option: %s", key_path)

    if len(missing_keys) > 0:
        success_write = _write_config(config_path, user_conf)
        if not success_write:
            manual_insert = {}
            for keys, value in missing_keys:
                manual_insert = add_nested(manual_insert, keys, value)
            manual_yaml = yaml.dump(
                manual_insert,
                default_flow_style=False,
                sort_keys=False,
            ).rstrip()
            logger.error(
                "Can't write to config file, manual add this: \n%s", manual_yaml
            )


def check_missing(sys_conf, user_conf, missing, dirpath, replace_empty=False):
    """Recursive method that returns a list of missing dictionary keys"""
    if isinstance(sys_conf, dict):
        for key, value in sys_conf.items():
            check_path = dirpath + [key]
            if isinstance(user_conf, dict) and key in user_conf:
                if (
                    replace_empty
                    and not isinstance(value, dict)
                    and user_conf[key] in [None, ""]
                    and value not in [None, ""]
                ):
                    missing.append([check_path, value])
                else:
                    check_missing(
                        value, user_conf[key], missing, check_path, replace_empty
                    )
            else:
                missing.append([check_path, value])
    return missing


def add_nested(dct, keys, value, replace_empty=False):
    """
    Adds a nested dictionary item based on a list of keys to an existing dictionary.

    Args:
    dct (dict): The original dictionary to be modified.
    keys (list): A list of keys representing the nested structure.
    value (any): The value to be set at the innermost level.

    Returns:
    dict: The modified dictionary with the new nested item added.
    """
    current_level = dct
    for key in keys[:-1]:
        # Create a new dictionary at the current key if it does not exist
        if key not in current_level or not isinstance(current_level[key], dict):
            current_level[key] = {}
        current_level = current_level[key]

    # Set the value at the innermost level
    if keys[-1] not in current_level or (
        replace_empty
        and current_level[keys[-1]] in [None, ""]
        and value not in [None, ""]
    ):
        current_level[keys[-1]] = value
    return dct


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
        config["mqtt"]["clientId"] = (
            input(f" Change clientId [{config['mqtt']['clientId']}]: ")
            or config["mqtt"]["clientId"]
        )
        statistics = query_true_false("Send statistics", True)
        if not statistics:
            config["exclude"].append("statistics")

    if _write_config(config_path, config):
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
            cmd,
            shell=True,
            capture_output=True,
            check=False,
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
        service_text = systemd_service.format(exec_cmd=exec_cmd).encode()
        try:
            with open(f"{service_location}/lnxlink.service", "wb") as config:
                config.write(service_text)
        except PermissionError:
            cmd = f'echo "{service_text}" | {sudo} tee "{service_location}/lnxlink.service"'
            subprocess.call(cmd, shell=True)

        cmd = f"{sudo} chmod +x {service_location}/lnxlink.service"
        subprocess.call(cmd, shell=True)
        cmd = f"{sudo} systemctl {cmd_user} enable lnxlink.service"
        subprocess.call(cmd, shell=True)
        cmd = f"{sudo} systemctl {cmd_user} daemon-reload"
        subprocess.call(cmd, shell=True)


def setup_modules(config_path):
    """Asks user which modules to include in the configuration"""
    with open(config_path, encoding="UTF-8") as file:
        config = yaml.safe_load(file)

    modules = get_modules_info(config["modules"], config["exclude"])
    options = [
        f"[bold]{module['name']}[/bold] - [dim]{module['description']}[/dim]"
        for module in modules
    ]
    initial_ticked = [num for num, module in enumerate(modules) if module["is_enabled"]]
    selected_formatted = beaupy.select_multiple(
        options, ticked_indices=initial_ticked, pagination=True, page_size=18
    )
    selected_names = [
        opt.split(" - ")[0].replace("[bold]", "").replace("[/bold]", "")
        for opt in selected_formatted
    ]
    all_module_names = [module["name"] for module in modules]
    unselected_names = [name for name in all_module_names if name not in selected_names]

    if len(selected_names) == 0:
        return
    print("You selected:", selected_names)
    if len(selected_names) < len(unselected_names):
        config["exclude"] = None
        config["modules"] = selected_names
    else:
        config["exclude"] = unselected_names
        config["modules"] = None

    _write_config(config_path, config)


if __name__ == "__main__":
    # config_path = sys.argv[1]
    # download_template(config_path)
    # setup_systemd("lnxlink.yaml")
    setup_modules("config.yaml")
