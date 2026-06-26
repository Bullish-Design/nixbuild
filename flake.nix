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
      # The nixos-rebuild-test CLI, built directly from ./src.
      # (Previously surfaced via devenv.lib.mkFlake, which current devenv no
      # longer exposes — packaged directly here, matching repoman's flake idiom.
      # `devenv shell` authoring is unaffected: it reads devenv.yaml/devenv.nix.)
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          nixbuild = pkgs.python312Packages.buildPythonApplication {
            pname = "nixos-rebuild-tester";
            version = "0.2.0";
            src = ./src;
            pyproject = true;
            build-system = with pkgs.python312Packages; [
              setuptools
              wheel
            ];
            propagatedBuildInputs = with pkgs.python312Packages; [
              typer
            ];
          };
          default = self.packages.${system}.nixbuild;
        });

      lib = {
        mkCliVmTest = import ./nix/mk-cli-vm-test.nix { lib = nixpkgs.lib; };
      };

      nixosModules.default = { pkgs, ... }: {
        environment.systemPackages = [
          pkgs.asciinema
        ];
      };

      # App that can be run with `nix run`
      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.nixbuild}/bin/nixos-rebuild-test";
        };
      });

      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python312
              pkgs.uv
              pkgs.git
            ];
          };
        });
    };
}
