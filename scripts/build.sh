#!/usr/bin/env bash
# build.sh — Main build script for Vision Linux
# Builds the ISO image for Vision Linux distribution.
#
# Usage:
#   sudo ./scripts/build.sh
#
# Requirements:
#   - Linux host (or WSL2)
#   - archiso installed (pacman -S archiso)
#   - Root privileges

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROFILE_DIR="$PROJECT_DIR/profiles/visionlinux"
BUILD_DIR="$PROJECT_DIR/build"
OUTPUT_DIR="$PROJECT_DIR/build"

echo "╔══════════════════════════════════════════╗"
echo "║       Vision Linux Build System          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (sudo)"
    exit 1
fi

# Check mkarchiso
if ! command -v mkarchiso &> /dev/null; then
    echo "Error: mkarchiso not found. Install with: pacman -S archiso"
    exit 1
fi

echo "Profile: $PROFILE_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Step 1: Generate signing keys
echo "[1/5] Generating signing keys..."
python3 "$PROJECT_DIR/keys/generate-keys.py" --out-dir "$PROJECT_DIR/keys"
echo "      Keys generated."
echo ""

# Step 2: Prepare rootfs files
echo "[2/5] Preparing rootfs..."
# Copy Vision Linux components into the airootfs
AIROOTFS="$PROFILE_DIR/airootfs"
mkdir -p "$AIROOTFS/usr/local/bin"
mkdir -p "$AIROOTFS/opt/visionlinux/nickman"
mkdir -p "$AIROOTFS/opt/visionlinux/setup"
mkdir -p "$AIROOTFS/etc/visionlinux/keys"
mkdir -p "$AIROOTFS/etc/init.d"

# Copy bin/ commands
cp "$PROJECT_DIR/bin/open" "$AIROOTFS/usr/local/bin/"
cp "$PROJECT_DIR/bin/vision-shell" "$AIROOTFS/usr/local/bin/"
cp "$PROJECT_DIR/bin/nock" "$AIROOTFS/usr/local/bin/"
cp "$PROJECT_DIR/bin/timeQmi" "$AIROOTFS/usr/local/bin/"
cp "$PROJECT_DIR/bin/wi-fi" "$AIROOTFS/usr/local/bin/"
chmod +x "$AIROOTFS/usr/local/bin/"*

# Copy nickman
cp "$PROJECT_DIR/nickman/"*.py "$AIROOTFS/opt/visionlinux/nickman/"

# Copy setup wizard
cp "$PROJECT_DIR/setup/vision-setup.py" "$AIROOTFS/opt/visionlinux/setup/"

# Copy public keys
cp "$PROJECT_DIR/keys/"*.pub "$AIROOTFS/etc/visionlinux/keys/" 2>/dev/null || true

# Copy init script
cp "$PROJECT_DIR/rootfs/etc/init.d/vision-init" "$AIROOTFS/etc/init.d/"

echo "      Rootfs prepared."
echo ""

# Step 3: Kernel info
echo "[3/5] Kernel: linux-lts (archiso default)"
echo "      For custom kernel: edit configs/kernel.config"
echo ""

# Step 4: Build ISO with mkarchiso
echo "[4/5] Building ISO..."
mkdir -p "$BUILD_DIR"

archiso_cmd=$(which mkarchiso)
$archiso_cmd -w "$BUILD_DIR/work" -o "$OUTPUT_DIR" "$PROFILE_DIR"

# Step 5: Post-build
echo "[5/5] Post-build..."
ISO_FILE=$(ls -t "$OUTPUT_DIR"/*.iso 2>/dev/null | head -1)
if [ -n "$ISO_FILE" ]; then
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║  BUILD COMPLETE                          ║"
    echo "╠══════════════════════════════════════════╣"
    echo "║  ISO: $ISO_FILE"
    echo "║  Size: $(du -h "$ISO_FILE" | cut -f1)"
    echo "╚══════════════════════════════════════════╝"
    echo ""
    echo "To test: sudo ./scripts/launch.sh"
    echo "To write to USB: sudo dd if=$ISO_FILE of=/dev/sdX bs=4M status=progress"
else
    echo "Error: ISO not found in $OUTPUT_DIR"
    exit 1
fi
