{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
  jeepney,
}:

buildPythonPackage rec {
  pname = "dbus-networkdevices";
  version = "2026.7.0";
  pyproject = true;

  src = fetchPypi {
    pname = "dbus_networkdevices";
    inherit version;
    hash = "sha256-SrKC+KZsgrOQ18WO8PfTk6GObObM2KJNN6ppJr32EIU=";
  };

  build-system = [ setuptools ];

  dependencies = [ jeepney ];

  # Requires a live system bus with NetworkManager.
  doCheck = false;

  pythonImportsCheck = [ "dbus_networkdevices" ];

  meta = {
    description = "List NetworkManager devices over D-Bus";
    homepage = "https://github.com/bkbilly/dbus-networkdevices";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}
