# End-to-end check: boot a VM with a real MQTT broker, let the packaged
# service connect, and assert that it both announces itself and publishes
# sensor state.
{ testers }:

testers.runNixOSTest {
  name = "lnxlink";

  nodes.machine = { pkgs, ... }: {
    # The bare module, not `nixosModules.default`: the test framework pins
    # `nixpkgs.*` read-only, and the node's `pkgs` already carries the
    # overlay that the flake's `checks` were evaluated with.
    imports = [ ../nixos-module.nix ];

    virtualisation = {
      memorySize = 2048;
      diskSize = 4096;
    };

    services.mosquitto = {
      enable = true;
      listeners = [
        {
          address = "127.0.0.1";
          port = 1883;
          omitPasswordAuth = true;
          settings.allow_anonymous = true;
          acl = [ "topic readwrite #" ];
        }
      ];
    };

    services.lnxlink = {
      enable = true;
      mode = "system";

      # Trim the closure so the VM image stays small; none of the disabled
      # feature groups are reachable from a headless test anyway.
      package = pkgs.lnxlink.override {
        withDbus = false;
        withX11 = false;
        withAudio = false;
        withDocker = false;
        withRestApi = false;
        withSteam = false;
        withGio = false;
      };

      logLevel = "DEBUG";
      settings = {
        mqtt = {
          transport = "mqtt";
          prefix = "lnxlink";
          clientId = "testvm";
          server = "127.0.0.1";
          port = 1883;
          auth = {
            user = "";
            pass = "";
            tls = false;
          };
          discovery = {
            enabled = true;
            prefix = "homeassistant";
          };
          lwt = {
            enabled = true;
            qos = 1;
          };
        };
        update_interval = 2;
        # Modules that need neither a session bus nor a display.
        modules = [
          "cpu"
          "memory"
          "disk_usage"
          "lwt"
        ];
      };
    };

    environment.systemPackages = [ pkgs.mosquitto ];
  };

  testScript = ''
    machine.wait_for_unit("mosquitto.service")
    machine.wait_for_open_port(1883)
    machine.wait_for_unit("lnxlink.service")

    # The declarative config must have been seeded into the state directory,
    # writable, so lnxlink can backfill defaults for the modules it loads.
    machine.succeed("test -w /var/lib/lnxlink/config.yaml")

    machine.wait_until_succeeds(
        "journalctl -u lnxlink.service | grep -q 'Loaded addons'", timeout=120
    )

    # The service must not have picked up the git-checkout install method, or
    # the Home Assistant update entity would try to `git pull` the store path.
    machine.succeed(
        "journalctl -u lnxlink.service | grep -q 'Install method: nix'"
    )

    # Birth certificate: retained LWT payload flipped to ON on connect.
    lwt = machine.succeed(
        "mosquitto_sub -h 127.0.0.1 -t 'lnxlink/testvm/lwt' -C 1 -W 60"
    )
    assert lwt.strip() == "ON", f"unexpected LWT payload: {lwt!r}"

    # Home Assistant MQTT discovery announcements.
    machine.succeed(
        "mosquitto_sub -h 127.0.0.1 -t 'homeassistant/#' -C 1 -W 60 >/dev/null"
    )

    # And actual telemetry, which proves the monitor loop is running.
    state = machine.succeed(
        "mosquitto_sub -h 127.0.0.1 -t 'lnxlink/testvm/monitor_controls/#' -C 1 -W 90 -v"
    )
    assert state.strip(), "no sensor state published"

    with subtest("shutting down publishes the offline notice"):
        machine.succeed("systemctl stop lnxlink.service")
        lwt = machine.succeed(
            "mosquitto_sub -h 127.0.0.1 -t 'lnxlink/testvm/lwt' -C 1 -W 60"
        )
        assert lwt.strip() == "OFF", f"unexpected LWT payload: {lwt!r}"
  '';
}
