let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell {
  packages = [
    (pkgs.python312.withPackages (python-pkgs: [
      python-pkgs.requests
      python-pkgs.certifi
      python-pkgs.six
      python-pkgs.python-dateutil
      python-pkgs.setuptools
      python-pkgs.urllib3
      python-pkgs.selenium
      python-pkgs.faiss
      python-pkgs.fastapi
      python-pkgs.pydantic
      python-pkgs.uvicorn
      python-pkgs.pynvim
      python-pkgs.black
    ]))
    pkgs.chromedriver
  ];

  shellHook = ''
    if [ -z "$FISH_VERSION" ]; then
      exec fish
    fi
  '';
}
