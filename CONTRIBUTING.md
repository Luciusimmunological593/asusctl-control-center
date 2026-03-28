# Contributing

## Principles

- Keep support claims conservative.
- Do not expose controls that cannot be verified.
- Prefer explicit capability detection over device-family guessing.
- Preserve clean separation between UI, backend probing, and action execution.

## Setup

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e .[dev]
```

## Workflow

1. Run `make test`.
2. Run `make lint`.
3. If you changed UI or hardware probing, run `make diagnostics`.
4. If you touched feature support, update `docs/SUPPORT.md`.
5. If you changed behavior, update `docs/VALIDATION.md` and `CHANGELOG.md`.

## Issue reports

When filing bugs, include:

- distro and kernel version
- `asusctl info`
- whether `asusd.service` is active
- whether `supergfxctl` is installed
- the diagnostics report from `asus-linux-control-center --diagnostics`

## Pull requests

- Keep PRs focused.
- Document support assumptions explicitly.
- Avoid broad refactors without a concrete product benefit.
- Add parser or settings tests for new backend logic.
