{
  lib,
  buildPythonPackage,
  fetchPypi,
  poetry-core,
}:

buildPythonPackage rec {
  pname = "nvsmi";
  version = "0.4.2";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-waORx8Ta3G7FcpCf8DckUdRk663BROWqX7vMiT3Le/o=";
  };

  # Upstream still declares the pre-1.0 `poetry.masonry` backend, which no
  # longer ships with poetry-core. The metadata itself is plain poetry, so
  # pointing it at the modern backend is enough.
  postPatch = ''
    substituteInPlace pyproject.toml \
      --replace-fail 'requires = ["poetry>=0.12"]' 'requires = ["poetry-core"]' \
      --replace-fail 'build-backend = "poetry.masonry.api"' 'build-backend = "poetry.core.masonry.api"'
  '';

  build-system = [ poetry-core ];

  # Every test shells out to a real nvidia-smi.
  doCheck = false;

  pythonImportsCheck = [ "nvsmi" ];

  meta = {
    description = "User-friendly wrapper around nvidia-smi";
    homepage = "https://github.com/pmav99/nvsmi";
    license = lib.licenses.mit;
    mainProgram = "nvsmi";
    platforms = lib.platforms.linux;
  };
}
