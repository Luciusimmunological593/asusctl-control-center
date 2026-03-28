# Publishing on GitHub

This guide covers two things:

1. how to publish the repository on GitHub
2. how to present the project so users can install and run it without guessing

## Recommended repository details

- Repository name: `asusctl-control-center`
- Description: `Capability-aware ASUS Linux control center for asusctl and optional supergfxctl`
- Visibility: `Public`
- License: `GPL-3.0-or-later`
- Topics: `asus`, `linux`, `asusctl`, `supergfxctl`, `pyqt6`, `qt`, `hardware-control`, `rog`

## First upload

### Step 1. Create the repository on GitHub

Create a new GitHub repository with the same name.

Recommended choices:

- owner: your user or organization
- visibility: public
- do not add a README from GitHub
- do not add a license from GitHub
- do not add a `.gitignore` from GitHub

This repository already contains those files locally.

### Step 2. Commit the local project

From the project root, run:

```bash
git add .
git commit -m "Initial public release"
```

### Step 3. Set the main branch

```bash
git branch -M main
```

### Step 4. Connect the local repository to GitHub

SSH:

```bash
git remote add origin git@github.com:YOUR-USER/asusctl-control-center.git
```

HTTPS:

```bash
git remote add origin https://github.com/YOUR-USER/asusctl-control-center.git
```

### Step 5. Push the repository

```bash
git push -u origin main
```

After that, the project will be live on GitHub.

## What users should understand immediately

The main GitHub page should answer these questions in the first screen:

1. What is this app?
2. What does it depend on?
3. How do I install it?
4. How do I run it?
5. How do I collect diagnostics if something is missing?

The top-level `README.md` in this repository is written to cover exactly that flow.

The repo name uses `asusctl` for trademark caution, while the app title remains `ASUS Linux Control Center` for user clarity and search relevance.

## Recommended GitHub text

### Repository description

Use this short description in the GitHub repository settings:

`Capability-aware ASUS Linux control center for asusctl and optional supergfxctl`

### Short project introduction

Use this wording at the top of the README or release notes:

`ASUS Linux Control Center is a desktop GUI for the Linux ASUS stack. It uses asusctl and optional supergfxctl, detects which features are really available on the current machine, and exposes diagnostics when the backend is incomplete.`

## Release checklist

Before creating a public release, run:

```bash
make test
make lint
make build
```

Then commit any final changes:

```bash
git add README.md docs/PUBLISHING.md CHANGELOG.md pyproject.toml
git commit -m "Prepare release"
```

## Create a GitHub release

### Step 1. Tag the release

Example for `v0.1.0`:

```bash
git tag -a v0.1.0 -m "v0.1.0"
git push origin main
git push origin v0.1.0
```

### Step 2. Draft the release on GitHub

On GitHub:

1. Open the repository.
2. Open `Releases`.
3. Click `Draft a new release`.
4. Choose tag `v0.1.0`.
5. Title it `ASUS Linux Control Center v0.1.0`.

### Step 3. Write direct release notes

Use a structure like this:

```text
First public release of ASUS Linux Control Center.

What it is:
- Desktop GUI for the Linux ASUS stack
- Uses asusctl and optional supergfxctl
- Detects supported capabilities instead of exposing fake controls

Before installing:
1. Install asusctl and asusd
2. Verify `asusctl info`
3. Verify `systemctl is-active asusd.service` returns `active`
4. Install supergfxctl only if you need graphics mode switching

Install:
- `python3 -m pip install .`
- or `./scripts/install-user.sh`

Run:
- `asus-linux-control-center`

Diagnostics:
- `asus-linux-control-center --diagnostics`
- `asus-linux-control-center --diagnostics-json`
```

### Step 4. Attach build artifacts if wanted

If you ran `make build`, upload files from `dist/` to the GitHub release so users can download the built source distribution or wheel directly.

## After publishing

Check these items once the repository is public:

- the README renders correctly on GitHub
- the install section is visible without scrolling too far
- the license is detected by GitHub
- the latest release has clear install and run commands
- issue reports ask users for diagnostics output
