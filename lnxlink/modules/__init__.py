from importlib import import_module
import time
import traceback
import glob
import os
import sys


def autoload_modules():
    modules = []
    modules_path = f"{os.path.dirname(__file__)}/*.py"
    for module_path in glob.glob(modules_path):
        module = os.path.basename(module_path)
        if '__' not in module and '.py' in module:
            modules.append(module.replace('.py', ''))

    return modules


def parse_modules(list_modules=None):
    if list_modules is None:
        list_modules = autoload_modules()
    modules = {}
    for module_name in list_modules:
        retries = 10
        while retries >= 0:
            try:
                if '.py' in module_name:
                    module_path = os.path.dirname(module_name)
                    module_basename = os.path.basename(module_name)
                    module_name = os.path.splitext(module_basename)[0]
                    sys.path.append(module_path)
                    addon = getattr(import_module(f"{module_name}"), 'Addon')
                else:
                    addon = getattr(import_module(f"{__name__}.{module_name}"), 'Addon')
                addon.service = module_name
                modules[module_name] = addon
                retries = -1
                print(f"Loaded addon: {module_name}")
            except ModuleNotFoundError as e:
                print(f"Addon {module_name} is not supported, please remove it from your config")
                print(e)
                retries = -1
            except Exception as e:
                print("----------------")
                print(f"Error with module: {module_name}")
                traceback.print_exc()
                time.sleep(2)
                retries -= 1
    return modules
