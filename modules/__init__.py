from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module

modules = {}

# iterate through the modules in the current package
package_dir = Path(__file__).resolve().parent
for (_, module_name, _) in iter_modules([package_dir]):
    addons = getattr(import_module(f"{__name__}.{module_name}"), 'Addon')
    modules[module_name] = addons
