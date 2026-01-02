{
  description = "NixOS rebuild test automation with terminal recording";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    terminal-state = {
      url = "github:Bullish-Design/terminal-state";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, terminal-state }:
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
          terminal-state-pkg = terminal-state.packages.${system}.default;
        in
        {
          default = python.pkgs.buildPythonApplication {
            pname = "nixos-rebuild-tester";
            version = "0.1.0";

            pyproject = true;
            src = ./src;

            build-system = [
              python.pkgs.setuptools
              python.pkgs.wheel
            ];

            dependencies = [
              terminal-state-pkg
              python.pkgs.pydantic
              python.pkgs.click
            ];

            meta = {
              description = "Automated NixOS rebuild testing";
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
              terminal-state.packages.${system}.default
              python.pkgs.pydantic
              python.pkgs.click
              python.pkgs.pytest
              python.pkgs.pytest-asyncio
              python.pkgs.ruff
              pkgs.uv
              pkgs.tmux
            ];

            shellHook = ''
              echo "NixOS Rebuild Tester Development Shell"
              echo "Run: uv pip install -e ./src"
            '';
          };
        });
    };
}
