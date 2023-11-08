"""A collection of helper functions"""
import sys
import logging
import subprocess

logger = logging.getLogger("lnxlink")


def syscommand(command, ignore_errors=False, timeout=3):
    """Global subprocess command"""
    if isinstance(command, list):
        command = " ".join(command)
    result = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )
    stderr = result.stderr.decode("UTF-8").strip()
    stdout = result.stdout.decode("UTF-8").strip()
    returncode = result.returncode
    if returncode != 0 and ignore_errors is False:
        logger.error("Error with command: %s (%s)", command, stderr)
    return stdout, stderr, returncode


def import_install_package(package, version="", syspackage=None):
    """Imports a system package and if it doesn't exist, it gets installed"""
    if syspackage is None:
        syspackage = package
    try:
        return __import__(syspackage)
    except ImportError:
        package_version = package + version
        logger.error("Package %s is not installed, installing now...", package_version)
        args = [sys.executable, "-m", "pip", "install", "--quiet", package_version]
        _, stderr, returncode = syscommand(args)
        if returncode != 0:
            logger.error("Can't install package %s: %s", package, stderr)
            return None
    return __import__(syspackage)
