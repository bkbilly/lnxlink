"""Auto load addons/modules"""
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
import time
import logging
import glob
import os
import requests

logger = logging.getLogger("lnxlink")


def autoload_modules(exclude=None):
    """Gather a list of all modules"""
    if exclude is None:
        exclude = []
    modules = []
    modules_path = f"{os.path.dirname(__file__)}/*.py"
    for module_path in glob.glob(modules_path):
        module = os.path.basename(module_path)
        if "__" not in module and module.endswith(".py"):
            module = module.replace(".py", "")
            if module not in exclude:
                modules.append(module)

    modules.sort()
    return modules


def parse_modules(list_modules=None, custom_modules=None, exclude=None):
    """Import all modules and return them as a dict"""
    if list_modules is None or len(list_modules) == 0:
        list_modules = autoload_modules(exclude)
    if custom_modules is not None and len(custom_modules) > 0:
        list_modules.extend(custom_modules)
    modules = {}
    for module_name in list_modules:
        retries = 10
        while retries >= 0:
            try:
                if module_name.endswith(".py"):
                    if module_name.startswith("http"):
                        logger.info("Downloading custom module: %s", module_name)
                        module_data = requests.get(module_name, timeout=3).content
                        module_basename = os.path.basename(module_name)
                        module_name = f"/tmp/{module_basename}"
                        with open(module_name, "wb") as handler:
                            handler.write(module_data)
                    if os.path.isfile(module_name):
                        spec = spec_from_file_location("Addon", module_name)
                        module_spec = module_from_spec(spec)
                        spec.loader.exec_module(module_spec)
                        addon = getattr(module_spec, "Addon")
                        module_name = os.path.basename(module_name).split(".py")[0]
                    else:
                        logger.error("Can't find custom module: %s", module_name)
                        retries = -1
                        continue
                else:
                    addon = getattr(import_module(f"{__name__}.{module_name}"), "Addon")
                addon.service = module_name
                modules[module_name] = addon
                retries = -1
            except ModuleNotFoundError as err:
                logger.error(
                    "Addon %s is not supported, please remove it from your config: %s",
                    module_name,
                    err,
                )
                retries = -1
            except Exception as err:
                logger.error(
                    "Error with module %s: %s", module_name, err, exc_info=True
                )
                time.sleep(2)
                retries -= 1
    logger.debug("Found addons: %s", ", ".join(modules))
    return modules


def get_modules_info(include=None, exclude=None):
    """Return a list of all available modules"""
    if include is None:
        include = []
    if exclude is None:
        exclude = []
    descriptions = []
    for module in autoload_modules():
        description = import_module(f"{__name__}.{module}").__doc__
        is_enabled = True
        if module in exclude:
            is_enabled = False
        elif len(include) == 0:
            is_enabled = True
        elif len(include) > 0 and module in include:
            is_enabled = True
        else:
            is_enabled = False
        descriptions.append(
            {
                "is_enabled": is_enabled,
                "name": module,
                "description": description,
            }
        )
    return descriptions
