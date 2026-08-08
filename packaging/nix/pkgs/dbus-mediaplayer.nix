{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
  jeepney,
}:

buildPythonPackage rec {
  pname = "dbus-mediaplayer";
  version = "2026.7.0";
  pyproject = true;

  src = fetchPypi {
    pname = "dbus_mediaplayer";
    inherit version;
    hash = "sha256-LKr/DdnceXfmS7V03HoiOEWshRdFJltoDetYap31ZOU=";
  };

  build-system = [ setuptools ];

  dependencies = [ jeepney ];

  # Requires a live D-Bus session bus with an MPRIS player.
  doCheck = false;

  pythonImportsCheck = [ "dbus_mediaplayer" ];

  meta = {
    description = "Read and control MPRIS media players over D-Bus";
    homepage = "https://github.com/bkbilly/dbus-mediaplayer";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}
