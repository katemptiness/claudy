"""Build Claudy as a standalone macOS app.

Usage:
    pip install py2app
    python setup.py py2app

The app will be created in dist/Claudy.app
"""

import os

from setuptools import setup

APP = ['app.py']

# Find libffi for bundling (needed by ctypes/PyObjC)
_conda = os.path.expanduser('~/anaconda3/lib')
FRAMEWORKS = []
_libffi = os.path.join(_conda, 'libffi.8.dylib')
if os.path.exists(_libffi):
    FRAMEWORKS.append(_libffi)

OPTIONS = {
    'argv_emulation': False,
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
