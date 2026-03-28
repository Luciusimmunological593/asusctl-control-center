# npm Wrapper

The repository now includes a thin npm wrapper in [`npm-wrapper/`](../npm-wrapper).

The wrapper does not replace the Python/PyQt application. The Python app remains the product and the hardware-control implementation. The Node layer only handles bootstrap, dependency checks, and process launch.

## Current publish status

The wrapper source is part of this repository and is also published on npm as `asusctl-control-center`.

The normal install path is:

```bash
npm install -g asusctl-control-center
asusctl-control-center doctor
asusctl-control-center
```

For local development from a checkout:

```bash
npm install -g ./npm-wrapper
```

## Design goals

- keep Python as the source of truth for device probing and diagnostics
- prefer an existing system install when it already exists
- provide a managed fallback when users come from the Node ecosystem
- keep the JavaScript API small and orchestration-focused

## Wrapper modes

### `auto`

Default behavior.

- if `asus-linux-control-center` is already on `PATH`, use it
- otherwise create or reuse a managed virtualenv and install the pinned Python wheel

### `system`

Force a system-installed core.

- no managed bootstrap
- fails if `asus-linux-control-center` is not already on `PATH`

### `managed`

Force the managed fallback.

- creates a private virtualenv
- installs the pinned wheel from the GitHub release by default
- supports `ALCC_WRAPPER_CORE_SOURCE` for development overrides

## CLI surface

The wrapper intentionally exposes a CLI first:

- `asusctl-control-center`
- `asusctl-control-center doctor`
- `asusctl-control-center diagnostics`
- `asusctl-control-center install-core`
- `asusctl-control-center version`

## JS API surface

The JS API stays intentionally small:

- `ensureCore()`
- `doctor()`
- `diagnostics()`
- `run()`

That keeps JavaScript focused on orchestration instead of duplicating backend logic.

## Dependency detection

The wrapper checks:

- Linux platform support
- display availability (`DISPLAY` or `WAYLAND_DISPLAY`)
- `python3` presence and version
- `python3 -m venv` availability
- optional system integration state:
  - `asusctl`
  - `systemctl`
  - `asusd.service`
  - `supergfxctl`
  - `supergfxd.service`

When a core executable is available, the wrapper calls `asus-linux-control-center --diagnostics-json` and uses that output as the structured contract for richer status reporting.

## Release coupling

The wrapper records both its own npm package version and the pinned Python core version.

Patch wrapper releases may update packaging, metadata, or docs while keeping the same pinned Python core.

For the current line, the managed installer is pinned to the exact `v0.1.0` GitHub release wheel plus SHA256 checksum verification. That gives the wrapper a deterministic bootstrap path without moving the Python implementation into Node.
