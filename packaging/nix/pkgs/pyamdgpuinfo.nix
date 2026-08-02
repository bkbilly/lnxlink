{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
  cython,
  libdrm,
}:

buildPythonPackage rec {
  pname = "pyamdgpuinfo";
  version = "2.1.8";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-44mYHwC/Qv3kEjOViiHGKIhTpGx9/nsGKyq+BUz7HXs=";
  };

  # setup.py hardcodes the Debian include path for libdrm.
  postPatch = ''
    substituteInPlace setup.py \
      --replace-fail '"/usr/include/libdrm"' '"${lib.getDev libdrm}/include/libdrm"'
  '';

  build-system = [
    setuptools
    cython
  ];

  buildInputs = [ libdrm ];

  # Needs a real amdgpu device node.
  doCheck = false;

  pythonImportsCheck = [ "pyamdgpuinfo" ];

  meta = {
    description = "AMD GPU stats read straight from libdrm_amdgpu";
    homepage = "https://github.com/mark9064/pyamdgpuinfo";
    license = lib.licenses.gpl3Only;
    platforms = lib.platforms.linux;
  };
}
