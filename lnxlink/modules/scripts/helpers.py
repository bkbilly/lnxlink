"""A collection of helper functions"""
import importlib.metadata
import logging
import os
import shutil
import subprocess
import sys

logger = logging.getLogger("lnxlink")


def _get_installer():
    """Get the installer tool name from package metadata"""
    try:
        dist = importlib.metadata.distribution("lnxlink")
        installer_file = dist.read_text("INSTALLER")
        if installer_file:
            return installer_file.strip()
    except Exception:
        pass
    return ""


def get_install_method():
    """Detect how lnxlink was installed"""
    path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    installer = _get_installer()
    if os.environ.get("FLATPAK_ID"):
        method = "flatpak"
    elif os.path.exists("/.dockerenv"):
        method = "docker"
    elif "pipx" in path:
        method = "pipx"
    elif "/uv/" in path or installer == "uv":
        method = "uv"
    elif (
        path.startswith("/usr/lib")
        and syscommand("pacman -Qq python-lnxlink", ignore_errors=True)[2] == 0
    ):
        method = "aur"
    elif path.startswith("/usr/lib"):
        method = "system"
    else:
        method = "pip"

    if os.path.exists(os.path.join(path, "lnxlink/edit.txt")):
        method += "_edit"

    return method


def get_version():
    """Get the current version and the path of the app"""
    pkg_name = __package__.split(".", maxsplit=1)[0] if __package__ else __name__
    try:
        version = importlib.metadata.version(pkg_name)
    except importlib.metadata.PackageNotFoundError:
        version = importlib.metadata.version("lnxlink")
    path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    if os.path.exists(os.path.join(path, "lnxlink/edit.txt")):
        version += "+edit"
        git_hash, _, return_code = syscommand(
            f"git -c safe.directory=* -C {path} rev-parse --short HEAD",
            ignore_errors=True,
        )
        if return_code == 0:
            version += f"-{git_hash}"
    return version, path


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


def find_uv_bin():
    """Find the path to the uv binary, checking PATH, SUDO_USER, sys.executable, and user home dirs"""
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path

    homes = [os.path.expanduser("~")]

    # Check SUDO_USER home if running under sudo/root
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        homes.append(os.path.expanduser(f"~{sudo_user}"))
        homes.append(f"/home/{sudo_user}")

    # Infer home directory from sys.executable if located under /home/
    if sys.executable.startswith("/home/"):
        parts = sys.executable.split("/")
        if len(parts) >= 3:
            homes.append(f"/home/{parts[2]}")

    # Check user directories under /home/
    if os.path.exists("/home"):
        try:
            for user in os.listdir("/home"):
                homes.append(os.path.join("/home", user))
        except Exception:
            pass

    candidates = []
    for home in homes:
        candidates.extend(
            [
                os.path.join(home, ".local", "bin", "uv"),
                os.path.join(home, ".cargo", "bin", "uv"),
            ]
        )
    candidates.extend(
        [
            "/usr/local/bin/uv",
            "/usr/bin/uv",
        ]
    )

    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


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
        uv_bin = find_uv_bin()
        returncode = -1
        if uv_bin:
            args = [
                uv_bin,
                "pip",
                "install",
                "--python",
                sys.executable,
                "--break-system-packages",
                "-U",
                "--quiet",
                package_version,
            ]
            _, _, returncode = syscommand(args, ignore_errors=True, timeout=None)

        if returncode != 0:
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
