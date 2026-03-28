#!/usr/bin/env node

const {
  diagnostics,
  doctor,
  ensureCore,
  formatDoctorReport,
  manifest,
  run,
} = require("../index.js");

function printHelp() {
  console.log(`asusctl-control-center ${manifest.wrapperVersion}

Usage:
  asusctl-control-center [run] [app-args...]
  asusctl-control-center doctor [--json] [--managed|--system] [--install-core]
  asusctl-control-center diagnostics [--json] [--managed|--system]
  asusctl-control-center install-core [--core-source <path-or-url>] [--cache-dir <dir>]
  asusctl-control-center version

Wrapper options:
  --managed              Force the managed Python core
  --system               Force a system-installed asus-linux-control-center
  --core-source <value>  Override the managed core install source
  --cache-dir <dir>      Override the managed core cache directory

Examples:
  asusctl-control-center
  asusctl-control-center doctor --json
  asusctl-control-center diagnostics
  asusctl-control-center install-core --core-source file:///tmp/core.whl
`);
}

function parseArgs(argv) {
  const commands = new Set(["run", "doctor", "diagnostics", "install-core", "version", "help"]);
  const options = {};
  let command = null;
  const rest = [];

  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--help" || value === "-h") {
      command = "help";
      continue;
    }
    if (value === "--") {
      rest.push(...argv.slice(index + 1));
      break;
    }
    if (value === "--managed") {
      options.mode = "managed";
      continue;
    }
    if (value === "--system") {
      options.mode = "system";
      continue;
    }
    if (value === "--json") {
      options.json = true;
      continue;
    }
    if (value === "--install-core") {
      options.installCore = true;
      continue;
    }
    if (value === "--core-source") {
      index += 1;
      options.coreSource = argv[index];
      continue;
    }
    if (value === "--cache-dir") {
      index += 1;
      options.cacheDir = argv[index];
      continue;
    }
    if (!command && commands.has(value)) {
      command = value;
      continue;
    }
    rest.push(value);
  }

  return {
    command: command || "run",
    rest,
    options,
  };
}

async function main() {
  const { command, rest, options } = parseArgs(process.argv.slice(2));

  switch (command) {
    case "help":
      printHelp();
      return;
    case "version":
      console.log(`wrapper ${manifest.wrapperVersion}`);
      console.log(`core ${manifest.coreVersion}`);
      return;
    case "install-core": {
      const core = await ensureCore({ ...options, mode: "managed" });
      console.log(core.executable);
      return;
    }
    case "doctor": {
      const report = await doctor(options);
      if (options.json) {
        console.log(JSON.stringify(report, null, 2));
      } else {
        process.stdout.write(formatDoctorReport(report));
      }
      return;
    }
    case "diagnostics": {
      if (options.json) {
        const result = await diagnostics({ ...options, json: true });
        console.log(JSON.stringify(result.snapshot, null, 2));
      } else {
        const textResult = await diagnostics({ ...options, json: false });
        process.stdout.write(textResult.text);
      }
      return;
    }
    case "run":
    default: {
      const result = await run(rest, options);
      process.exitCode = result.code;
    }
  }
}

main().catch((error) => {
  console.error(error.message || String(error));
  process.exitCode = 1;
});
