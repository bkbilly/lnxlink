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

  sourceConfig = if cfg.configFile != null then cfg.configFile else generatedConfig;

  stateDir = "lnxlink";
  runtimeConfig = "%S/${stateDir}/config.yaml";

  args = lib.escapeShellArgs (
    [
      "--config"
      runtimeConfig
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
in
{
  options.services.lnxlink = {
    enable = lib.mkEnableOption "LNXlink, a Linux to Home Assistant MQTT bridge";

    package = lib.mkPackageOption pkgs "lnxlink" { };

    settings = lib.mkOption {
      inherit (settingsFormat) type;
      default = { };
      example = lib.literalExpression ''
        {
          mqtt = {
            prefix = "lnxlink";
            clientId = "laptop";
            server = "192.168.1.10";
            port = 1883;
            discovery.enabled = true;
          };
          update_interval = 5;
        }
      '';
      description = ''
        Contents of `config.yaml`, rendered to YAML.

        Keep credentials out of this — the generated file lands in the
        world-readable Nix store. Use
        {option}`services.lnxlink.environmentFile` instead.
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
        Seed `config.yaml` only when it is missing, instead of overwriting it
        on every start. Lets settings changed from the Home Assistant UI
        persist, at the cost of {option}`services.lnxlink.settings` no longer
        being authoritative.
      '';
    };

    environmentFile = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      example = "/run/user/1000/secrets/lnxlink.env";
      description = ''
        `KEY=value` file read by systemd, kept out of the Nix store. LNXlink
        honours `LNXLINK_MQTT_SERVER`, `LNXLINK_MQTT_PORT`,
        `LNXLINK_MQTT_USER`, `LNXLINK_MQTT_PASS`, `LNXLINK_MQTT_PREFIX` and
        `LNXLINK_MQTT_CLIENTID`.
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
      description = "Extra command line arguments for {command}`lnxlink`.";
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = !(cfg.configFile != null && cfg.settings != { });
        message = "services.lnxlink: set either `configFile` or `settings`, not both.";
      }
    ];

    home.packages = [ cfg.package ];

    systemd.user.services.lnxlink = {
      Unit = {
        Description = "LNXlink - Linux integration for Home Assistant";
        Documentation = "https://bkbilly.gitbook.io/lnxlink";
        After = [
          "network-online.target"
          "graphical-session.target"
        ];
        Wants = [ "network-online.target" ];
        PartOf = [ "graphical-session.target" ];
      };

      Service = {
        Type = "simple";
        ExecStartPre = "${seedConfig}";
        ExecStart = "${lib.getExe cfg.package} ${args}";
        Restart = "always";
        RestartSec = 5;
        StateDirectory = stateDir;
        StateDirectoryMode = "0700";
      }
      // lib.optionalAttrs (cfg.environmentFile != null) {
        EnvironmentFile = toString cfg.environmentFile;
      };

      Install.WantedBy = [ "graphical-session.target" ];
    };
  };
}
