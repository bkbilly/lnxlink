from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
import time
import traceback


def parse_modules(list_modules):
    modules = {}
    for module_name in list_modules:
        retries = 10
        while retries >= 0:
            try:
                addon = getattr(import_module(f"{__name__}.{module_name}"), 'Addon')
                addon.service = module_name
                modules[module_name] = addon
                retries = -1
                print(f"Successfully loaded addon: {module_name}")
            except Exception as e:
                print("----------------")
                print(f"Error with module: {module_name}")
                traceback.print_exc()
                time.sleep(2)
                retries -= 1
    return modules
