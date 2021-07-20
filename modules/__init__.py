from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
import time
import traceback

modules = {}

# iterate through the modules in the current package
package_dir = str(Path(__file__).resolve().parent)
for (_, module_name, _) in iter_modules([package_dir]):
    retries = 10
    while retries >= 0:
        try:
            addons = getattr(import_module(f"{__name__}.{module_name}"), 'Addon')
            modules[module_name] = addons
            retries = -1
        except Exception as e:
            traceback.print_exc()
            time.sleep(2)
            retries -= 1
