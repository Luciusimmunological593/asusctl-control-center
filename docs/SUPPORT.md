# Support Model

## Research summary

This rebuild was designed around the current ASUS Linux ecosystem rather than around one machine.

Key upstream points that affect this project:

- `asusctl` already provides the real Linux control backend and includes an upstream GUI.
- Upstream explicitly states that many features depend on kernel work, patched kernels, or newer upstream support.
- Keyboard LED support is model-specific and relies on per-model support data.
- Fan curve support is limited to supported laptops, not every ASUS device.
- The ASUS Linux Arch guide now warns that `supergfxctl` is being phased out and should not be installed by default.
- The `supergfxctl` README says users mainly need it for dGPU suspend issues, VFIO, monitoring, hotplug, or ASUS eGPU workflows.
- Debian and Ubuntu families are still described by upstream guides as not officially supported, even though they may work in practice.

## What should work broadly

- Reading device info through `asusctl info`
- Detecting available ASUS profiles
- Switching active ASUS profiles when `asusd` is active
- Reading battery charge limits when the kernel exposes them
- Reading keyboard brightness when supported
- Reading Aura effect and power capabilities through CLI help output
- Exporting diagnostics

## What is model-dependent

- Fan curve editing
- Aura zones and effect coverage
- AniMe Matrix
- Slash and SCSI LEDs
- GPU MUX behavior
- NVIDIA dynamic boost and other firmware attributes
- Battery care threshold availability

## Graphics strategy

The app treats `supergfxctl` as optional, not assumed.

- If `supergfxctl` is installed, the Graphics page exposes its supported modes.
- A `supergfxctl` binary on `PATH` is not enough by itself; working mode switching also requires `supergfxd`, its systemd unit, and the system D-Bus policy.
- If it is absent, the app still shows graphics-related diagnostics and low-level firmware state when available.
- The app does not advise installing `supergfxctl` unless the user needs explicit graphics mode control, VFIO, eGPU handling, or dGPU power troubleshooting.

## Distro stance

- Arch/Fedora/openSUSE remain the upstream-friendly paths.
- Ubuntu and Debian are documented here because many users run them, but the docs remain explicit that upstream does not currently call them officially supported.
- The app avoids hard dependencies on distro-specific packaging so it can still be run where the backend stack exists.
