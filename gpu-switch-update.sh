#!/bin/bash
set -e

# 1. Simplified startx wrapper
tee /usr/local/bin/startx > /dev/null << 'EOF'
#!/bin/bash
# GPU session switcher — usage: startx igpu
# Everything else passes straight through to real startx.
# To revert: sudo rm /usr/local/bin/startx

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
EOF
chmod +x /usr/local/bin/startx

# 2. Fix igpu config: add Screen + ServerLayout so amdgpu is actually used
tee /etc/X11/xorg-igpu.d/10-igpu.conf > /dev/null << 'EOF'
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
EOF

# 3. Remove nested duplicate dir from triple install run
rm -rf /etc/X11/xorg-igpu.d/xorg-igpu.d

echo "Done."
