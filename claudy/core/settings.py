"""Settings persistence for Claudy (platform-independent)."""

import json
import os

from claudy.config import DATA_DIR
from claudy.content.phrases import set_language
from claudy.log import log

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

TERMINAL_OPTIONS = ["Terminal", "iTerm2", "Warp"]
LINUX_TERMINAL_OPTIONS = ["gnome-terminal", "kitty", "alacritty"]

# Where Claudy sits relative to the Dock, in pixels. 0 is the Dock baseline
# (the default); positive raises the crab above the Dock, negative sinks it
# below. The slider lets each user dial in their preferred height.
VERTICAL_OFFSET_MIN = -50
VERTICAL_OFFSET_MAX = 50

# How high the named star hangs above the Dock line, in pixels (to the bottom
# of its little window). The floor keeps it clear of the speech bubble, which
# sits right above Claudy's head; above that it is a matter of taste and of
# which windows the user keeps open, so it is a slider.
STAR_HEIGHT_MIN = 150
STAR_HEIGHT_MAX = 400

# How many icons are in the Dock — used to estimate its width so Claudy paces
# only across the Dock. The user updates this when they add/remove Dock items.
DOCK_ICONS_MIN = 1
DOCK_ICONS_MAX = 50

# Cooldown ranges in ms for each speech interval
SPEECH_COOLDOWNS = {
    "10s": (8000, 12000),
    "1m": (45000, 75000),
    "10m": (500000, 700000),
    "30m": (1500000, 2100000),
    "1h": (3000000, 4200000),
}

# Duration in seconds for each gift duration option
GIFT_DURATIONS = {
    "10s": 10, "1m": 60, "5m": 300,
    "15m": 900, "30m": 1800, "1h": 3600,
}

# Cooldown in seconds for user-to-Claudy gifts
GIFT_COOLDOWNS = {
    "off": 0, "1m": 60, "5m": 300,
    "10m": 600, "30m": 1800,
}


def read_json(path):
    """The JSON object saved at `path`, or {} if there is none.

    A file that is there but can't be used (a typo from a hand edit, a write
    cut short, text that isn't UTF-8, anything but a JSON object) is moved
    aside to `path + ".bad"` and logged. Starting fresh would otherwise write
    over it at the first save, and it may hold something the user wants back.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        # ValueError covers both broken JSON and bytes that aren't UTF-8
        problem = e
    else:
        if isinstance(data, dict):
            return data
        problem = f"expected a JSON object, found {type(data).__name__}"
    bad = path + ".bad"
    try:
        os.replace(path, bad)
        log.error("could not read %s (%s); moved it to %s and started fresh",
                  path, problem, bad)
    except OSError:
        log.exception("could not read %s (%s) or move it aside", path, problem)
    return {}


def write_json_atomic(path, data):
    """Save `data` as JSON so that a crash never leaves half a file.

    It goes to a temp file first, which replaces the old one only once it is
    safely on disk. Raises OSError (or TypeError for data JSON can't hold);
    callers log it, since nothing here is worth crashing over.
    """
    content = json.dumps(data, indent=2, ensure_ascii=False)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


class _Setting:
    """A persisted setting stored in Settings._data under its attribute name."""

    def __init__(self, default):
        self.default = default

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.coerce(obj._data.get(self.name, self.default))

    def __set__(self, obj, value):
        obj._data[self.name] = self.coerce(value)

    def coerce(self, value):
        return value


class _IntSetting(_Setting):
    """An integer setting clamped to [lo, hi]; junk falls back to default."""

    def __init__(self, default, lo, hi):
        super().__init__(default)
        self.lo, self.hi = lo, hi

    def coerce(self, value):
        try:
            value = int(round(float(value)))
        except (TypeError, ValueError):
            value = self.default
        return max(self.lo, min(self.hi, value))


class _LanguageSetting(_Setting):
    """Switching the language also switches the phrase translator."""

    def __set__(self, obj, value):
        super().__set__(obj, value)
        set_language(value)


class Settings:
    """Load, save, and access settings. Use Settings.shared()."""

    terminal = _Setting("Terminal")
    schedule = _Setting("owl")
    language = _LanguageSetting("en")
    speech_interval = _Setting("1m")
    user_name = _Setting("")
    dev_mode = _Setting(False)
    gift_duration = _Setting("5m")
    gift_limit = _Setting(3)
    gift_cooldown = _Setting("10m")
    vertical_offset = _IntSetting(0, VERTICAL_OFFSET_MIN, VERTICAL_OFFSET_MAX)
    dock_icons = _IntSetting(13, DOCK_ICONS_MIN, DOCK_ICONS_MAX)
    star_height = _IntSetting(160, STAR_HEIGHT_MIN, STAR_HEIGHT_MAX)

    _instance = None

    @classmethod
    def shared(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def fields(cls):
        return {name: attr for name, attr in vars(cls).items()
                if isinstance(attr, _Setting)}

    def __init__(self):
        self._data = {name: f.default for name, f in self.fields().items()}
        self._load()
        set_language(self.language)

    def _load(self):
        saved = read_json(SETTINGS_FILE)
        for name, field in self.fields().items():
            if name in saved:
                self._data[name] = field.coerce(saved[name])

    def save(self):
        try:
            write_json_atomic(SETTINGS_FILE, self._data)
        except Exception:
            # The settings in use are already applied; only the file is
            # stale. Never crash the Save button over it.
            log.exception("failed to save settings")

    # Derived values

    def speech_cooldown_range(self):
        """(min_ms, max_ms) between idle phrases."""
        return SPEECH_COOLDOWNS.get(self.speech_interval, SPEECH_COOLDOWNS["1m"])

    def gift_duration_seconds(self):
        return GIFT_DURATIONS.get(self.gift_duration, 300)

    def gift_cooldown_seconds(self):
        return GIFT_COOLDOWNS.get(self.gift_cooldown, 600)
