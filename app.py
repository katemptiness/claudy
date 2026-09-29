#!/usr/bin/env python3
"""Claudy — desktop companion. Cross-platform entry point."""

import sys
import os

# Ensure the project root is in sys.path so shared modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # First, so that even a backend that fails to import leaves a trace in
    # ~/.claudy/error.log when there is no terminal to print it to
    from claudy.log import install_excepthook
    install_excepthook()

    if sys.platform == "darwin":
        from claudy.backends.macos.app import main as _main
    elif sys.platform.startswith("linux"):
        from claudy.backends.linux.app import main as _main
    else:
        print(f"Unsupported platform: {sys.platform}")
        sys.exit(1)
    _main()


if __name__ == "__main__":
    main()
