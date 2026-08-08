# Nix packaging

A flake that packages LNXlink, ships NixOS and Home Manager service modules,
and covers both with a VM integration test.

```
flake.nix                     # at the repository root — Nix requires it there
packaging/nix/
├── package.nix               # the lnxlink derivation
├── overlay.nix               # lnxlink + the Python deps missing from nixpkgs
├── nixos-module.nix          # services.lnxlink for NixOS
├── home-manager-module.nix   # services.lnxlink for Home Manager
├── pkgs/                     # Python packages not yet in nixpkgs
└── tests/integration.nix     # NixOS VM test against a real MQTT broker
```

## Try it

```console
$ nix run github:bkbilly/lnxlink -- --config ./config.yaml --ignore-systemd
```

`--ignore-systemd` matters: without it LNXlink writes a unit file into
`~/.config/systemd/user` pointing at a store path that a later garbage
collection will remove.

## Install as a service

### NixOS

```nix
{
  inputs.lnxlink.url = "github:bkbilly/lnxlink";

  outputs = { nixpkgs, lnxlink, ... }: {
    nixosConfigurations.desktop = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        lnxlink.nixosModules.default
        {
          services.lnxlink = {
            enable = true;
            settings = {
              mqtt = {
                server = "192.168.1.10";
                port = 1883;
                clientId = "desktop";
                discovery.enabled = true;
              };
              update_interval = 5;
            };
            # Credentials stay out of the world-readable store.
            environmentFile = "/run/secrets/lnxlink.env";
          };
        }
      ];
    };
  };
}
```

with `/run/secrets/lnxlink.env`:

```sh
LNXLINK_MQTT_USER=homeassistant
LNXLINK_MQTT_PASS=hunter2
```

`LNXLINK_MQTT_SERVER`, `LNXLINK_MQTT_PORT`, `LNXLINK_MQTT_PREFIX` and
`LNXLINK_MQTT_CLIENTID` work the same way.

The module defaults to `mode = "user"` — a systemd **user** service bound to
`graphical-session.target`. That is what you want on a desktop: `media`,
`notify`, `idle`, `screenshot`, `send_keys` and friends need the session bus
and the display, neither of which a system service can see. Use
`mode = "system"` on headless machines and exclude those modules.

### Home Manager

```nix
{
  imports = [ lnxlink.homeModules.default ];

  # The Home Manager module does not carry the overlay; either add it to
  # nixpkgs.overlays or set the package directly.
  services.lnxlink = {
    enable = true;
    package = lnxlink.packages.${pkgs.system}.default;
    settings.mqtt = {
      server = "192.168.1.10";
      clientId = "laptop";
    };
  };
}
```

### Configuration lifecycle

LNXlink rewrites `config.yaml` at runtime to backfill defaults for every module
it loads, so it cannot run against a store path. Both modules seed a writable
copy into the service's `StateDirectory` (`/var/lib/lnxlink` for a system
service, `~/.local/state/lnxlink` for a user one) and point `--config` at that.

By default the copy is refreshed on **every** start, so `settings` stays
authoritative and rebuilds are reproducible — at the cost of discarding
anything Home Assistant wrote back. Set `mutableConfig = true` to seed once and
then leave the file alone.

## Package variants

| Attribute | What it adds |
| --- | --- |
| `packages.default` / `packages.lnxlink` | Desktop defaults: D-Bus, X11, audio, Docker, REST API, Steam, GIO |
| `packages.lnxlink-full` | Also OpenCV, NVIDIA, AMD GPU and speech recognition |
| `packages.lnxlink-headless` | Drops X11, audio and GIO |

Every group is an override, so you can mix freely:

```nix
pkgs.lnxlink.override {
  withNvidia = true;
  withSteam = false;
  # For anything listed under `custom_modules:` in config.yaml.
  extraPythonPackages = ps: [ ps.paramiko ];
}
```

| Flag | Default | Modules |
| --- | --- | --- |
| `withDbus` | `true` | `idle`, `media`, `notify`, `interfaces` |
| `withX11` | `true` | `mouse`, `send_keys`, `active_window`, `fullscreen`, `keyboard_hotkeys`, `clipboard` |
| `withAudio` | `true` | `audio_select`, `speaker_used`, `microphone_used` |
| `withDocker` | `true` | `docker` |
| `withRestApi` | `true` | `restful` |
| `withSteam` | `true` | `steam` |
| `withGio` | `true` | `mounts` |
| `withWebcam` | `false` | `webcam`, `screenshot` (pulls in OpenCV) |
| `withNvidia` | `false` | `gpu` on NVIDIA |
| `withAmdGpu` | `false` | `gpu` on AMD |
| `withSpeechRecognition` | `false` | `speech_recognition` |
| `withGpio` | `false` | `gpio`, `fingerprint` |

Each flag controls both the Python dependencies and the command line tools
added to the wrapper's `PATH`. The `PATH` is *suffixed*, never prefixed, so the
running system's `systemctl` and its driver-matched `nvidia-smi` keep
precedence over anything vendored here.

## Deviations from upstream

Two behaviours do not survive contact with an immutable store, so
`package.nix` patches them:

* **Runtime `pip install`.** Optional module dependencies are normally fetched
  with `pip install --break-system-packages` on first use. That can never
  succeed against `/nix/store`, and the failed attempt costs a subprocess and a
  network timeout per module load, so the installer is short-circuited straight
  to the import. Whatever a `with*` flag selected is already importable;
  anything else disables its module, exactly as a failed install would.

* **Self-update.** `get_install_method` would classify a store path as a `pip`
  install, and the Home Assistant update entity would then run
  `pip install -U lnxlink`. It now reports `nix`, and the update entity logs
  that updates are managed elsewhere.

`lnxlink/edit.txt` — the marker for a git-checkout install — is excluded from
the packaged source, so the version is not stamped `+edit-<hash>` and the
update entity does not try to `git pull` the store path.

## Known limitations

* `screenshot` shells out to `flatpak run com.dec05eba.gpu_screen_recorder` and
  refuses to load without it. The native `pkgs.gpu-screen-recorder` is not a
  substitute; enable `services.flatpak` and install that app to use the module.
* `sys_updates` looks for `apt`, `dnf` or `pacman` and stays disabled on NixOS.
* `boot_select` and `wol` invoke `sudo -n efibootmgr` / `sudo ethtool`; grant
  those through `security.sudo.extraRules` if you need them.
* The `fingerprint` module's `adafruit-circuitpython-fingerprint` dependency is
  not packaged — it is Raspberry-Pi-only and pulls in the whole Blinka stack.

## Development

```console
$ nix develop          # python env with every dependency, plus ruff + pre-commit
$ nix fmt              # format the Nix files
$ nix flake check -L   # build, evaluate both modules, check formatting, run the VM test
$ nix build .#checks.x86_64-linux.integration -L   # just the VM test
```

`packaging/nix/pkgs/` holds the eight Python packages nixpkgs does not carry:
`dbus-idle`, `dbus-mediaplayer`, `dbus-networkdevices`, `dbus-notification`,
`xlib-hotkeys`, `nvitop`, `nvsmi` and `pyamdgpuinfo`. The overlay prefers the
nixpkgs attribute whenever one appears upstream, so each file can simply be
deleted once that happens.

The package version is read from `pyproject.toml`, so a release bump needs no
change here.
