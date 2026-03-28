# Troubleshooting

## The app opens but most controls are disabled

Check:

```bash
asusctl info
systemctl is-active asusd.service
```

If `asusctl` is missing or `asusd.service` is inactive, the UI will correctly disable most write actions.

## Fan curves are unavailable

That usually means one of the following:

- the laptop does not expose fan curve editing
- the current kernel or firmware does not expose the feature
- the backend stack is too old for the device

Use:

```bash
asusctl fan-curve --mod-profile Performance
```

If that command fails, the app will keep the curve editor in read-only mode.

## Graphics page says `supergfxctl` is optional and not installed

That is intentional. Install `supergfxctl` only if you actually need explicit graphics mode switching or a related workflow. Do not install it just because the page exists.

## Graphics page says the binary is installed but the daemon is unavailable

That means the CLI was found, but `supergfxd` is still missing, disabled, inactive, or blocked from owning the `org.supergfxctl.Daemon` system bus name.

`supergfxctl` is not a user-local binary only feature. A working setup needs:

- the `supergfxctl` and `supergfxd` binaries installed system-wide
- the `supergfxd.service` systemd unit installed and enabled
- the system D-Bus policy installed for `org.supergfxctl.Daemon`

If only the binary exists, the app will correctly keep graphics mode switching disabled.

## Ubuntu-specific problems

Ubuntu may work well on some ASUS devices, but upstream still treats Ubuntu and Debian families as not officially supported. Newer kernels generally improve support. If the app sees missing capabilities, the limitation may be below the UI layer.

## Filing a useful bug

Attach:

- output from `asus-linux-control-center --diagnostics`
- output from `asusctl info`
- distro name and kernel version
- the exact model family and board name
