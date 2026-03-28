# asusctl-control-center

`asusctl-control-center` is a thin npm wrapper around the Python/PyQt `asus-linux-control-center` application.

It does not reimplement hardware logic in JavaScript. Instead, it:

- prefers a system-installed `asus-linux-control-center` when present
- can bootstrap a managed Python virtual environment as a fallback
- exposes `doctor`, `diagnostics`, `install-core`, and launch commands from Node

## Install status

The package is published on npm as `asusctl-control-center`.

Install it normally with:

```bash
npm install -g asusctl-control-center
```

For local development from a checkout:

```bash
npm install -g ./npm-wrapper
```

Then verify the machine before launch:

```bash
asusctl-control-center doctor
asusctl-control-center
```

The wrapper still depends on the same Linux ASUS backend stack as the Python app:

- `asusctl`
- `asusd`
- optional `supergfxctl`
- optional `supergfxd`

## Commands

```bash
asusctl-control-center
asusctl-control-center doctor
asusctl-control-center doctor --json
asusctl-control-center diagnostics
asusctl-control-center diagnostics --json
asusctl-control-center install-core
```

## Wrapper behavior

- `auto` mode prefers an existing `asus-linux-control-center` on `PATH`
- `managed` mode creates a private virtualenv and installs the pinned wheel from the GitHub release
- `system` mode only uses the existing launcher on `PATH`

## Environment overrides

- `ALCC_WRAPPER_CORE_SOURCE`: override the managed core install source
- `ALCC_WRAPPER_CACHE_DIR`: override the managed core cache directory

## Development

Run the wrapper tests from the repository root:

```bash
npm --prefix npm-wrapper test
```
