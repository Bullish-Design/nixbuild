{ lib }:

{ pkgs
, name
, machineModules
, commands
, env ? { }
, extraDiagnostics ? true
, extraNodes ? { }
}:
let
  modules =
    if lib.isList machineModules
    then machineModules
    else [ machineModules ];

  commandsJson = builtins.toJSON commands;
  envJson = builtins.toJSON env;
  diagnosticsEnabled = if extraDiagnostics then "True" else "False";

  testScript = ''
    import json
    import os
    import shlex
    import time

    commands = json.loads('''${commandsJson}''')
    env_map = json.loads('''${envJson}''')
    output_dir = os.environ.get("NIXOS_TEST_OUTPUT_DIR", os.getcwd())
    os.makedirs(output_dir, exist_ok=True)

    transcript_path = os.path.join(output_dir, "transcript.log")
    journal_path = os.path.join(output_dir, "journal.txt")
    diagnostics_path = os.path.join(output_dir, "diagnostics.txt")
    summary_path = os.path.join(output_dir, "summary.json")

    def write_transcript(text):
        with open(transcript_path, "a", encoding="utf-8") as handle:
            handle.write(text)
            if not text.endswith("\n"):
                handle.write("\n")

    def wrap_command(cmd):
        combined = f"{cmd} 2>&1"
        env_prefix = " ".join(
            f"{key}={shlex.quote(str(value))}" for key, value in env_map.items()
        )
        if env_prefix:
            return f"env {env_prefix} bash -lc {shlex.quote(combined)}"
        return f"bash -lc {shlex.quote(combined)}"

    def collect_diagnostics():
        if not ${diagnosticsEnabled}:
            return
        _, journal = machine.execute("journalctl -b --no-pager")
        with open(journal_path, "w", encoding="utf-8") as handle:
            handle.write(journal)

        sections = []
        for cmd in [
            "systemctl --failed --no-pager",
            "nixos-version",
            "dmesg --color=never",
        ]:
            status, output = machine.execute(wrap_command(cmd))
            sections.append(f"$ {cmd}\n{output}\n[exit={status}]\n")
        with open(diagnostics_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(sections))

    start_all()
    machine.wait_for_unit("multi-user.target")

    summary = {
        "success": True,
        "started_at": time.time(),
        "commands": [],
    }

    for cmd in commands:
        write_transcript(f"$ {cmd}")
        started = time.time()
        status, output = machine.execute(wrap_command(cmd))
        duration = time.time() - started
        if output:
            write_transcript(output.rstrip("\n"))
        write_transcript(f"[exit={status}]")
        write_transcript("")

        summary["commands"].append(
            {
                "command": cmd,
                "exit_code": status,
                "duration_seconds": round(duration, 2),
            }
        )

        if status != 0:
            summary["success"] = False
            collect_diagnostics()
            summary["finished_at"] = time.time()
            with open(summary_path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(summary, indent=2))
            raise Exception(f"Command failed: {cmd}")

    collect_diagnostics()
    summary["finished_at"] = time.time()
    with open(summary_path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, indent=2))
  '';

  testResult = pkgs.testers.runNixOSTest {
    inherit name testScript;
    nodes = {
      machine = { ... }: {
        imports = modules;
      };
    } // extraNodes;
  };
in
{
  test = testResult;
  driverInteractive = testResult.driverInteractive or testResult;
}
