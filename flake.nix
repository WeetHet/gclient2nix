{
  description = "Generate Nix expressions for gclient/gn projects";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
    flake-parts.url = "github:hercules-ci/flake-parts";
    pyproject-nix = {
      url = "github:nix-community/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      flake-parts,
      pyproject-nix,
      systems,
      ...
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = import systems;

      perSystem =
        { config, pkgs, ... }:
        let
          python = pkgs.python3;
          pyproject = pyproject-nix.lib.project.loadPyproject {
            projectRoot = ./.;
          };
          pyattrs = pyproject.renderers.buildPythonPackage { inherit python; };
          pythonEnv = python.withPackages (pyproject.renderers.withPackages { inherit python; });
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
            gclient2nix = python.pkgs.buildPythonPackage pyattrs;
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
              pythonEnv
            ];
          };
        };
    };
}
