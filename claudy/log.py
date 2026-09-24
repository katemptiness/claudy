"""Error logging to ~/.claudy/error.log.

Claudy runs without a console most of the time, so unexpected errors are
written to a file instead of vanishing. Callers use `log.exception(...)`
inside an except block; the app keeps running.
"""

import logging
import os

from claudy.config import DATA_DIR

LOG_FILE = os.path.join(DATA_DIR, "error.log")

log = logging.getLogger("claudy")


def _configure():
    if log.handlers:
        return
    log.setLevel(logging.INFO)
    log.propagate = False
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8", delay=True)
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)


_configure()
