"""Test suite for Claudy's platform-independent core.

Run from the project root:
    /usr/bin/python3 -m unittest discover -s tests -t .

Importing this package points CLAUDY_HOME at a throwaway directory before
any Claudy module loads, so tests never touch the real ~/.claudy.
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
os.environ["CLAUDY_HOME"] = _TMP_HOME
