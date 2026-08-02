{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.services.lnxlink;

  settingsFormat = pkgs.formats.yaml { };
  generatedConfig = settingsFormat.generate "lnxlink.yaml" cfg.settings;

  # Either an unmanaged file the user maintains, or the generated one.
  sourceConfig = if cfg.configFile != null then cfg.configFile else generatedConfig;

  stateDir = "lnxlink";

  # lnxlink rewrites its own config to fill in defaults for every module it
  # loads, so it cannot run against a read-only store path. Seed a writable
  # copy in the state directory instead.
  #
  # `%S` expands to /var/lib for system units and $XDG_STATE_HOME for user
  # units, which is exactly the split we want.
  runtimeConfig = "%S/${stateDir}/config.yaml";

  args = lib.escapeShellArgs (
    [
      "--config"
      runtimeConfig
      # The NixOS unit *is* the service definition; never let lnxlink write one
      # into ~/.config/systemd or /etc/systemd.
      "--ignore-systemd"
      "--logging"
      cfg.logLevel
      "--log-directory"
      "%S/${stateDir}"
      "--registry-path"
      "%S/${stateDir}/discovery-registry.json"
    ]
    ++ cfg.extraArgs
  );

  seedConfig = pkgs.writeShellScript "lnxlink-seed-config" ''
    set -eu
    config="$STATE_DIRECTORY/config.yaml"
    ${
      if cfg.mutableConfig then
        ''
          if [ ! -e "$config" ]; then
            install -m 0600 ${sourceConfig} "$config"
          fi
        ''
      else
        ''
          install -m 0600 ${sourceConfig} "$config"
        ''
    }
  '';

  serviceConfig = {
    Type = "simple";
    ExecStartPre = "${seedConfig}";
    ExecStart = "${lib.getExe cfg.package} ${args}";
    Restart = "always";
    RestartSec = 5;
    StateDirectory = stateDir;
    StateDirectoryMode = "0700";
  }
  // lib.optionalAttrs (cfg.environmentFile != null) { EnvironmentFile = cfg.environmentFile; };
in
{
  options.services.lnxlink = {
    enable = lib.mkEnableOption "LNXlink, a Linux to Home Assistant MQTT bridge";

    package = lib.mkPackageOption pkgs "lnxlink" { };

    mode = lib.mkOption {
      type = lib.types.enum [
        "user"
        "system"
      ];
      default = "user";
      description = ''
        Whether to run LNXlink as a systemd *user* service or a *system*
        service.

        `user` is what you want on a desktop: modules such as `media`,
        `notify`, `idle`, `screenshot` and `send_keys` need the session D-Bus
        and the X11/Wayland display, both of which only exist inside a user
        session.

        `system` suits headless machines. Session-scoped modules will be
        unavailable, so exclude them in {option}`services.lnxlink.settings`.
      '';
    };

    autoStart = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Start the user service automatically with every graphical session, for
        {option}`services.lnxlink.mode` = `"user"`.

        NixOS user units are defined system-wide, so this applies to every user
        who logs in graphically. Set it to `false` to install the unit without
        activating it — individual users can then run
        {command}`systemctl --user enable --now lnxlink`. For genuinely
        per-user control, use the Home Manager module instead.
      '';
    };

    user = lib.mkOption {
      type = lib.types.str;
      default = "root";
      description = ''
        User the system service runs as, for
        {option}`services.lnxlink.mode` = `"system"`.

        The default of `root` matches upstream: `shutdown`, `suspend`,
        `boot_select` and `wol` all need privileges. Point this at an
        unprivileged account if you exclude those modules.
      '';
    };

    settings = lib.mkOption {
      inherit (settingsFormat) type;
      default = { };
      example = lib.literalExpression ''
        {
          mqtt = {
            prefix = "lnxlink";
            clientId = "desktop";
            server = "192.168.1.10";
            port = 1883;
            discovery.enabled = true;
          };
          update_interval = 5;
          exclude = [ "gpu" "webcam" ];
        }
      '';
      description = ''
        Contents of `config.yaml`, rendered to YAML.

        Do not put credentials here — everything in {file}`/nix/store` is
        world-readable. Use {option}`services.lnxlink.environmentFile` with
        `LNXLINK_MQTT_USER` / `LNXLINK_MQTT_PASS` instead.

        See <https://bkbilly.gitbook.io/lnxlink> for the full schema. LNXlink
        fills in any key it needs but does not find.
      '';
    };

    configFile = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      description = ''
        Use this file as the configuration instead of rendering
        {option}`services.lnxlink.settings`. Mutually exclusive with it.
      '';
    };

    mutableConfig = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        By default the configuration is re-seeded from the Nix-generated file
        on every start, so the deployed state always matches the
        configuration — and any change LNXlink or Home Assistant wrote back
        into `config.yaml` is discarded.

        Set this to `true` to seed the file only once and then leave it alone.
        Settings adjusted from the Home Assistant UI then survive restarts, at
        the cost of {option}`services.lnxlink.settings` no longer being
        authoritative after the first start.
      '';
    };

    environmentFile = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      example = "/run/secrets/lnxlink.env";
      description = ''
        Path to a file with `KEY=value` lines, read by systemd and kept out of
        the Nix store. LNXlink reads these on startup:

        `LNXLINK_MQTT_SERVER`, `LNXLINK_MQTT_PORT`, `LNXLINK_MQTT_USER`,
        `LNXLINK_MQTT_PASS`, `LNXLINK_MQTT_PREFIX`, `LNXLINK_MQTT_CLIENTID`.

        For a user service the file must be readable by that user.
      '';
    };

    logLevel = lib.mkOption {
      type = lib.types.enum [
        "DEBUG"
        "INFO"
        "WARNING"
        "ERROR"
        "CRITICAL"
      ];
      default = "INFO";
      description = "Log level passed to LNXlink.";
    };

    extraArgs = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [
        "--exclude"
        "gpu,webcam"
      ];
      description = "Extra command line arguments for {command}`lnxlink`.";
    };

    openFirewall = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Open the port used by the `restful` module
        (`settings.restful.port`, 8112 by default).
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = !(cfg.configFile != null && cfg.settings != { });
        message = "services.lnxlink: set either `configFile` or `settings`, not both.";
      }
      {
        assertion = cfg.mode == "user" -> cfg.user == "root";
        message = "services.lnxlink: `user` only applies when `mode = \"system\"`.";
      }
    ];

    warnings = lib.optional (cfg.configFile == null && cfg.settings == { }) ''
      services.lnxlink is enabled but no configuration was given. LNXlink will
      generate a template pointing at 192.168.1.1 and fail to reach a broker.
      Set services.lnxlink.settings.mqtt.server.
    '';

    environment.systemPackages = [ cfg.package ];

    networking.firewall.allowedTCPPorts = lib.optional cfg.openFirewall (
      cfg.settings.settings.restful.port or 8112
    );

    systemd.user.services.lnxlink = lib.mkIf (cfg.mode == "user") {
      description = "LNXlink - Linux integration for Home Assistant";
      documentation = [ "https://bkbilly.gitbook.io/lnxlink" ];
      after = [
        "network-online.target"
        "graphical-session.target"
      ];
      wants = [ "network-online.target" ];
      partOf = [ "graphical-session.target" ];
      wantedBy = lib.optional cfg.autoStart "graphical-session.target";
      inherit serviceConfig;
    };

    systemd.services.lnxlink = lib.mkIf (cfg.mode == "system") {
      description = "LNXlink - Linux integration for Home Assistant";
      documentation = [ "https://bkbilly.gitbook.io/lnxlink" ];
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = serviceConfig // {
        User = cfg.user;
      };
    };
  };
}
