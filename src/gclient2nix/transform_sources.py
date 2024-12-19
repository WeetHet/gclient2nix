from typing import Dict

NIX_TEMPLATE = """
{{
  fetchFromGitHub,
  fetchFromGitiles,
  fetchgit,
  fetchurl,
  runCommand,
  lib
}}:
let
  sourceDerivations = {{
    {derivations}
  }};
  namedSourceDerivations = builtins.mapAttrs (
    path: drv:
    drv.overrideAttrs {{
      name = lib.strings.sanitizeDerivationName path;
    }}
  ) sourceDerivations;
in
runCommand {name} {{ }} (
  lib.concatLines (
    [ "mkdir $out" ]
    ++ (lib.mapAttrsToList (path: drv: ''
      mkdir -p $out/${{path}}
      cp --no-preserve=mode --reflink=auto -rfT ${{drv}} $out/${{path}}
    '') namedSourceDerivations)
  )
)
"""


def transform_sources(name: str, sources: Dict[str, str]) -> str:
    derivations: str = "\n".join(f'"{p}" = {e};' for p, e in sources.items())
    return NIX_TEMPLATE.format(derivations=derivations, name=name)
