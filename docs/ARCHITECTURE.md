# Vision Linux Architecture

## Overview

Vision Linux is a USB-only Linux distribution built from scratch (Linux From Scratch style) with a custom package manager (Nickman) and persistence system.

## Key Principles

1. **USB Only** — Cannot be installed on real disks. Only USB flash drives.
2. **Two Modes**:
   - **Install mode** — Full installation to USB. Real disks are hidden.
   - **Save mode** — Persistence via save file on USB. System never forgets.
3. **Signed Packages** — All packages must be signed with Ed25519 keys. Unsigned = rejected.
4. **Terminal + GUI** — Terminal is primary. GUI apps open via `open <app>` command.
5. **Shift+Tab** — Switch between terminal and running GUI applications.

## System Components

```
vision-linux/
├── kernel/              Linux LTS kernel (custom config)
├── rootfs/              Root filesystem
│   ├── init             PID 1 init
│   ├── bin/             Core utilities
│   └── etc/             System configuration
├── nickman/             Package manager
│   ├── nickman.py       Main package manager
│   ├── npm_format.py    NPM format handler
│   └── signing.py       Ed25519 signing
├── bin/                 User commands
│   ├── open             Launch GUI apps
│   ├── vision-shell     Terminal shell
│   ├── nock             List programs
│   ├── timeQmi          Time display
│   └── wi-fi            Wi-Fi manager
├── setup/               First-run wizard
├── keys/                Signing keys (10 pairs)
├── scripts/             Build scripts
└── configs/             Kernel/system configs
```

## Boot Process

1. BIOS/UEFI loads Limine bootloader
2. Limine loads Vision Linux kernel
3. Kernel starts init (vision-init)
4. init detects USB, determines mode (install/save)
5. If save mode: mount save file, restore user data
6. If install mode: show only USB drives, install
7. First boot: run setup wizard (root pass, username)
8. Launch vision-shell (terminal)

## Package Format: NPM (Nick Pack Master)

```
app-1.0.npm (tar.zst)
├── app/           Application files
├── manifest.json  Metadata
└── signature      Ed25519 signature
```

- Signed with one of 10 trusted keys
- Verified offline (no network needed)
- Installed to /opt/visionlinux/apps/<name>
- Desktop icon created automatically

## Signing Keys

10 Ed25519 key pairs:
- vision-main, vision-core, vision-apps, vision-drivers
- vision-shell, vision-net, vision-gui, vision-utils
- vision-media, vision-backup

Public keys in /etc/visionlinux/keys/
Private keys: kept by maintainers, never on the ISO

## Persistence System

### Save File
- Location: /visionlinux.save on USB
- Format: ext4 image file
- Size: 4GB default
- Contains: user data, installed packages, config changes

### Save Mode Flow
1. System detects USB drive
2. Looks for visionlinux.save file
3. If found: mount, restore /home, /opt, /etc changes
4. If not found: create new save file
5. On shutdown: sync changes to save file

### Install Mode Flow
1. Show only USB drives (real disks hidden)
2. User selects USB drive
3. Partition: 512MB FAT32 boot + rest ext4 root
4. Install Vision Linux to root partition
5. Create save file on root partition
6. Install bootloader

## GUI System

- **Compositor**: labwc (Wayland)
- **Panel**: Custom panel at bottom
- **Desktop**: Wallpaper, context menus
- **App Launch**: `open <AppName>` from terminal
- **Switching**: Shift+Tab between terminal and GUI apps
- **Close**: `exit <AppName>` in terminal

## Built-in Applications

- Firefox (web browser)
- File manager
- Text editor
- Media player
- Terminal (vision-shell)
