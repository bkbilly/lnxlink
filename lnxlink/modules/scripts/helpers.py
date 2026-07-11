"""A collection of helper functions"""
import importlib.metadata
import logging
import os
import subprocess
import sys

logger = logging.getLogger("lnxlink")


# pylint: disable=consider-using-with
def syscommand(command, ignore_errors=False, timeout=3, background=False):
    """Global subprocess command"""
    logger.debug("Executing command: %s", command)

    if isinstance(command, list):
        command = " ".join(command)

    if background:
        subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return "", "", 0

    stdout = b""
    stderr = b""
    returncode = 0
    timed_out = False

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            timeout=timeout,
        )
        stdout = result.stdout
        stderr = result.stderr
        returncode = result.returncode

    except subprocess.TimeoutExpired as err:
        stdout = err.stdout or b""
        stderr = err.stderr or b""
        returncode = -1
        timed_out = True

    stdout = stdout.decode("UTF-8", errors="replace").strip()
    stderr = stderr.decode("UTF-8", errors="replace").strip()

    if timed_out:
        timeout_msg = f"Command timed out after {timeout} seconds"
        stderr = f"{stderr}\n{timeout_msg}".strip()

    if returncode != 0 and ignore_errors is False:
        if timed_out:
            logger.error("Timeout with command: %s (%s)", command, stderr)
        else:
            logger.error("Error with command: %s (%s)", command, stderr)

    return stdout, stderr, returncode


def import_install_package(package, req_version="", syspackage=None):
    """Imports a system package and if it doesn't exist, it gets installed"""
    if syspackage is None:
        syspackage = package

    try:
        current_version = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        current_version = None

    if current_version is None or needs_update(current_version, req_version):
        package_version = f"'{package}{req_version}'"
        logger.info("Installing %s...", package_version)
        args = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--break-system-packages",
            "-U",
            "--quiet",
            package_version,
        ]
        _, _, returncode = syscommand(args, ignore_errors=True, timeout=None)
        if returncode != 0:
            try:
                if isinstance(syspackage, tuple):
                    return __import__(syspackage[0], fromlist=syspackage[1])
                return __import__(syspackage)
            except ModuleNotFoundError:
                logger.error("Can't install package %s", package)
                return None

    try:
        if isinstance(syspackage, tuple):
            return __import__(syspackage[0], fromlist=syspackage[1])
        return __import__(syspackage)
    except Exception as err:
        logger.error("Can't import package %s: %s", package, err)
        return None


def needs_update(current_version, request_version):
    """Compares two version strings"""
    current_version = str(current_version).strip("><=~")
    request_version = str(request_version).strip("><=~")
    try:
        current_versions = [int(version) for version in current_version.split(".")]
    except (TypeError, ValueError):
        current_versions = [0]
    if request_version is None or request_version == "":
        return False
    try:
        request_versions = [int(version) for version in request_version.split(".")]
    except (TypeError, ValueError):
        return False
    for num in range(max(len(current_versions), len(request_versions))):
        cur_version = current_versions[num] if num < len(current_versions) else 0
        req_version = request_versions[num] if num < len(request_versions) else 0
        if req_version > cur_version:
            return True
        if req_version < cur_version:
            return False
    return False


def get_display_variable():
    """Get the DISPLAY variable"""
    display_var = os.environ.get("DISPLAY")
    if display_var:
        return display_var
    display_var, _, _ = syscommand("echo $DISPLAY")
    if display_var:
        return display_var
    other_displays, _, _ = syscommand(
        "sed -zn 's/^DISPLAY=//p' /proc/*/environ 2> /dev/null | LC_ALL=C sort -zu | tr '\\0' '\\n'"
    )
    other_displays = other_displays.split("\n")
    if len(other_displays) > 0:
        if other_displays[0] == "":
            other_displays[0] = None
        return other_displays[0]
    return None


def text_to_topic(text):
    """Used for setting a text to be sent to mqtt topic"""
    text = text.lower()
    text = text.replace(" ", "_")
    text = text.replace("+", "")
    text = text.replace("*", "")
    text = text.replace("(", "")
    text = text.replace(")", "")
    text = text.replace("@", "")
    text = text.replace(":", "")
    text = text.replace("'", "")
    text = text.replace(".", "")
    return text
