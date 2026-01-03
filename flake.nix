{
  description = "NixOS rebuild test automation with terminal recording";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      # App that can be run with `nix run`
      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/nixos-rebuild-test";
        };
      });

      # Python package
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python312;
        in
        {
          default = python.pkgs.buildPythonApplication {
            pname = "nixos-rebuild-tester";
            version = "0.2.0";

            pyproject = true;
            src = ./src;

            build-system = [
              python.pkgs.setuptools
              python.pkgs.wheel
            ];

            dependencies = [
              python.pkgs.typer
            ];

            meta = {
              description = "Minimal NixOS rebuild testing with direct subprocess approach";
              mainProgram = "nixos-rebuild-test";
            };
          };
        });

      # Development shell
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python312;
        in
        {
          default = pkgs.mkShell {
            packages = [
              python
              python.pkgs.typer
              python.pkgs.pytest
              python.pkgs.pytest-asyncio
              python.pkgs.ruff
              pkgs.uv
              pkgs.asciinema
            ];

            shellHook = ''
              echo "NixOS Rebuild Tester Development Shell (Refactored)"
              echo "Run: uv pip install -e ./src"
            '';
          };
        });
    };
}
