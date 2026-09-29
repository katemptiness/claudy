"""Error logging to ~/.claudy/error.log.

Claudy runs without a console most of the time, so unexpected errors are
written to a file instead of vanishing. Callers use `log.exception(...)`
inside an except block; the app keeps running. Once `install_excepthook()`
has run, whatever reaches Python's excepthooks uncaught is logged too.
"""

import contextlib
import logging
import logging.handlers
import os
import sys
import threading
import time
import traceback

from claudy.config import DATA_DIR

LOG_FILE = os.path.join(DATA_DIR, "error.log")
# The file is capped: one full file is kept as error.log.1 and the older one
# goes. Claudy runs for weeks, and a bug in the frame loop repeats sixty
# times a second.
LOG_MAX_BYTES = 1_000_000
# While the same error keeps repeating, it is written out once and after
# that only counted, with a line saying so this often.
REPEAT_SUMMARY_S = 10 * 60

log = logging.getLogger("claudy")


class RepeatFilter(logging.Filter):
    """Write a repeating error once, then only how often it came back.

    The frame loops log "tick failed" with a traceback whenever a frame
    raises, and a bug that is hit on every frame would otherwise bury the
    log in identical tracebacks. Records count as the same when their
    message, exception type and traceback lines match; the exception text
    may differ (it often holds a changing number).
    """

    def __init__(self, interval_s=REPEAT_SUMMARY_S, clock=time.monotonic):
        super().__init__()
        self.interval_s = interval_s
        self.clock = clock
        self._seen = {}     # key -> [last written at, repeats since then]

    @staticmethod
    def _key(record):
        try:
            message = record.getMessage()
        except Exception:
            # A bad format string; let the handler report it as usual
            message = str(record.msg)
        exc_type, tb = None, None
        if record.exc_info:
            exc_type, _, tb = record.exc_info
        lines = []
        while tb is not None:
            lines.append((tb.tb_frame.f_code.co_filename, tb.tb_lineno))
            tb = tb.tb_next
        return message, exc_type, tuple(lines)

    def filter(self, record):
        now = self.clock()
        key = self._key(record)
        seen = self._seen.get(key)
        if seen is None:
            if len(self._seen) > 100:
                self._seen.clear()      # a runaway of distinct errors
            self._seen[key] = [now, 0]
            return True
        written_at, repeats = seen
        if now - written_at < self.interval_s:
            seen[1] += 1
            return False
        seen[:] = [now, 0]
        if repeats:
            # Still repeating: a line with the count, not another traceback
            record.msg = "%s (again, %d more times in the last %d min)"
            record.args = (key[0], repeats + 1,
                           round((now - written_at) / 60))
            record.exc_info = record.exc_text = None
        return True


def _configure():
    if log.handlers:
        return
    log.setLevel(logging.INFO)
    log.propagate = False
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=1,
            encoding="utf-8", delay=True)
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"))
    handler.addFilter(RepeatFilter())
    log.addHandler(handler)


def install_excepthook():
    """Log exceptions that nothing caught, and still print them as usual.

    Covers a backend that fails to import, a crash while the Linux app
    starts, and errors in GTK callbacks, which PyGObject reports through
    sys.excepthook. Started from the Dock or a login item there is no
    terminal to print to, and without this they would leave no trace.

    AppKit callbacks never get here: PyObjC turns an exception in one into
    an NSException, which AppKit reports itself. That includes the macOS
    launch, which runs in applicationDidFinishLaunching_, so those
    callbacks run their bodies under reported() instead.
    """
    if getattr(sys.excepthook, "_claudy", False) is True:
        return      # already installed; a second one would log twice
    print_uncaught = sys.excepthook
    print_thread_uncaught = threading.excepthook

    def excepthook(exc_type, exc, tb):
        if not issubclass(exc_type, KeyboardInterrupt):
            log.error("uncaught exception", exc_info=(exc_type, exc, tb))
        print_uncaught(exc_type, exc, tb)

    def thread_excepthook(args):
        if not issubclass(args.exc_type, SystemExit):
            name = args.thread.name if args.thread else "?"
            log.error("uncaught exception in thread %s", name, exc_info=(
                args.exc_type, args.exc_value, args.exc_traceback))
        print_thread_uncaught(args)

    excepthook._claudy = True
    sys.excepthook = excepthook
    threading.excepthook = thread_excepthook


@contextlib.contextmanager
def reported(what):
    """Run a callback's body; log what it raises and print it as well.

    For callbacks whose exceptions never reach sys.excepthook (AppKit's,
    see install_excepthook). The error is swallowed, as AppKit would do.
    """
    try:
        yield
    except Exception:
        log.exception("%s failed", what)
        traceback.print_exc()


_configure()
