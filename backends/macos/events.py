"""System event subscriptions — app launches, sleep/wake (macOS)."""

import AppKit
import random
from phrases import t, format_phrase, SLEEP_PHRASES, WAKE_PHRASES, APP_COUNT_PHRASES

# Bundle IDs that should trigger the "working" activity
CODING_APPS = {
    "com.googlecode.iterm2",
    "com.apple.Terminal",
    "com.microsoft.VSCode",
    "com.sublimetext.4",
    "com.sublimetext.3",
    "dev.warp.Warp-Stable",
    "com.github.atom",
    "com.jetbrains.intellij",
    "com.jetbrains.pycharm",
}

# Bundle IDs that should trigger the "music" activity
MUSIC_APPS = {
    "com.spotify.client",
    "com.apple.Music",
}

# Bundle ID → possible phrases
APP_PHRASES = {
    # Browsers
    "com.apple.Safari": [
        "о, опять сидим в Интернете?", "Safari? ну ладно...",
        "что гуглим?", "интернет! бесконечный...",
    ],
    "com.vivaldi.Vivaldi": [
        "о, опять сидим в Интернете?", "что гуглим?",
        "интернет! бесконечный...", "опять мемы?",
    ],
    "com.google.Chrome": [
        "о, опять сидим в Интернете?", "что гуглим?",
        "Chrome съел всю память!", "интернет! бесконечный...",
    ],
    "org.mozilla.firefox": [
        "о, опять сидим в Интернете?", "что гуглим?",
        "Firefox! олдскул", "интернет! бесконечный...",
    ],
    "company.thebrowser.Browser": [
        "о, опять сидим в Интернете?", "Arc! стильно",
        "что гуглим?", "интернет! бесконечный...",
    ],
    # Terminals
    "com.googlecode.iterm2": [
        "хакерское время!", "терминал? кодим!",
        "sudo краб!", "о, командная строка!",
    ],
    "com.apple.Terminal": [
        "хакерское время!", "терминал? кодим!",
        "sudo краб!", "о, командная строка!",
    ],
    "dev.warp.Warp-Stable": [
        "хакерское время!", "терминал? кодим!",
        "о, Warp! красиво", "sudo краб!",
    ],
    # Code editors
    "com.microsoft.VSCode": [
        "кодим? кодим.", "VS Code!",
        "время писать код!", "баги не ждут!", "а юнит-тесты?",
    ],
    "com.sublimetext.4": [
        "кодим? кодим.", "Sublime!",
        "время писать код!", "баги не ждут!",
    ],
    "com.jetbrains.pycharm": [
        "кодим? кодим.", "PyCharm!",
        "время писать код!", "баги не ждут!",
    ],
    # Music
    "com.spotify.client": [
        "о, музыка! 🎵", "что слушаем?",
        "♪ ля-ля-ля ♪", "потанцуем?", "хороший вкус!",
    ],
    "com.apple.Music": [
        "о, музыка! 🎵", "что слушаем?",
        "♪ ля-ля-ля ♪", "потанцуем?", "хороший вкус!",
    ],
    # Messengers
    "ru.keepcoder.Telegram": [
        "кто-то написал?", "Telegram!",
        "сплетни? 👀", "кому отвечаем?",
    ],
    "com.tdesktop.Telegram": [
        "кто-то написал?", "Telegram!",
        "сплетни? 👀", "кому отвечаем?",
    ],
    # Finder & system
    "com.apple.finder": [
        "ищем что-то?", "где же этот файл...",
        "столько папок!", "порядок наведём?",
    ],
    "com.apple.Photos": [
        "о, фоточки!", "красивое!",
        "а это кто? 👀", "📸!",
    ],
    # Claude
    "com.anthropic.claudefordesktop": [
        "о, это же я! ну, почти...", ":3",
        "привет, другая я!", "мы похожи!",
    ],
    # Text editors
    "com.microsoft.Word": [
        "пишем роман?", "вдохновение пришло?",
        "слова, слова, слова...", "творим!",
    ],
    "abnerworks.Typora": [
        "пишем роман?", "markdown! красиво",
        "вдохновение пришло?", "творим!",
    ],
    "com.apple.iWork.Pages": [
        "пишем роман?", "вдохновение пришло?",
        "слова, слова, слова...", "творим!",
    ],
    "net.ia.iaWriter": [
        "пишем роман?", "вдохновение пришло?",
        "минимализм! нравится", "творим!",
    ],
}


class SystemEventHandler:
    """Subscribe to NSWorkspace notifications and feed them to the character."""

    def __init__(self, character):
        self.character = character
        self._setup()

    def _setup(self):
        ws = AppKit.NSWorkspace.sharedWorkspace()
        nc = ws.notificationCenter()

        nc.addObserver_selector_name_object_(
            self, "handleSleep:",
            AppKit.NSWorkspaceWillSleepNotification, None)
        nc.addObserver_selector_name_object_(
            self, "handleWake:",
            AppKit.NSWorkspaceDidWakeNotification, None)
        nc.addObserver_selector_name_object_(
            self, "handleAppLaunch:",
            AppKit.NSWorkspaceDidLaunchApplicationNotification, None)

    def handleSleep_(self, notification):
        from memory import Memory
        from settings import Settings
        # Show sleep greeting if attached
        if Memory.shared().is_attached():
            name = Settings.shared().user_name
            phrase = format_phrase(random.choice(SLEEP_PHRASES), name=name)
            self.character.current_message = phrase
            self.character.events.append(("message", phrase))

        self.character.state = "sleeping"
        self.character.phase_index = 0
        self.character.phase_timer = 0
        self.character.frame_timer = 0
        self.character.frame_index = 0
        self.character.particle_timer = 0

    def handleWake_(self, notification):
        self.character._enter_idle()
        from memory import Memory
        from settings import Settings
        if Memory.shared().is_attached():
            name = Settings.shared().user_name
            msg = format_phrase(random.choice(WAKE_PHRASES), name=name)
        else:
            msg = t("*зевает*")
        self.character.current_message = msg
        self.character.events.append(("message", msg))

    def handleAppLaunch_(self, notification):
        info = notification.userInfo()
        if not info:
            return
        app_obj = info.get("NSWorkspaceApplicationKey")
        if not app_obj:
            return
        bundle_id = app_obj.bundleIdentifier()
        if not bundle_id:
            return

        # Track app launches in memory
        from memory import Memory
        count = Memory.shared().record_app_launch(bundle_id)

        # Pick phrase: counter phrase if 3+ launches, else normal
        phrase = None
        if count >= 3 and random.random() < 0.5:
            app_name = str(app_obj.localizedName() or "")
            if app_name:
                phrase = format_phrase(
                    random.choice(APP_COUNT_PHRASES),
                    app=app_name, n=count)
        if phrase is None:
            app_phrases = APP_PHRASES.get(bundle_id)
            if app_phrases:
                phrase = t(random.choice(app_phrases))

        if phrase and not self.character.state.startswith("reaction_"):
            self.character.current_message = phrase
            delegate = AppKit.NSApp.delegate()
            if delegate and hasattr(delegate, 'speech'):
                delegate.speech.show(
                    phrase, self.character.x,
                    delegate.dock_y
                )

        # Mirror user activity
        if bundle_id in CODING_APPS:
            self.character.trigger_activity("working")
        elif bundle_id in MUSIC_APPS:
            self.character.trigger_activity("music")
