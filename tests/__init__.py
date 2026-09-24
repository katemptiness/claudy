"""Test suite for Claudy's platform-independent core.

Run from the project root:
    /usr/bin/python3 -m unittest discover -s tests -t .

Importing this package redirects all persistence (settings, memory, error
log) into a throwaway directory so tests never touch the real ~/.claudy.
"""

import atexit
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_TMP_HOME = tempfile.mkdtemp(prefix="claudy-tests-")
atexit.register(shutil.rmtree, _TMP_HOME, ignore_errors=True)

import settings as _settings  # noqa: E402
import memory as _memory  # noqa: E402

_settings.SETTINGS_DIR = _TMP_HOME
_settings.SETTINGS_FILE = os.path.join(_TMP_HOME, "settings.json")
_memory.MEMORY_DIR = _TMP_HOME
_memory.MEMORY_FILE = os.path.join(_TMP_HOME, "memory.json")
