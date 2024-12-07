{
  lib,
  buildPythonPackage,
  flit-core,
  click,
}:
buildPythonPackage {
  pname = "gclient2nix";
  version = "0.2.0";
  pyproject = true;

  src = ../.;

  build-system = [
    flit-core
  ];

  dependencies = [
    click
  ];

  meta = {
    description = "Generate Nix expressions for projects based on the Google build tools";
    homepage = "https://github.com/WeetHet/gclient2nix";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [
      weethet
    ];
  };
}
