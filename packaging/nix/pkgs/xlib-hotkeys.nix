{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
  python-xlib,
}:

buildPythonPackage rec {
  pname = "xlib-hotkeys";
  version = "2024.3.0";
  pyproject = true;

  src = fetchPypi {
    pname = "xlib_hotkeys";
    inherit version;
    hash = "sha256-KRGoZ45OgU5UOMZImTDIrgTXFPzaAN0N/IvHeonW2UU=";
  };

  # Upstream pins its build backend to a long-superseded setuptools/wheel
  # pair. The package itself is a plain pure-Python build.
  postPatch = ''
    substituteInPlace pyproject.toml \
      --replace-fail 'requires = ["setuptools~=68.0.0", "wheel~=0.40.0"]' 'requires = ["setuptools"]'
  '';

  build-system = [ setuptools ];

  dependencies = [ python-xlib ];

  # Needs a running X server.
  doCheck = false;

  pythonImportsCheck = [ "xlib_hotkeys" ];

  meta = {
    description = "Global hotkey capture for X11 built on python-xlib";
    homepage = "https://github.com/bkbilly/xlib_hotkeys";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}
