{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
  nvidia-ml-py,
  psutil,
}:

buildPythonPackage rec {
  pname = "nvitop";
  version = "1.7.1";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-OAMRKh1KfgGYmuW/Wl5C8DZr95HWitjjsYWdftdHFAw=";
  };

  build-system = [ setuptools ];

  # Upstream caps nvidia-ml-py to match a specific CUDA release; nixpkgs ships a
  # single newer version and lnxlink only uses the stable query API.
  pythonRelaxDeps = [ "nvidia-ml-py" ];

  dependencies = [
    nvidia-ml-py
    psutil
  ];

  # Needs an actual NVIDIA device and driver.
  doCheck = false;

  pythonImportsCheck = [ "nvitop" ];

  meta = {
    description = "Interactive NVIDIA-GPU process viewer and library";
    homepage = "https://github.com/XuehaiPan/nvitop";
    license = with lib.licenses; [
      asl20
      gpl3Only
    ];
    mainProgram = "nvitop";
    platforms = lib.platforms.linux;
  };
}
