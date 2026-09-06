#!/usr/bin/env python3
"""__init__.py for Vision Linux common library."""

from pathlib import Path

VISION_VERSION = "1.0.0"
VISION_NAME = "Vision Linux"
VISION_CONFIG = Path("/etc/visionlinux")
VISION_KEYS = VISION_CONFIG / "keys"
VISION_APPS = Path("/opt/visionlinux/apps")
VISION_REGISTRY = Path("/var/lib/visionlinux/npm/registry.json")
VISION_LOG = Path("/var/log/visionlinux")
