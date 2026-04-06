"""Settings persistence for Claudy (platform-independent)."""

import json
import os
from phrases import set_language

SETTINGS_DIR = os.path.expanduser("~/.claudy")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULTS = {
    "terminal": "Terminal",
    "schedule": "owl",
    "language": "en",
    "speech_interval": "1m",
    "user_name": "",
    "dev_mode": False,
    "gift_duration": "5m",
    "gift_limit": 3,
}

TERMINAL_OPTIONS = ["Terminal", "iTerm2", "Warp"]
LANGUAGE_OPTIONS = [("ru", "Русский"), ("en", "English")]

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

# Localized option lists: (key, EN title, RU title)
_SCHEDULE_OPTIONS = [
    ("owl", "Night Owl", "Сова"),
    ("lark", "Early Bird", "Жаворонок"),
]
_SPEECH_OPTIONS = [
    ("10s", "Often (10s)", "Часто (10с)"),
    ("1m", "Normal (1 min)", "Обычно (1 мин)"),
    ("10m", "Rarely (10 min)", "Редко (10 мин)"),
    ("30m", "Very rarely (30 min)", "Оч. редко (30 мин)"),
    ("1h", "Almost never (1 hr)", "Почти никогда (1 ч)"),
]
_GIFT_DURATION_OPTIONS = [
    ("10s", "10 sec", "10 сек"),
    ("1m", "1 min", "1 мин"),
    ("5m", "5 min", "5 мин"),
    ("15m", "15 min", "15 мин"),
    ("30m", "30 min", "30 мин"),
    ("1h", "1 hour", "1 час"),
]
_GIFT_LIMIT_OPTIONS = [
    (1, "1", "1"),
    (3, "3", "3"),
    (5, "5", "5"),
    (10, "10", "10"),
    (0, "Unlimited", "Безлимит"),
]

# Labels: (EN, RU)
_LABELS = {
    "terminal": ("Open Claude Code in:", "Открывать Claude Code в:"),
    "schedule": ("Schedule mode:", "Режим расписания:"),
    "language": ("Language:", "Язык / Language:"),
    "name": ("Your name:", "Ваше имя:"),
    "speech": ("Speech frequency:", "Частота фраз:"),
    "gift_dur": ("Gift duration:", "Время подарка:"),
    "gift_lim": ("Gifts per day:", "Подарков в день:"),
    "dev": ("Developer mode", "Режим разработчика"),
    "save": ("Save", "Сохранить"),
    "title": ("Claudy — Settings", "Claudy — Настройки"),
}


def _loc(options, lang):
    """Get (key, title) pairs for the current language from trilingual options."""
    idx = 1 if lang == "en" else 2
    return [(o[0], o[idx]) for o in options]


def _l(key, lang):
    """Get a label in the current language."""
    en, ru = _LABELS[key]
    return en if lang == "en" else ru


class Settings:
    """Load, save, and access settings."""

    _instance = None

    @classmethod
    def shared(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._data = dict(DEFAULTS)
        self._load()
        set_language(self._data["language"])

    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    saved = json.load(f)
                for k in DEFAULTS:
                    if k in saved:
                        self._data[k] = saved[k]
            except (json.JSONDecodeError, IOError):
                pass

    def save(self):
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def terminal(self):
        return self._data["terminal"]

    @terminal.setter
    def terminal(self, value):
        self._data["terminal"] = value

    @property
    def schedule(self):
        return self._data["schedule"]

    @schedule.setter
    def schedule(self, value):
        self._data["schedule"] = value

    @property
    def language(self):
        return self._data["language"]

    @language.setter
    def language(self, value):
        self._data["language"] = value
        set_language(value)

    @property
    def speech_interval(self):
        return self._data["speech_interval"]

    @speech_interval.setter
    def speech_interval(self, value):
        self._data["speech_interval"] = value

    @property
    def user_name(self):
        return self._data.get("user_name", "")

    @user_name.setter
    def user_name(self, value):
        self._data["user_name"] = value

    @property
    def dev_mode(self):
        return self._data.get("dev_mode", False)

    @dev_mode.setter
    def dev_mode(self, value):
        self._data["dev_mode"] = value

    @property
    def gift_duration(self):
        return self._data.get("gift_duration", "5m")

    @gift_duration.setter
    def gift_duration(self, value):
        self._data["gift_duration"] = value

    @property
    def gift_limit(self):
        return self._data.get("gift_limit", 3)

    @gift_limit.setter
    def gift_limit(self, value):
        self._data["gift_limit"] = value


