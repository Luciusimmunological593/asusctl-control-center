const crypto = require("node:crypto");
const fs = require("node:fs/promises");
const path = require("node:path");
const os = require("node:os");
const { execFile, spawn } = require("node:child_process");
const { promisify } = require("node:util");
const { fileURLToPath } = require("node:url");

const manifest = require("./manifest.json");

const execFileAsync = promisify(execFile);
const CORE_BINARY = "asus-linux-control-center";
const DEFAULT_BUFFER = 10 * 1024 * 1024;

function withEnvOverrides(baseEnv, options = {}) {
  const env = { ...(baseEnv || process.env) };
  if (options.cacheDir) {
    env.ALCC_WRAPPER_CACHE_DIR = options.cacheDir;
  }
  if (options.coreSource) {
    env.ALCC_WRAPPER_CORE_SOURCE = options.coreSource;
  }
  return env;
}

function parseMode(options = {}) {
  return options.mode || "auto";
}

function getCacheRoot(env = process.env) {
  if (env.ALCC_WRAPPER_CACHE_DIR) {
    return env.ALCC_WRAPPER_CACHE_DIR;
  }
  const xdgCache = env.XDG_CACHE_HOME || path.join(os.homedir(), ".cache");
  return path.join(xdgCache, "asusctl-control-center", "npm-wrapper", manifest.coreVersion);
}

function getManagedPaths(env = process.env) {
  const root = getCacheRoot(env);
  const venvDir = path.join(root, "venv");
  const binDir = path.join(venvDir, "bin");
  return {
    root,
    venvDir,
    binDir,
    python: path.join(binDir, "python"),
    executable: path.join(binDir, CORE_BINARY),
    wheelPath: path.join(root, manifest.wheelFile),
  };
}

async function pathExists(target) {
  try {
    await fs.access(target);
    return true;
  } catch {
    return false;
  }
}

function splitPath(env = process.env) {
  return (env.PATH || "").split(path.delimiter).filter(Boolean);
}

async function findOnPath(name, env = process.env) {
  for (const directory of splitPath(env)) {
    const candidate = path.join(directory, name);
    if (await pathExists(candidate)) {
      return candidate;
    }
  }
  return null;
}

async function runCapture(command, args = [], options = {}) {
  try {
    const { stdout, stderr } = await execFileAsync(command, args, {
      env: options.env,
      cwd: options.cwd,
      maxBuffer: options.maxBuffer || DEFAULT_BUFFER,
    });
    return {
      ok: true,
      command,
      args,
      code: 0,
      stdout,
      stderr,
    };
  } catch (error) {
    return {
      ok: false,
      command,
      args,
      code: typeof error.code === "number" ? error.code : 1,
      stdout: error.stdout || "",
      stderr: error.stderr || "",
      error: error.message,
    };
  }
}

function parsePythonVersion(output) {
  const match = output.match(/Python (\d+)\.(\d+)\.(\d+)/);
  if (!match) {
    return null;
  }
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    raw: `${match[1]}.${match[2]}.${match[3]}`,
  };
}

function isSupportedPython(version) {
  if (!version) {
    return false;
  }
  return version.major > 3 || (version.major === 3 && version.minor >= 11);
}

async function inspectPython(env = process.env) {
  const python = (await findOnPath("python3", env)) || (await findOnPath("python", env));
  if (!python) {
    return {
      found: false,
      supported: false,
      command: null,
      version: null,
      venv: false,
      message: "python3 was not found on PATH.",
    };
  }

  const versionRun = await runCapture(python, ["--version"], { env });
  const version = parsePythonVersion(`${versionRun.stdout}${versionRun.stderr}`.trim());
  const venvRun = await runCapture(python, ["-m", "venv", "--help"], { env });

  return {
    found: true,
    supported: isSupportedPython(version),
    command: python,
    version,
    venv: venvRun.ok,
    message: version
      ? `python ${version.raw}${isSupportedPython(version) ? "" : " is below 3.11"}`
      : "python version could not be parsed.",
  };
}

async function getCoreVersion(executable, env = process.env) {
  const versionRun = await runCapture(executable, ["--version"], { env });
  if (!versionRun.ok) {
    return null;
  }
  const line = versionRun.stdout.trim() || versionRun.stderr.trim();
  const match = line.match(/(\d+\.\d+\.\d+)$/);
  return match ? match[1] : line || null;
}

async function inspectSystemCore(env = process.env) {
  const executable = await findOnPath(CORE_BINARY, env);
  if (!executable) {
    return {
      source: "system",
      found: false,
      executable: null,
      version: null,
    };
  }
  return {
    source: "system",
    found: true,
    executable,
    version: await getCoreVersion(executable, env),
  };
}

async function inspectManagedCore(env = process.env) {
  const managed = getManagedPaths(env);
  if (!(await pathExists(managed.executable))) {
    return {
      source: "managed",
      found: false,
      executable: managed.executable,
      version: null,
      cacheRoot: managed.root,
    };
  }
  return {
    source: "managed",
    found: true,
    executable: managed.executable,
    version: await getCoreVersion(managed.executable, env),
    cacheRoot: managed.root,
  };
}

function sha256Buffer(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

async function sha256File(filePath) {
  return sha256Buffer(await fs.readFile(filePath));
}

async function downloadFile(url, destination) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Download failed for ${url}: HTTP ${response.status}`);
  }
  const arrayBuffer = await response.arrayBuffer();
  await fs.writeFile(destination, Buffer.from(arrayBuffer));
}

function resolveCoreSource(options = {}) {
  return options.coreSource || options.env?.ALCC_WRAPPER_CORE_SOURCE || null;
}

async function materializeInstallTarget(env, root, coreSource) {
  if (!coreSource) {
    const wheelPath = path.join(root, manifest.wheelFile);
    if (await pathExists(wheelPath)) {
      const checksum = await sha256File(wheelPath);
      if (checksum === manifest.wheelSha256) {
        return wheelPath;
      }
    }

    const tempPath = `${wheelPath}.tmp`;
    await fs.mkdir(root, { recursive: true });
    await downloadFile(manifest.wheelUrl, tempPath);
    const checksum = await sha256File(tempPath);
    if (checksum !== manifest.wheelSha256) {
      throw new Error(
        `Downloaded wheel checksum mismatch. Expected ${manifest.wheelSha256}, got ${checksum}.`,
      );
    }
    await fs.rename(tempPath, wheelPath);
    return wheelPath;
  }

  if (coreSource.startsWith("file://")) {
    return fileURLToPath(coreSource);
  }
  if (coreSource.startsWith("http://") || coreSource.startsWith("https://")) {
    const filename = path.basename(new URL(coreSource).pathname) || "core-source";
    const target = path.join(root, filename);
    await fs.mkdir(root, { recursive: true });
    await downloadFile(coreSource, target);
    return target;
  }
  return path.resolve(coreSource);
}

async function ensureManagedCore(options = {}) {
  const env = withEnvOverrides(options.env || process.env, options);
  if (process.platform !== "linux") {
    throw new Error("The managed ASUS Linux Control Center core is only supported on Linux.");
  }

  const python = await inspectPython(env);
  if (!python.found) {
    throw new Error("python3 is required to bootstrap the managed core.");
  }
  if (!python.supported) {
    throw new Error("python3 >= 3.11 is required to bootstrap the managed core.");
  }
  if (!python.venv) {
    throw new Error("python3 -m venv is required to bootstrap the managed core.");
  }

  const managed = getManagedPaths(env);
  const coreSource = resolveCoreSource({ ...options, env });
  const shouldReuse = !coreSource && !options.force && (await pathExists(managed.executable));

  if (!shouldReuse) {
    await fs.mkdir(managed.root, { recursive: true });
    if (!(await pathExists(managed.python))) {
      const venvRun = await runCapture(
        python.command,
        ["-m", "venv", "--system-site-packages", managed.venvDir],
        { env },
      );
      if (!venvRun.ok) {
        throw new Error(
          `Could not create the managed virtual environment:\n${venvRun.stderr || venvRun.error}`,
        );
      }
    }

    const installTarget = await materializeInstallTarget(env, managed.root, coreSource);
    const pipRun = await runCapture(
      managed.python,
      ["-m", "pip", "install", "--upgrade", installTarget],
      { env },
    );
    if (!pipRun.ok) {
      throw new Error(`Could not install the managed core:\n${pipRun.stderr || pipRun.error}`);
    }
  }

  if (!(await pathExists(managed.executable))) {
    throw new Error("The managed core install completed without creating the launcher.");
  }

  return {
    source: "managed",
    found: true,
    executable: managed.executable,
    version: await getCoreVersion(managed.executable, env),
    cacheRoot: managed.root,
  };
}

async function ensureCore(options = {}) {
  const env = withEnvOverrides(options.env || process.env, options);
  const mode = parseMode(options);

  if (mode === "system") {
    const system = await inspectSystemCore(env);
    if (!system.found) {
      throw new Error("System install not found: asus-linux-control-center is not on PATH.");
    }
    return system;
  }

  if (mode === "managed") {
    return ensureManagedCore({ ...options, env });
  }

  const system = await inspectSystemCore(env);
  if (system.found) {
    return system;
  }
  return ensureManagedCore({ ...options, env });
}

async function collectCoreDiagnostics(executable, env = process.env) {
  const result = await runCapture(executable, ["--diagnostics-json"], { env });
  if (!result.ok) {
    return {
      ok: false,
      stdout: result.stdout,
      stderr: result.stderr,
      message: result.stderr || result.error || "Could not collect diagnostics.",
      snapshot: null,
    };
  }
  try {
    return {
      ok: true,
      stdout: result.stdout,
      stderr: result.stderr,
      message: "",
      snapshot: JSON.parse(result.stdout),
    };
  } catch (error) {
    return {
      ok: false,
      stdout: result.stdout,
      stderr: result.stderr,
      message: `Diagnostics JSON could not be parsed: ${error.message}`,
      snapshot: null,
    };
  }
}

async function diagnostics(options = {}) {
  const env = withEnvOverrides(options.env || process.env, options);
  const core = await ensureCore({ ...options, env });
  const args = [options.json === false ? "--diagnostics" : "--diagnostics-json"];
  const result = await runCapture(core.executable, args, { env });
  if (!result.ok) {
    throw new Error(result.stderr || result.error || "Diagnostics command failed.");
  }
  if (options.json === false) {
    return {
      core,
      text: result.stdout,
    };
  }
  return {
    core,
    snapshot: JSON.parse(result.stdout),
    text: result.stdout,
  };
}

async function inspectBackend(env = process.env) {
  const asusctl = await findOnPath("asusctl", env);
  const systemctl = await findOnPath("systemctl", env);
  const supergfxctl = await findOnPath("supergfxctl", env);

  const asusctlInfo = asusctl
    ? await runCapture(asusctl, ["info"], { env })
    : { ok: false, stdout: "", stderr: "", error: "missing" };

  const asusdService = systemctl
    ? await runCapture(systemctl, ["is-active", "asusd.service"], { env })
    : { ok: false, stdout: "", stderr: "", error: "systemctl missing" };

  const supergfxdService = systemctl
    ? await runCapture(systemctl, ["is-active", "supergfxd.service"], { env })
    : { ok: false, stdout: "", stderr: "", error: "systemctl missing" };

  return {
    asusctl: {
      found: Boolean(asusctl),
      path: asusctl,
      ok: asusctlInfo.ok,
      message: asusctlInfo.ok
        ? "asusctl info succeeded."
        : asusctlInfo.stderr.trim() || asusctlInfo.error || "asusctl info failed.",
    },
    systemctl: {
      found: Boolean(systemctl),
      path: systemctl,
    },
    asusdService: {
      status: asusdService.stdout.trim() || "unknown",
      ok: asusdService.ok && asusdService.stdout.trim() === "active",
      message: asusdService.stderr.trim() || asusdService.error || "",
    },
    supergfxctl: {
      found: Boolean(supergfxctl),
      path: supergfxctl,
    },
    supergfxdService: {
      status: supergfxdService.stdout.trim() || "unknown",
      ok: supergfxdService.ok && supergfxdService.stdout.trim() === "active",
      message: supergfxdService.stderr.trim() || supergfxdService.error || "",
    },
  };
}

async function doctor(options = {}) {
  const env = withEnvOverrides(options.env || process.env, options);
  const mode = parseMode(options);
  const display = env.WAYLAND_DISPLAY || env.DISPLAY || null;

  const report = {
    wrapperVersion: manifest.wrapperVersion,
    coreVersion: manifest.coreVersion,
    mode,
    platform: {
      platform: process.platform,
      arch: process.arch,
      supported: process.platform === "linux",
    },
    display: {
      available: Boolean(display),
      session: env.XDG_SESSION_TYPE || null,
      value: display,
    },
    python: await inspectPython(env),
    core: {
      system: await inspectSystemCore(env),
      managed: await inspectManagedCore(env),
      active: null,
    },
    backend: await inspectBackend(env),
    diagnostics: {
      ok: false,
      snapshot: null,
      message: "No core executable was selected.",
    },
    summary: {
      readyToLaunch: false,
      backendReady: false,
      message: "",
    },
  };

  if (mode === "system") {
    report.core.active = report.core.system.found ? report.core.system : null;
  } else if (mode === "managed") {
    report.core.active = report.core.managed.found
      ? report.core.managed
      : options.installCore
        ? await ensureManagedCore({ ...options, env })
        : null;
  } else if (report.core.system.found) {
    report.core.active = report.core.system;
  } else if (report.core.managed.found) {
    report.core.active = report.core.managed;
  } else if (options.installCore) {
    report.core.active = await ensureManagedCore({ ...options, env });
  }

  if (report.core.active) {
    report.diagnostics = await collectCoreDiagnostics(report.core.active.executable, env);
  }

  report.summary.backendReady = report.backend.asusctl.ok && report.backend.asusdService.ok;
  report.summary.readyToLaunch =
    report.platform.supported && report.display.available && Boolean(report.core.active);

  if (!report.platform.supported) {
    report.summary.message = "The wrapper only supports Linux hosts.";
  } else if (!report.display.available) {
    report.summary.message = "No graphical display was detected.";
  } else if (!report.core.active) {
    report.summary.message = "No Python core is available yet.";
  } else if (!report.summary.backendReady) {
    report.summary.message = "The UI can launch, but backend controls are not fully ready yet.";
  } else {
    report.summary.message = "The wrapper and backend look ready.";
  }

  return report;
}

function yesNo(value) {
  return value ? "yes" : "no";
}

function formatDoctorReport(report) {
  const lines = [
    `Wrapper version: ${report.wrapperVersion}`,
    `Core target version: ${report.coreVersion}`,
    `Platform: ${report.platform.platform} ${report.platform.arch} (supported=${yesNo(report.platform.supported)})`,
    `Display available: ${yesNo(report.display.available)}${report.display.session ? ` (${report.display.session})` : ""}`,
    "",
    "[Python]",
    `- Found: ${yesNo(report.python.found)}`,
    `- Command: ${report.python.command || "missing"}`,
    `- Version: ${report.python.version ? report.python.version.raw : "unknown"}`,
    `- Supported: ${yesNo(report.python.supported)}`,
    `- venv available: ${yesNo(report.python.venv)}`,
    "",
    "[Core]",
    `- System core: ${report.core.system.found ? report.core.system.executable : "missing"}`,
    `- System version: ${report.core.system.version || "unknown"}`,
    `- Managed core: ${report.core.managed.found ? report.core.managed.executable : "missing"}`,
    `- Managed version: ${report.core.managed.version || "unknown"}`,
    `- Active core: ${report.core.active ? `${report.core.active.source} (${report.core.active.version || "unknown"})` : "none"}`,
    "",
    "[Backend]",
    `- asusctl found: ${yesNo(report.backend.asusctl.found)}`,
    `- asusctl info ok: ${yesNo(report.backend.asusctl.ok)}`,
    `- asusd.service: ${report.backend.asusdService.status}`,
    `- supergfxctl found: ${yesNo(report.backend.supergfxctl.found)}`,
    `- supergfxd.service: ${report.backend.supergfxdService.status}`,
    "",
    "[Summary]",
    `- Ready to launch: ${yesNo(report.summary.readyToLaunch)}`,
    `- Backend ready: ${yesNo(report.summary.backendReady)}`,
    `- Note: ${report.summary.message}`,
  ];

  if (report.diagnostics.ok && report.diagnostics.snapshot) {
    lines.push(
      "",
      "[Diagnostics]",
      `- Device: ${report.diagnostics.snapshot.device.product_family} / ${report.diagnostics.snapshot.device.board_name}`,
      `- asusctl version: ${report.diagnostics.snapshot.device.asusctl_version}`,
      `- Active profile: ${report.diagnostics.snapshot.profiles.active || "unknown"}`,
      `- Warning count: ${report.diagnostics.snapshot.warnings.length}`,
    );
  } else if (report.diagnostics.message) {
    lines.push("", "[Diagnostics]", `- ${report.diagnostics.message}`);
  }

  return `${lines.join("\n")}\n`;
}

async function runApp(appArgs = [], options = {}) {
  const env = withEnvOverrides(options.env || process.env, options);
  const core = await ensureCore({ ...options, env });
  return new Promise((resolve, reject) => {
    const child = spawn(core.executable, appArgs, {
      env,
      stdio: "inherit",
    });
    child.on("exit", (code, signal) => {
      if (signal) {
        reject(new Error(`Process exited due to signal ${signal}.`));
        return;
      }
      resolve({ code: code ?? 0, core });
    });
    child.on("error", reject);
  });
}

module.exports = {
  manifest,
  ensureCore,
  ensureManagedCore,
  diagnostics,
  doctor,
  formatDoctorReport,
  getManagedPaths,
  inspectManagedCore,
  inspectPython,
  inspectSystemCore,
  run: runApp,
};
