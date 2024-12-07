{
  description = "Generate Nix expressions for gclient/gn projects";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs =
    inputs@{
      flake-parts,
      systems,
      ...
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = import systems;

      perSystem =
        { config, pkgs, ... }:
        let
          nativeDeps = [
            pkgs.nurl
            pkgs.nix-prefetch-git
            pkgs.nix
            pkgs.coreutils
            pkgs.nixfmt-rfc-style
          ];
        in
        {
          packages = {
            gclient2nix = pkgs.python3.pkgs.callPackage ./nix/package.nix { };
            default = pkgs.symlinkJoin {
              name = "gclient2nix-with-deps";
              paths = [ config.packages.gclient2nix ];
              nativeBuildInputs = [ pkgs.makeWrapper ];
              postBuild = ''
                wrapProgram $out/bin/gclient2nix \
                  --set PATH ${pkgs.lib.makeBinPath nativeDeps}
              '';
            };
          };
          devShells.default = pkgs.mkShell {
            packages = nativeDeps ++ [
              (pkgs.python3.withPackages (ps: [ ps.click ]))
            ];
          };
        };
    };
}
