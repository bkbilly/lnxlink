{
  lib,
  stdenv,
  python3Packages,
  makeWrapper,
  versionCheckHook,
  nix-update-script,

  # Runtime programs. Each is optional at run time — lnxlink probes with
  # `which` and disables the corresponding module when a tool is absent — so
  # every group can be switched off to trim the closure.
  alsa-utils,
  coreutils,
  efibootmgr,
  ethtool,
  glib,
  gnused,
  networkmanager,
  power-profiles-daemon,
  psmisc,
  pulseaudio,
  systemd,
  wirelesstools,
  wl-clipboard,
  xclip,
  xdg-utils,
  xdotool,
  xset,
  xsel,
  ydotool,

  # Feature flags. The defaults cover everything a normal desktop install
  # exercises while keeping the closure free of CUDA/OpenCV-sized inputs.
  withDbus ? true, # idle, media, notify, interfaces
  withX11 ? true, # mouse, send_keys, active_window, fullscreen, keyboard_hotkeys
  withAudio ? true, # audio_select, speaker_used, microphone_used
  withDocker ? true, # docker
  withRestApi ? true, # restful
  withSteam ? true, # steam
  withGio ? true, # mounts (remote GVFS mounts)
  withWebcam ? false, # webcam, screenshot — pulls in OpenCV
  withNvidia ? false, # gpu (NVIDIA)
  withAmdGpu ? false, # gpu (AMD)
  withSpeechRecognition ? false, # speech_recognition
  withGpio ? false, # gpio, fingerprint (Raspberry Pi)

  # Escape hatch for custom modules pulled in via `custom_modules`.
  extraPythonPackages ? _ps: [ ],
}:

let
  pyproject = lib.importTOML ../../pyproject.toml;

  # `syscommand` builds shell pipelines, so the basics have to be reachable too.
  baseRuntimeInputs = [
    coreutils
    gnused
    psmisc # fuser — camera_used
    systemd # systemctl, loginctl, shutdown — restart, shutdown, suspend, systemd
  ];

  runtimeInputs =
    baseRuntimeInputs
    ++ lib.optionals withX11 [
      glib # gsettings — keep_alive
      wl-clipboard # wl-copy, wl-paste — clipboard
      xclip
      xdg-utils # xdg-open
      xdotool
      xset # keep_alive, screen_onoff
      xsel
      ydotool
    ]
    ++ lib.optionals withAudio [
      alsa-utils # amixer
      pulseaudio # pactl
    ]
    ++ [
      efibootmgr # boot_select
      ethtool # wol
      networkmanager # nmcli — interfaces
      power-profiles-daemon # powerprofilesctl — power_profile
      wirelesstools # iwgetid — wifi
    ];
in

python3Packages.buildPythonApplication {
  pname = "lnxlink";
  inherit (pyproject.project) version;
  pyproject = true;

  src = lib.fileset.toSource {
    root = ../../.;
    fileset = lib.fileset.unions [
      # `lnxlink/edit.txt` marks a git-checkout install: its presence makes
      # lnxlink stamp the version as "+edit-<hash>" and makes the update
      # entity run `git pull`. Neither is meaningful for a store path.
      (lib.fileset.difference ../../lnxlink (lib.fileset.maybeMissing ../../lnxlink/edit.txt))
      ../../pyproject.toml
      ../../README.md
      ../../LICENSE.md
    ];
  };

  postPatch = ''
    # lnxlink lazily `pip install --break-system-packages`es optional module
    # dependencies on first use. That can never work against an immutable
    # store, and the failure costs a subprocess plus a network timeout on every
    # module load, so short-circuit straight to the import. Anything selected
    # by a `with*` flag below is already on PYTHONPATH; anything else degrades
    # to the module disabling itself, which is the same outcome as a failed
    # install.
    substituteInPlace lnxlink/modules/scripts/helpers.py \
      --replace-fail \
        'if current_version is None or needs_update(current_version, req_version):' \
        'if False:  # patched by nixpkgs: never pip-install at runtime'

    # Teach the self-updater that it is not in charge here. Without this the
    # store path falls through to the "pip" branch and the update entity in
    # Home Assistant would try `pip install -U lnxlink`.
    substituteInPlace lnxlink/files_setup.py \
      --replace-fail \
        'method = "pip"' \
        'method = "nix" if path.startswith("/nix/store") else "pip"'
  '';

  build-system = with python3Packages; [ setuptools ];

  dependencies =
    with python3Packages;
    [
      aiohttp
      beaupy
      distro
      inotify
      jeepney
      paho-mqtt
      psutil
      pyyaml
      requests
    ]
    ++ lib.optionals withDbus [
      dbus-idle
      dbus-mediaplayer
      dbus-networkdevices
      dbus-notification
    ]
    ++ lib.optionals withX11 [
      ewmh
      python-xlib
      xlib-hotkeys
    ]
    ++ lib.optionals withAudio [
      pulsectl
      pyalsaaudio
    ]
    ++ lib.optional withDocker docker
    ++ lib.optionals withRestApi [
      flask
      waitress
    ]
    ++ lib.optional withSteam vdf
    ++ lib.optional withGio pygobject3
    ++ lib.optional withWebcam opencv-python
    ++ lib.optionals withNvidia [
      nvitop
      nvsmi
    ]
    ++ lib.optional withAmdGpu pyamdgpuinfo
    ++ lib.optionals withSpeechRecognition [
      # The module hard-fails without PyAudio, before it ever reaches
      # SpeechRecognition itself.
      pyaudio
      pyalsaaudio
      speechrecognition
    ]
    ++ lib.optionals withGpio [
      pigpio
      pyserial
      rpi-gpio
    ]
    ++ extraPythonPackages python3Packages;

  nativeBuildInputs = [ makeWrapper ];

  # Suffix rather than prefix: on NixOS the running system's systemd and the
  # driver-matched nvidia-smi must keep winning over anything vendored here.
  makeWrapperArgs = [
    "--suffix"
    "PATH"
    ":"
    (lib.makeBinPath runtimeInputs)
  ];

  # There is no test suite in the source tree; `testpaths` points at a
  # directory that upstream does not ship.
  doCheck = false;

  pythonImportsCheck = [
    "lnxlink"
    "lnxlink.modules"
  ];

  nativeInstallCheckInputs = [ versionCheckHook ];
  versionCheckProgramArg = "--version";
  doInstallCheck = true;

  passthru = {
    inherit runtimeInputs;
    updateScript = nix-update-script { };
  };

  meta = {
    description = "Internet of Things integration with Linux using MQTT";
    longDescription = ''
      LNXlink exposes a Linux machine to Home Assistant over MQTT: system
      monitoring, media control, notifications, shutdown/suspend, screen
      capture and more, using Home Assistant's MQTT discovery.
    '';
    homepage = "https://github.com/bkbilly/lnxlink";
    changelog = "https://github.com/bkbilly/lnxlink/releases";
    license = lib.licenses.mit;
    mainProgram = "lnxlink";
    platforms = lib.platforms.linux;
    # Several modules read /proc and /sys layouts that only exist on Linux.
    broken = !stdenv.hostPlatform.isLinux;
  };
}
