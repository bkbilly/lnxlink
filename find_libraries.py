"""Parses all requirements to a file"""
# pylint: skip-file

import re
import sys
import glob

modules_dependancies = set()
pattern = re.compile(r"import_install_package\(\s*\"(\S+)\", \s*\"(\S+)\"")
modules = glob.glob("lnxlink/modules/*.py", recursive=False)
for module in modules:
    with open(module, encoding="UTF-8") as file:
        match = re.findall(pattern, file.read())
        for requirement, version in match:
            modules_dependancies.add(f"{requirement}{version}")
modules_dependancies = list(modules_dependancies)
modules_dependancies.sort()

with open("pyproject.toml", encoding="UTF-8") as file:
    # Find dependencies section
    match = re.search(r"dependencies = \[(.*?)\]", file.read(), re.DOTALL)
    system_dependancies = []
    if match:
        system_dependancies = re.findall(r'"([^"]*)"', match.group(1))
system_dependancies.sort()

new_requirements = ""
new_requirements += "# System dependencies\n"
for dependency in system_dependancies:
    new_requirements += f"{dependency}\n"
new_requirements += "\n"
new_requirements += "# Modules dependencies\n"
for requirement in modules_dependancies:
    new_requirements += f"{requirement}\n"

with open("requirements.txt", encoding="UTF-8") as file:
    prev_requirements = file.read()

with open("requirements.txt", "w", encoding="UTF-8") as file:
    file.writelines(new_requirements)

if prev_requirements != new_requirements:
    sys.exit(10)
