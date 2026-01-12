{
  description = "NixOS rebuild test automation with terminal recording";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
  };

  outputs = { self, nixpkgs, devenv, ... }@inputs:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      devenvFlake = devenv.lib.mkFlake {
        inherit inputs systems;
        modules = [ ./devenv.nix ];
      };
    in
    {
      inherit (devenvFlake) packages devShells;

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
    };
}
