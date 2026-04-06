"""System event subscriptions — app launches, sleep/wake (Linux)."""

import random
import subprocess

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib

from phrases import t, format_phrase, SLEEP_PHRASES, WAKE_PHRASES, APP_COUNT_PHRASES

# Process names that trigger the "working" activity
CODING_APPS = {
    "gnome-terminal-", "tilix", "terminator",
    "alacritty", "kitty", "warp-terminal", "xterm",
    "code", "codium", "sublime_text",
    "pycharm", "idea", "webstorm", "clion",
}

# Process names that trigger the "music" activity
MUSIC_APPS = {
    "spotify", "rhythmbox", "lollypop", "gnome-music",
}

# Process name fragment → possible phrases
APP_PHRASES = {
    # Browsers
    "firefox": [
        "о, опять сидим в Интернете?", "что гуглим?",
        "Firefox! олдскул", "интернет! бесконечный...",
    ],
    "chrome": [
        "о, опять сидим в Интернете?", "что гуглим?",
        "Chrome съел всю память!", "интернет! бесконечный...",
    ],
    "chromium": [
        "о, опять сидим в Интернете?", "что гуглим?",
        "Chrome съел всю память!", "интернет! бесконечный...",
    ],
    "vivaldi": [
        "о, опять сидим в Интернете?", "что гуглим?",
        "интернет! бесконечный...", "опять мемы?",
    ],
    # Terminals
    "gnome-terminal": [
        "хакерское время!", "терминал? кодим!",
        "sudo краб!", "о, командная строка!",
    ],
    "alacritty": [
        "хакерское время!", "терминал? кодим!",
        "о, Alacritty! быстро", "sudo краб!",
    ],
    "kitty": [
        "хакерское время!", "терминал? кодим!",
        "о, Kitty! красиво", "sudo краб!",
    ],
    "tilix": [
        "хакерское время!", "терминал? кодим!",
        "sudo краб!", "о, командная строка!",
    ],
    # Code editors
    "code": [
        "кодим? кодим.", "VS Code!",
        "время писать код!", "баги не ждут!", "а юнит-тесты?",
    ],
    "sublime_text": [
        "кодим? кодим.", "Sublime!",
        "время писать код!", "баги не ждут!",
    ],
    "pycharm": [
        "кодим? кодим.", "PyCharm!",
        "время писать код!", "баги не ждут!",
    ],
    # Music
    "spotify": [
        "о, музыка! 🎵", "что слушаем?",
        "♪ ля-ля-ля ♪", "потанцуем?", "хороший вкус!",
    ],
    "rhythmbox": [
        "о, музыка! 🎵", "что слушаем?",
        "♪ ля-ля-ля ♪", "потанцуем?",
    ],
    # Messengers
    "telegram": [
        "кто-то написал?", "Telegram!",
        "сплетни? 👀", "кому отвечаем?",
    ],
    # File manager
    "nautilus": [
        "ищем что-то?", "где же этот файл...",
        "столько папок!", "порядок наведём?",
    ],
    "thunar": [
        "ищем что-то?", "где же этот файл...",
        "столько папок!", "порядок наведём?",
    ],
    # Claude
    "claude": [
        "о, это же я! ну, почти...", ":3",
        "привет, другая я!", "мы похожи!",
    ],
    # Text editors
    "gedit": [
        "пишем роман?", "вдохновение пришло?",
        "слова, слова, слова...", "творим!",
    ],
    "libreoffice": [
        "пишем роман?", "вдохновение пришло?",
        "слова, слова, слова...", "творим!",
    ],
    "eog": [
        "о, фоточки!", "красивое!",
        "а это кто? 👀", "📸!",
    ],
}


class SystemEventHandler:
    """Monitor system events on Linux via D-Bus and process polling."""

    def __init__(self, character):
        self.character = character
        self._known_apps = set()  # app names seen this session
        self._app_cooldowns = {}  # app_key → last trigger time
        self._speech_fn = None  # set by app.py: fn(phrase, crab_x, crab_y)
        self._setup_sleep_wake()
        self._setup_app_monitor()

    def set_speech(self, speech_fn):
        """Set callback for showing speech: fn(phrase)."""
        self._speech_fn = speech_fn

    def _setup_sleep_wake(self):
        """Listen to logind PrepareForSleep signal."""
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            bus.signal_subscribe(
                "org.freedesktop.login1",
                "org.freedesktop.login1.Manager",
                "PrepareForSleep",
                "/org/freedesktop/login1",
                None,
                Gio.DBusSignalFlags.NONE,
                self._on_prepare_for_sleep,
                None,
            )
        except Exception:
            pass  # logind not available

    def _on_prepare_for_sleep(self, conn, sender, path, iface, signal, params, data):
        """Handle sleep/wake from logind."""
        going_to_sleep = params.unpack()[0]
        if going_to_sleep:
            self._handle_sleep()
        else:
            self._handle_wake()

    def _handle_sleep(self):
        from memory import Memory
        from settings import Settings
        if Memory.shared().is_attached():
            name = Settings.shared().user_name
            phrase = format_phrase(random.choice(SLEEP_PHRASES), name=name)
            self.character.current_message = phrase
            if self._speech_fn:
                self._speech_fn(phrase)

        self.character.state = "sleeping"
        self.character.phase_index = 0
        self.character.phase_timer = 0
        self.character.frame_timer = 0
        self.character.frame_index = 0
        self.character.particle_timer = 0

    def _handle_wake(self):
        self.character._enter_idle()
        from memory import Memory
        from settings import Settings
        if Memory.shared().is_attached():
            name = Settings.shared().user_name
            msg = format_phrase(random.choice(WAKE_PHRASES), name=name)
        else:
            msg = t("*зевает*")
        self.character.current_message = msg
        if self._speech_fn:
            self._speech_fn(msg)

    def _setup_app_monitor(self):
        """Start polling for running apps (by name, not PID)."""
        self._scan_running_apps()
        GLib.timeout_add_seconds(3, self._check_new_apps)

    def _scan_running_apps(self):
        """Snapshot currently running app names."""
        try:
            out = subprocess.check_output(
                ['ps', 'ax', '-o', 'comm='], text=True, timeout=2)
            for line in out.strip().split('\n'):
                name = line.strip().lower()
                key = self._match_app(name)
                if key:
                    self._known_apps.add(key)
        except Exception:
            pass

    def _match_app(self, proc_name):
        """Match a process name to an APP_PHRASES key. Returns key or None."""
        for key in APP_PHRASES:
            if key in proc_name:
                return key
        return None

    def _check_new_apps(self):
        """Poll for newly launched apps (by name, with cooldown)."""
        import time
        now = time.time()
        try:
            out = subprocess.check_output(
                ['ps', 'ax', '-o', 'comm='], text=True, timeout=2)
            current_apps = set()
            for line in out.strip().split('\n'):
                name = line.strip().lower()
                key = self._match_app(name)
                if key:
                    current_apps.add(key)

            # Detect newly appeared app names (not seen before)
            new_apps = current_apps - self._known_apps
            for key in new_apps:
                # Cooldown: ignore if we reacted to this app < 60s ago
                last = self._app_cooldowns.get(key, 0)
                if now - last < 60:
                    continue
                self._app_cooldowns[key] = now
                self._on_app_launched(key)

            self._known_apps = current_apps
        except Exception:
            pass
        return True  # keep timer alive

    def _on_app_launched(self, app_key):
        """React to a newly detected app."""
        from memory import Memory
        count = Memory.shared().record_app_launch(app_key)

        # Pick phrase
        phrase = None
        if count >= 3 and random.random() < 0.5:
            phrase = format_phrase(
                random.choice(APP_COUNT_PHRASES), app=app_key, n=count)
        if phrase is None:
            phrases_list = APP_PHRASES.get(app_key)
            if phrases_list:
                phrase = t(random.choice(phrases_list))

        if phrase and not self.character.state.startswith("reaction_"):
            self.character.current_message = phrase
            # Show speech directly (character.events gets wiped each tick)
            if self._speech_fn:
                self._speech_fn(phrase)

        # Trigger activity
        is_coding = any(app in app_key for app in CODING_APPS)
        is_music = any(app in app_key for app in MUSIC_APPS)

        if is_coding:
            self.character.trigger_activity("working")
        elif is_music:
            self.character.trigger_activity("music")
