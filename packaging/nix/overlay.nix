# Overlay adding `lnxlink` plus the Python dependencies that nixpkgs does not
# carry yet. Each addition falls back to the nixpkgs attribute when one appears
# upstream, so this stays correct as nixpkgs catches up.
final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (pyfinal: pyprev: {
      dbus-idle = pyprev.dbus-idle or (pyfinal.callPackage ./pkgs/dbus-idle.nix { });
      dbus-mediaplayer = pyprev.dbus-mediaplayer or (pyfinal.callPackage ./pkgs/dbus-mediaplayer.nix { });
      dbus-networkdevices =
        pyprev.dbus-networkdevices or (pyfinal.callPackage ./pkgs/dbus-networkdevices.nix { });
      dbus-notification =
        pyprev.dbus-notification or (pyfinal.callPackage ./pkgs/dbus-notification.nix { });
      nvitop = pyprev.nvitop or (pyfinal.callPackage ./pkgs/nvitop.nix { });
      nvsmi = pyprev.nvsmi or (pyfinal.callPackage ./pkgs/nvsmi.nix { });
      pyamdgpuinfo = pyprev.pyamdgpuinfo or (pyfinal.callPackage ./pkgs/pyamdgpuinfo.nix { });
      xlib-hotkeys = pyprev.xlib-hotkeys or (pyfinal.callPackage ./pkgs/xlib-hotkeys.nix { });
    })
  ];

  lnxlink = final.callPackage ./package.nix { };
}
