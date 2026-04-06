#!/usr/bin/env python3
"""Claudy — desktop companion. Cross-platform entry point."""

import sys
import os

# Ensure the project root is in sys.path so shared modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if sys.platform == "darwin":
        from backends.macos.app import main as _main
    elif sys.platform.startswith("linux"):
        from backends.linux.app import main as _main
    else:
        print(f"Unsupported platform: {sys.platform}")
        sys.exit(1)
    _main()


if __name__ == "__main__":
    main()
