"""Build Claudy as a standalone macOS app.

Usage:
    pip install py2app
    python setup.py py2app

The app will be created in dist/Claudy.app
"""

import os
import sys

from setuptools import setup

APP = ['app.py']

# Find libffi for bundling (needed by ctypes/PyObjC). A conda-style Python
# keeps its own copy in lib/ next to the interpreter doing the build; a venv
# made from one has no lib/ of its own, hence base_prefix as well. Pythons
# that use the system libffi have none there, and bundle nothing.
FRAMEWORKS = []
for _prefix in (sys.prefix, sys.base_prefix):
    _libffi = os.path.join(_prefix, 'lib', 'libffi.8.dylib')
    if os.path.exists(_libffi):
        FRAMEWORKS.append(_libffi)
        break

OPTIONS = {
    'argv_emulation': False,
    # Built from Claudy's own sprites by tools/make_icon.py
    'iconfile': 'assets/claudy.icns',
    'plist': {
        'CFBundleName': 'Claudy',
        'CFBundleDisplayName': 'Claudy',
        'CFBundleIdentifier': 'com.katemptiness.claudy',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # No Dock icon (the crab IS on the Dock)
    },
    # The whole package: the backend is imported at runtime by app.py
    'packages': ['claudy'],
    'excludes': [
        'numpy', 'docutils', 'setuptools', 'pkg_resources',
        'unittest', 'html', 'http', 'pydoc',
        'tkinter', 'PIL', 'matplotlib', 'scipy', 'pandas',
        'wheel', 'pip', 'distutils', 'test', 'gi', 'cairo',
    ],
    'includes': ['objc', 'AppKit', 'Quartz', 'Foundation'],
    'frameworks': FRAMEWORKS,
}

setup(
    name='Claudy',
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
