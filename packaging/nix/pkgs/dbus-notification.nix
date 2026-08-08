{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
  jeepney,
}:

buildPythonPackage rec {
  pname = "dbus-notification";
  version = "2026.7.0";
  pyproject = true;

  src = fetchPypi {
    pname = "dbus_notification";
    inherit version;
    hash = "sha256-W/503FQPlOdV7gXOCn8obpSGhXmrIeGzScZfeKNk30g=";
  };

  build-system = [ setuptools ];

  dependencies = [ jeepney ];

  # The bundled tests talk to a real notification daemon.
  doCheck = false;

  pythonImportsCheck = [ "dbus_notification" ];

  meta = {
    description = "Send desktop notifications over D-Bus";
    homepage = "https://github.com/bkbilly/dbus-notification";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}
