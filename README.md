# Vision Linux

USB-only Linux distribution with persistence. Cannot be installed on real disks — only USB flash drives.

## Features

- **USB Only** — Install only on USB flash drives
- **Two Modes**: Install (full setup) and Save (persistence)
- **Nickman** — Package manager with NPM format (signed with Ed25519)
- **10 Signing Keys** — All packages must be signed
- **Terminal + GUI** — `open <app>` launches GUI apps
- **Shift+Tab** — Switch between terminal and GUI
- **timeQmi** — Persistent time display
- **Wi-Fi** — Graphical Wi-Fi connection window
- **LAN Auto-connect** — Automatic Ethernet detection

## Quick Start

### Build ISO

```bash
sudo ./scripts/build.sh
```

### Write to USB

```bash
sudo dd if=build/visionlinux-*.iso of=/dev/sdX bs=4M status=progress
```

### Boot from USB

1. Insert USB drive
2. Reboot, select USB in BIOS
3. First boot runs setup wizard
4. Set root password, username, optional password
5. Enter terminal — you're ready!

## Commands

| Command | Description |
|---------|-------------|
| `open <app>` | Launch GUI application |
| `exit <app>` | Close GUI application |
| `nock -program` | List installed programs |
| `nickman install <file.npm>` | Install package |
| `nickman list` | List installed packages |
| `timeQmi` | Show time in terminal |
| `timeQmi --daemon` | Persistent time overlay |
| `wi-fi` | Open Wi-Fi connection window |
| `wi-fi --status` | Show Wi-Fi status |

## First Boot

1. Welcome screen
2. Root password (required for nickman)
3. Username (e.g. "vasya")
4. User password (optional — press Enter to skip)
5. Persistence test
6. Enter terminal

## Package Format (NPM)

```
app-1.0.npm (tar.zst)
├── app/           Application files
├── manifest.json  Metadata
└── signature      Ed25519 signature
```

## Signing Keys

10 Ed25519 key pairs for package signing:
- vision-main, vision-core, vision-apps, vision-drivers
- vision-shell, vision-net, vision-gui, vision-utils
- vision-media, vision-backup

Generate keys:
```bash
python3 keys/generate-keys.py
```

## Project Structure

```
vision-linux/
├── bin/             User commands (open, vision-shell, nock, timeQmi, wi-fi)
├── nickman/         Package manager (nickman.py, npm_format.py, signing.py)
├── keys/            Signing key generation
├── setup/           First-run wizard
├── rootfs/          Root filesystem
├── scripts/         Build scripts
├── configs/         Kernel configuration
├── docs/            Documentation
└── profiles/        Archiso profiles
```

## Requirements

- Build ISO: Linux host (or WSL2) with archiso
- Run: x86_64 PC with USB boot support
- Components: Python 3.11+, GTK4/PyGObject (for GUI)
