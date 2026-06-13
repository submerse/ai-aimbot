# iGPU / GPU Session Switcher

## Goal

Allow starting an X session on the AMD iGPU (Granite Ridge, Ryzen 9 9950X3D)
so the RTX 4090 can be freed for VFIO VM passthrough while the host desktop
stays alive.

## Usage

```
startx igpu          # AMD iGPU session (4090 free for VM/LLM)
startx               # normal NVIDIA session (unchanged — uses ~/.xinitrc or client arg)
startx /usr/bin/i3   # normal NVIDIA session (unchanged — passes straight through)
```

## Files Created (new — nothing existing was modified)

### `/usr/local/bin/startx`
Thin wrapper that intercepts `igpu` and passes everything else straight through
to `/usr/bin/startx` unchanged.

```bash
#!/bin/bash
case "$1" in
  igpu)
    exec /usr/bin/startx "$HOME/.xinitrc-igpu" -- \
      -config /dev/null \
      -configdir /etc/X11/xorg-igpu.d
    ;;
  *)
    exec /usr/bin/startx "$@"
    ;;
esac
```

### `/etc/X11/xorg-igpu.d/`
Dedicated Xorg config directory for iGPU sessions.

**10-igpu.conf** — amdgpu driver, explicit Screen + ServerLayout so Xorg is
forced to use AMD even when the NVIDIA OutputClass is also active:
```
Section "Device"
    Identifier "iGPU"
    Driver     "amdgpu"
    BusID      "PCI:13:0:0"
EndSection

Section "Screen"
    Identifier "iGPU Screen"
    Device     "iGPU"
EndSection

Section "ServerLayout"
    Identifier "iGPU Layout"
    Screen     "iGPU Screen"
EndSection
```

**00-keyboard.conf** — US layout, swapyz (same as main session)  
**50-mouse-acceleration.conf** — libinput fallback accel  
**50-mouse-speed.conf** — AccelSpeed -0.5

### `~/.xinitrc-igpu`
```sh
#!/bin/sh
xrandr --auto
exec /usr/bin/i3
```
First time you run `startx igpu`, check output names with `xrandr --query`
and update this file if you want a specific resolution/refresh rate, e.g.:
```
xrandr --output DisplayPort-0 --mode 1920x1080 --rate 144
```

## Files Unchanged

- `/etc/X11/xorg.conf` — NVIDIA layout (untouched)
- `/etc/X11/xorg.conf.d/` — NVIDIA OutputClass etc. (untouched)
- `~/.xinitrc` — normal session xinitrc (untouched)

## How It Works

`startx igpu` calls Xorg with:
- `-config /dev/null` — suppresses `/etc/X11/xorg.conf` (the NVIDIA layout)
- `-configdir /etc/X11/xorg-igpu.d` — uses only the AMD device/screen/input configs

The explicit `ServerLayout "iGPU Layout"` in the configdir forces Xorg to use
only the AMD screen even though the NVIDIA OutputClass from
`/usr/share/X11/xorg.conf.d/` still fires.

Note: NVIDIA driver will still be loaded by Xorg as an offload provider (PRIME).
If you need NVIDIA completely free for VFIO, kill the igpu X session first, then
let the VM start script unload `nvidia_drm` / bind `vfio-pci`.

## Known Issue (TODO)

`-config /dev/null` has not been confirmed working yet — both test logs from
Jun 11 showed `(==) Using config file: "/etc/X11/xorg.conf"` (default, no
`-config` flag received), meaning those were normal GPU sessions, not igpu
tests. After rebooting, check `~/.local/share/xorg/Xorg.0.log` after running
`startx igpu`: look for `(++) Using config file: "/dev/null"`. If it still
shows xorg.conf, change the wrapper to use
`-config /etc/X11/xorg-igpu.conf` (a real file) instead.

## Revert (complete removal)

```bash
sudo rm /usr/local/bin/startx
sudo rm -rf /etc/X11/xorg-igpu.d
# ~/.xinitrc-igpu is harmless but can be removed:
rm ~/.xinitrc-igpu
```

Nothing else was modified — revert is instant.

## Troubleshooting

**Screen goes black for 1 second then back to TTY (GPU or iGPU session)**  
Usually a transient post-VFIO-VM state issue. Reboot to clear it. Confirmed
Jun 11 2026: two GPU sessions failed this way right after VFIO VM crashed at
16:27:42; both showed i3 failing to connect to X (no errorlog created).

**`startx igpu` still shows NVIDIA output**  
Check log: if `-config` fallback is happening, replace `-config /dev/null`
with `-config /etc/X11/xorg-igpu.conf` and create that file with the Device +
Screen + ServerLayout sections.

**xrandr output name mismatch**  
Run `xrandr --query` inside the igpu session to find the real output name
(e.g. `DisplayPort-0`, `HDMI-A-1`), then update `~/.xinitrc-igpu`.
