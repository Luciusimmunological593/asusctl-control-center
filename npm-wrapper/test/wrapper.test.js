const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");
const { execFile } = require("node:child_process");
const { promisify } = require("node:util");

const execFileAsync = promisify(execFile);

const wrapper = require("../index.js");

async function writeExecutable(filePath, contents) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, contents, { mode: 0o755 });
}

async function makeWorkspace() {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "alcc-wrapper-"));
  const binDir = path.join(root, "bin");
  const cacheDir = path.join(root, "cache");
  await fs.mkdir(binDir, { recursive: true });
  return {
    root,
    binDir,
    env: {
      PATH: `${binDir}${path.delimiter}${process.env.PATH || ""}`,
      XDG_CACHE_HOME: cacheDir,
      DISPLAY: ":99",
      XDG_SESSION_TYPE: "x11",
    },
  };
}

function fakeDiagnosticsJson() {
  return JSON.stringify({
    device: {
      product_family: "ROG Strix",
      board_name: "G614JV",
      asusctl_version: "6.3.5",
      kernel: "6.17.0-19-generic",
      distro: "Ubuntu 25.10",
      hostname: "test-host",
    },
    integration: {
      asusctl_path: "/usr/bin/asusctl",
      asusd_service: "active",
      asusd_bus_name: true,
      supergfxctl_path: null,
      supergfxd_service: "inactive",
      supergfxd_enabled: "disabled",
      supergfxd_bus_name: false,
    },
    profiles: {
      supported: true,
      available: ["Quiet", "Balanced", "Performance"],
      active: "Balanced",
      ac_profile: null,
      battery_profile: null,
      message: "",
    },
    fan_curve: {
      supported: false,
      message: "unsupported",
      probe_profile: null,
      snapshot: null,
    },
    battery: {
      supported: true,
      limit: 80,
      message: "",
    },
    keyboard: {
      supported: true,
      brightness: "high",
      levels: ["off", "low", "med", "high"],
      message: "",
    },
    aura: {
      supported: true,
      effects: ["static"],
      zones: ["keyboard"],
      message: "",
    },
    graphics: {
      installed: false,
      current_mode: null,
      supported_modes: [],
      vendor: null,
      power_status: null,
      pending_action: null,
      pending_mode: null,
      message: "not installed",
    },
    firmware_attributes: [],
    warnings: ["demo warning"],
    timestamp: "2026-03-28T00:00:00",
  });
}

test("auto mode prefers the system core on PATH", async () => {
  const workspace = await makeWorkspace();
  await writeExecutable(
    path.join(workspace.binDir, "asus-linux-control-center"),
    `#!/bin/bash
set -euo pipefail
if [[ "\${1:-}" == "--version" ]]; then
  echo "asus-linux-control-center 9.9.9"
  exit 0
fi
if [[ "\${1:-}" == "--diagnostics-json" ]]; then
  cat <<'EOF'
${fakeDiagnosticsJson()}
EOF
  exit 0
fi
echo "system core"
`,
  );

  const core = await wrapper.ensureCore({ env: workspace.env, mode: "auto" });
  assert.equal(core.source, "system");
  assert.equal(core.version, "9.9.9");
});

test("managed mode bootstraps a private virtualenv fallback", async () => {
  const workspace = await makeWorkspace();
  const sourcePath = path.join(workspace.root, "core.whl");
  await fs.writeFile(sourcePath, "fake wheel");

  await writeExecutable(
    path.join(workspace.binDir, "python3"),
    `#!/bin/bash
set -euo pipefail
if [[ "\${1:-}" == "--version" ]]; then
  echo "Python 3.11.9"
  exit 0
fi
if [[ "\${1:-}" == "-m" && "\${2:-}" == "venv" && "\${3:-}" == "--help" ]]; then
  echo "venv help"
  exit 0
fi
if [[ "\${1:-}" == "-m" && "\${2:-}" == "venv" ]]; then
  target="\${4:-}"
  mkdir -p "\${target}/bin"
  cat > "\${target}/bin/python" <<'PYEOF'
#!/bin/bash
set -euo pipefail
bin_dir="$(cd "$(dirname "$0")" && pwd)"
if [[ "\${1:-}" == "-m" && "\${2:-}" == "pip" && "\${3:-}" == "install" ]]; then
  cat > "\${bin_dir}/asus-linux-control-center" <<'EXEOF'
#!/bin/bash
set -euo pipefail
if [[ "\${1:-}" == "--version" ]]; then
  echo "asus-linux-control-center 0.1.0"
  exit 0
fi
if [[ "\${1:-}" == "--diagnostics-json" ]]; then
  cat <<'JSONEOF'
${fakeDiagnosticsJson()}
JSONEOF
  exit 0
fi
echo "managed core"
EXEOF
  chmod +x "\${bin_dir}/asus-linux-control-center"
  exit 0
fi
echo "unexpected fake python invocation: $*" >&2
exit 1
PYEOF
  chmod +x "\${target}/bin/python"
  exit 0
fi
echo "unexpected top-level fake python invocation: $*" >&2
exit 1
`,
  );

  const core = await wrapper.ensureCore({
    env: workspace.env,
    mode: "managed",
    coreSource: sourcePath,
  });

  assert.equal(core.source, "managed");
  assert.equal(core.version, "0.1.0");
  assert.match(core.executable, /venv\/bin\/asus-linux-control-center$/);
});

test("CLI doctor --json exposes wrapper, backend, and diagnostics state", async () => {
  const workspace = await makeWorkspace();
  await writeExecutable(
    path.join(workspace.binDir, "asus-linux-control-center"),
    `#!/bin/bash
set -euo pipefail
if [[ "\${1:-}" == "--version" ]]; then
  echo "asus-linux-control-center 0.1.0"
  exit 0
fi
if [[ "\${1:-}" == "--diagnostics-json" ]]; then
  cat <<'EOF'
${fakeDiagnosticsJson()}
EOF
  exit 0
fi
echo "run"
`,
  );
  await writeExecutable(
    path.join(workspace.binDir, "asusctl"),
    `#!/bin/bash
set -euo pipefail
if [[ "\${1:-}" == "info" ]]; then
  echo "Product family: ROG Strix"
  exit 0
fi
echo "unexpected" >&2
exit 1
`,
  );
  await writeExecutable(
    path.join(workspace.binDir, "systemctl"),
    `#!/bin/bash
set -euo pipefail
if [[ "\${1:-}" == "is-active" && "\${2:-}" == "asusd.service" ]]; then
  echo "active"
  exit 0
fi
if [[ "\${1:-}" == "is-active" && "\${2:-}" == "supergfxd.service" ]]; then
  echo "inactive"
  exit 3
fi
echo "unknown" >&2
exit 1
`,
  );

  const cli = path.join(__dirname, "..", "bin", "asusctl-control-center.js");
  const { stdout } = await execFileAsync(process.execPath, [cli, "doctor", "--json"], {
    env: workspace.env,
  });
  const report = JSON.parse(stdout);

  assert.equal(report.core.active.source, "system");
  assert.equal(report.backend.asusctl.ok, true);
  assert.equal(report.backend.asusdService.status, "active");
  assert.equal(report.diagnostics.snapshot.device.board_name, "G614JV");
  assert.equal(report.summary.readyToLaunch, true);
});
