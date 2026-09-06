# NPM — Nick Pack Master Format

## Overview

NPM (Nick Pack Master) is the package format for Vision Linux. All packages must be signed with Ed25519 keys. Unsigned packages are rejected.

## Package Structure

```
app-1.0.npm (tar.zst)
├── app/
│   ├── bin/          Executables
│   ├── share/        Data, icons, .desktop files
│   └── ...           Application files
├── manifest.json     Package metadata
└── signature         Ed25519 signature
```

## manifest.json

```json
{
  "format": "npm",
  "format_version": 1,
  "name": "MyApp",
  "display_name": "My Application",
  "version": "1.0.0",
  "maintainer": "Vision Linux Team <team@visionlinux.dev>",
  "arch": "x86_64",
  "deps": ["gtk4", "python"],
  "entry": "bin/myapp",
  "desktop": "share/applications/myapp.desktop",
  "checksums": {
    "app": "sha256...",
    "manifest": "sha256..."
  },
  "homepage": "https://visionlinux.dev/apps/myapp"
}
```

## Signature

- Keys: Ed25519
- Public keys location: `/etc/visionlinux/keys/*.pub`
- Digest: `sha256(manifest.json || app-archives)` → Ed25519 signature
- Verification: offline, no network required
- 10 trusted keys by default

## Installation

1. `nickman install file.npm`
2. Signature verification (mandatory)
3. Root password prompt (polkit/pkexec)
4. Extract to `/opt/visionlinux/apps/<name>`
5. Create symlink in `/usr/bin/<name>`
6. Create desktop icon on user's desktop

## Removal

1. `nickman remove <name>`
2. Root password required
3. Remove app directory, symlink, desktop icon

## Commands

```bash
nickman install <file.npm>    # Install package
nickman remove <name>         # Remove package
nickman list                  # List installed packages
nickman verify <file.npm>     # Verify signature only
nickman keys                  # Show trusted keys
```

## Key Management

Generate 10 key pairs:
```bash
python3 keys/generate-keys.py
```

Keys are stored in:
- Private: `/etc/visionlinux/keys/<name>.priv` (on maintainer machines only)
- Public: `/etc/visionlinux/keys/<name>.pub` (on the ISO, trusted)

## Package Creation

```bash
nickman pack <dir> -o output.npm --key /path/to/private.key
```

The `--key` flag is required. Nickman will not create unsigned packages.
