{
  description = "LNXlink - Internet of Things (IoT) integration with Linux using MQTT";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      inherit (nixpkgs) lib;

      # LNXlink reads Linux-specific /proc and /sys layouts throughout, so
      # there is nothing to offer on Darwin.
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];

      forAllSystems =
        f:
        lib.genAttrs systems (
          system:
          f (
            import nixpkgs {
              inherit system;
              overlays = [ self.overlays.default ];
            }
          )
        );
    in
    {
      overlays.default = import ./packaging/nix/overlay.nix;

      packages = forAllSystems (pkgs: {
        default = pkgs.lnxlink;
        inherit (pkgs) lnxlink;

        # Everything upstream supports, including the OpenCV and NVIDIA stacks.
        lnxlink-full = pkgs.lnxlink.override {
          withWebcam = true;
          withNvidia = true;
          withAmdGpu = true;
          withSpeechRecognition = true;
        };

        # Server-shaped build: no session bus, no display, no audio.
        lnxlink-headless = pkgs.lnxlink.override {
          withX11 = false;
          withAudio = false;
          withGio = false;
        };
      });

      apps = forAllSystems (pkgs: {
        default = self.apps.${pkgs.stdenv.hostPlatform.system}.lnxlink;
        lnxlink = {
          type = "app";
          program = lib.getExe pkgs.lnxlink;
          meta = { inherit (pkgs.lnxlink.meta) description; };
        };
      });

      nixosModules = rec {
        lnxlink = { ... }: {
          imports = [ ./packaging/nix/nixos-module.nix ];
          nixpkgs.overlays = [ self.overlays.default ];
        };
        default = lnxlink;
      };

      # Home Manager module. Unlike the NixOS one this does not pull in the
      # overlay — Home Manager consumes the system's `pkgs` — so either add
      # `self.overlays.default` to `nixpkgs.overlays` or set
      # `services.lnxlink.package` explicitly.
      homeModules = rec {
        lnxlink = import ./packaging/nix/home-manager-module.nix;
        default = lnxlink;
      };

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          inputsFrom = [ pkgs.lnxlink ];

          packages = [
            (pkgs.python3.withPackages (
              ps:
              pkgs.lnxlink.dependencies
              ++ [
                ps.pytest
                ps.pytest-asyncio
                ps.pytest-cov
              ]
            ))
            pkgs.pre-commit
            pkgs.ruff
            pkgs.nixfmt-tree
            # Handy for poking at a broker while developing modules.
            pkgs.mosquitto
          ];

          shellHook = ''
            echo "lnxlink dev shell — python $(python3 --version | cut -d' ' -f2)"
            echo "run: python -m lnxlink -c ./lnxlink_config/lnxlink.yaml -i"
          '';
        };
      });

      checks = forAllSystems (
        pkgs:
        let
          system = pkgs.stdenv.hostPlatform.system;
        in
        {
          package = self.packages.${system}.default;
          package-headless = self.packages.${system}.lnxlink-headless;

          # Catch option-definition mistakes without paying for a VM.
          nixos-module-eval =
            (nixpkgs.lib.nixosSystem {
              modules = [
                self.nixosModules.default
                ({ ... }: {
                  nixpkgs.hostPlatform = system;
                  boot.loader.grub.enable = false;
                  fileSystems."/" = {
                    device = "/dev/null";
                    fsType = "ext4";
                  };
                  system.stateVersion = lib.trivial.release;

                  services.lnxlink = {
                    enable = true;
                    mode = "system";
                    settings.mqtt.server = "127.0.0.1";
                  };
                })
              ];
            }).config.system.build.toplevel;

          # End-to-end: real broker, real service, assert it publishes.
          integration = pkgs.callPackage ./packaging/nix/tests/integration.nix { };
          formatting = pkgs.runCommand "check-nix-formatting" { nativeBuildInputs = [ pkgs.nixfmt ]; } ''
            find ${
              lib.fileset.toSource {
                root = ./.;
                fileset = lib.fileset.unions [
                  ./flake.nix
                  ./packaging/nix
                ];
              }
            } -name '*.nix' -exec nixfmt --check --strict {} +
            touch $out
          '';
        }
      );

      formatter = forAllSystems (pkgs: pkgs.nixfmt-tree);
    };
}
