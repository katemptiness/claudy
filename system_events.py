"""System event subscriptions — app launches, sleep/wake, etc."""

import AppKit
import random
from phrases import t

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
        self.character.state = "sleeping"
        self.character.phase_index = 0
        self.character.phase_timer = 0
        self.character.frame_timer = 0
        self.character.frame_index = 0
        self.character.particle_timer = 0

    def handleWake_(self, notification):
        self.character._enter_idle()
        msg = t("*зевает*")
        self.character.current_message = msg
        self.character.events.append(("message", msg))

    def handleAppLaunch_(self, notification):
        info = notification.userInfo()
        if not info:
            return
        app = info.get("NSWorkspaceApplicationKey")
        if not app:
            return
        bundle_id = app.bundleIdentifier()
        if not bundle_id:
            return

        phrases = APP_PHRASES.get(bundle_id)
        if phrases:
            phrase = t(random.choice(phrases))
            if not self.character.state.startswith("reaction_"):
                self.character.current_message = phrase
                # Show speech bubble directly via app delegate
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
