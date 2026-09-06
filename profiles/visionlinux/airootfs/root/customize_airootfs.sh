#!/usr/bin/env bash
# customize_airootfs.sh — Post-installation customization for Vision Linux
# This script runs INSIDE the chroot during ISO build.
# Do NOT use /airootfs/ prefix — we are already inside the target rootfs.

set -e

echo "[visionlinux] Customizing root filesystem..."

# ---- Create directories ----
mkdir -p /etc/visionlinux/keys
mkdir -p /opt/visionlinux/apps
mkdir -p /opt/visionlinux/setup
mkdir -p /opt/visionlinux/nickman
mkdir -p /var/lib/visionlinux/npm
mkdir -p /var/log/visionlinux

# ---- Copy user commands to /usr/local/bin ----
# These are already placed by archiso build process from the profile
chmod +x /usr/local/bin/open 2>/dev/null || true
chmod +x /usr/local/bin/vision-shell 2>/dev/null || true
chmod +x /usr/local/bin/nock 2>/dev/null || true
chmod +x /usr/local/bin/timeQmi 2>/dev/null || true
chmod +x /usr/local/bin/wi-fi 2>/dev/null || true

# ---- Copy signing keys (public only — private keys never on ISO) ----
# Keys are generated before build and placed in the profile
for keyfile in /etc/visionlinux/keys/*.pub; do
    if [ -f "$keyfile" ]; then
        chmod 644 "$keyfile"
    fi
done

# ---- Configure init script ----
if [ -f /etc/init.d/vision-init ]; then
    chmod +x /etc/init.d/vision-init
fi

# ---- Set up default live user ----
useradd -m -G wheel,audio,video,storage,input -s /bin/bash user 2>/dev/null || true
echo "user:visionlinux" | chpasswd 2>/dev/null || true
echo "%wheel ALL=(ALL:ALL) ALL" > /etc/sudoers.d/visionlinux

# ---- Enable services ----
systemctl enable NetworkManager 2>/dev/null || true
systemctl enable nftables 2>/dev/null || true

# ---- Set default shell for live user ----
cat > /home/user/.bash_profile << 'BASHPROFILE'
# Vision Linux — auto-start terminal
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec vision-shell
fi
BASHPROFILE
chown user:user /home/user/.bash_profile

# ---- Auto-start setup wizard on first boot ----
mkdir -p /home/user/.config/autostart
cat > /home/user/.config/autostart/vision-setup.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Vision Linux Setup
Exec=/opt/visionlinux/setup/vision-setup.py
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
chown -R user:user /home/user/.config

# ---- Configure Wayland session (labwc) ----
mkdir -p /home/user/.config/labwc
cat > /home/user/.config/labwc/rc.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<labwc_config>
  <keyboard>
    <keybind key="S-Tab">
      <action name="NextWindow"/>
    </keybind>
    <keybind key="A-Tab">
      <action name="NextWindow"/>
    </keybind>
  </keyboard>
</labwc_config>
EOF
chown -R user:user /home/user/.config/labwc

# ---- Set permissions ----
chmod 755 /etc/init.d/vision-init 2>/dev/null || true

echo "[visionlinux] Customization complete."
