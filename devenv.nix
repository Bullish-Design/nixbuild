{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  env.GREET = "devenv";

  # https://devenv.sh/packages/
  packages = [ pkgs.git ];

  # https://devenv.sh/languages/
  # languages.rust.enable = true;
  languages.python = {
    enable = true;
    version = "3.12";
    uv.enable = true;
  };

  # https://devenv.sh/processes/
  # processes.dev.exec = "${lib.getExe pkgs.watchexec} -n -- ls -la";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo hello from $GREET
  '';

  # https://devenv.sh/basics/
  enterShell = ''
    hello         # Run scripts directly
    git --version # Use packages
  '';

  # https://devenv.sh/tasks/
  #
  # devman — the automation plane (CONCEPT.md §5), with the direct task shape
  # (like nix-desktop): this repository has no Python test suite (its pytest
  # config points at a `../tests` that does not exist), so the gate is the
  # flake itself. `base:check` is the repo's configured linter (src/pyproject
  # .toml); `base:test` builds the CLI package the flake ships.
  devman = {
    enable = true;
    project = "nixbuild";
    groups = [ "base" ];
  };

  tasks = {
    "base:check".exec = "ruff check src";
    "base:test".exec = "nix flake check";
  };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  outputs.nixbuild = config.languages.python.import ./src {};

  # https://devenv.sh/git-hooks/
  # git-hooks.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
