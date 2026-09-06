#!/usr/bin/env bash
# customize_airootfs.sh — Post-installation customization for Vision Linux
# Runs INSIDE the chroot during ISO build. Do NOT use /airootfs/ prefix.

set -e

echo "[visionlinux] Customizing root filesystem..."

# ---- Create directories ----
mkdir -p /etc/visionlinux/keys
mkdir -p /opt/visionlinux/apps
mkdir -p /opt/visionlinux/setup
mkdir -p /opt/visionlinux/nickman
mkdir -p /var/lib/visionlinux/npm
mkdir -p /var/log/visionlinux

# ---- Set permissions on commands ----
chmod 755 /usr/local/bin/open 2>/dev/null || true
chmod 755 /usr/local/bin/vision-shell 2>/dev/null || true
chmod 755 /usr/local/bin/nock 2>/dev/null || true
chmod 755 /usr/local/bin/timeQmi 2>/dev/null || true
chmod 755 /usr/local/bin/wi-fi 2>/dev/null || true

# ---- Copy signing keys (public only) ----
for keyfile in /etc/visionlinux/keys/*.pub; do
    [ -f "$keyfile" ] && chmod 644 "$keyfile"
done

# ---- Configure init script ----
chmod 755 /etc/init.d/vision-init 2>/dev/null || true

# ---- Set up default live user ----
useradd -m -G wheel,audio,video,storage,input -s /bin/bash user 2>/dev/null || true
echo "user:visionlinux" | chpasswd 2>/dev/null || true
echo "%wheel ALL=(ALL:ALL) ALL" > /etc/sudoers.d/visionlinux
chmod 440 /etc/sudoers.d/visionlinux

# ---- Enable services ----
systemctl enable NetworkManager 2>/dev/null || true
systemctl enable nftables 2>/dev/null || true

# ---- Auto-start terminal on tty1 ----
cat > /home/user/.bash_profile << 'BASHPROFILE'
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec vision-shell
fi
BASHPROFILE
chown user:user /home/user/.bash_profile

# ---- Labwc config (Wayland compositor) ----
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
chown -R user:user /home/user/.config

echo "[visionlinux] Customization complete."
