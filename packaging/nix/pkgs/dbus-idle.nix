{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
  jeepney,
}:

buildPythonPackage rec {
  pname = "dbus-idle";
  version = "2026.8.0";
  pyproject = true;

  src = fetchPypi {
    pname = "dbus_idle";
    inherit version;
    hash = "sha256-ZzPVJYgzmhoA6+gm7+ZRw9JK6/2etLwlU5uPKzg2bbw=";
  };

  build-system = [ setuptools ];

  dependencies = [ jeepney ];

  # Requires a live D-Bus session bus.
  doCheck = false;

  pythonImportsCheck = [ "dbus_idle" ];

  meta = {
    description = "Get the idle time of a user session over D-Bus";
    homepage = "https://github.com/bkbilly/dbus-idle";
    license = lib.licenses.bsd3;
    platforms = lib.platforms.linux;
  };
}
