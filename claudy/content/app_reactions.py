"""How Claudy reacts when the user launches an app.

Apps are grouped into categories that share phrases (and possibly an
activity Claudy mirrors). Each backend identifies apps its own way — macOS
by bundle ID, Linux by process name — and maps them to an `App` here.
"""

from dataclasses import dataclass, field

CATEGORY_PHRASES = {
    "browser": [
        "о, опять сидим в Интернете?", "что гуглим?",
        "интернет! бесконечный...",
    ],
    "terminal": [
        "хакерское время!", "терминал? кодим!",
        "sudo краб!", "о, командная строка!",
    ],
    "editor": [
        "кодим? кодим.", "время писать код!", "баги не ждут!",
    ],
    "music": [
        "о, музыка! 🎵", "что слушаем?",
        "♪ ля-ля-ля ♪", "потанцуем?", "хороший вкус!",
    ],
    "messenger": [
        "кто-то написал?", "сплетни? 👀", "кому отвечаем?",
    ],
    "files": [
        "ищем что-то?", "где же этот файл...",
        "столько папок!", "порядок наведём?",
    ],
    "photos": [
        "о, фоточки!", "красивое!", "а это кто? 👀", "📸!",
    ],
    "claude": [
        "о, это же я! ну, почти...", ":3",
        "привет, другая я!", "мы похожи!",
    ],
    "writing": [
        "пишем роман?", "вдохновение пришло?",
        "слова, слова, слова...", "творим!",
    ],
}

# Activities Claudy mirrors when the user opens an app of this category.
CATEGORY_ACTIVITY = {
    "terminal": "working",
    "editor": "working",
    "music": "music",
}


@dataclass(frozen=True)
class App:
    category: str
    extra_phrases: list = field(default_factory=list)

    @property
    def phrases(self):
        return CATEGORY_PHRASES[self.category] + self.extra_phrases

    @property
    def activity(self):
        return CATEGORY_ACTIVITY.get(self.category)


# macOS apps by bundle identifier
MACOS_APPS = {
    "com.apple.Safari": App("browser", ["Safari? ну ладно..."]),
    "com.vivaldi.Vivaldi": App("browser", ["опять мемы?"]),
    "com.google.Chrome": App("browser", ["Chrome съел всю память!"]),
    "org.mozilla.firefox": App("browser", ["Firefox! олдскул"]),
    "company.thebrowser.Browser": App("browser", ["Arc! стильно"]),
    "com.googlecode.iterm2": App("terminal"),
    "com.apple.Terminal": App("terminal"),
    "dev.warp.Warp-Stable": App("terminal", ["о, Warp! красиво"]),
    "com.microsoft.VSCode": App("editor", ["VS Code!", "а юнит-тесты?"]),
    "com.sublimetext.4": App("editor", ["Sublime!"]),
    "com.sublimetext.3": App("editor", ["Sublime!"]),
    "com.github.atom": App("editor"),
    "com.jetbrains.intellij": App("editor"),
    "com.jetbrains.pycharm": App("editor", ["PyCharm!"]),
    "com.spotify.client": App("music"),
    "com.apple.Music": App("music"),
    "ru.keepcoder.Telegram": App("messenger", ["Telegram!"]),
    "com.tdesktop.Telegram": App("messenger", ["Telegram!"]),
    "com.apple.finder": App("files"),
    "com.apple.Photos": App("photos"),
    "com.anthropic.claudefordesktop": App("claude"),
    "com.microsoft.Word": App("writing"),
    "abnerworks.Typora": App("writing", ["markdown! красиво"]),
    "com.apple.iWork.Pages": App("writing"),
    "net.ia.iaWriter": App("writing", ["минимализм! нравится"]),
}

# Linux apps by process-name fragment (matched as a substring of the
# lowercase process name; the first match in this order wins).
LINUX_APPS = {
    "firefox": App("browser", ["Firefox! олдскул"]),
    "chrome": App("browser", ["Chrome съел всю память!"]),
    "chromium": App("browser", ["Chrome съел всю память!"]),
    "vivaldi": App("browser", ["опять мемы?"]),
    "gnome-terminal": App("terminal"),
    "alacritty": App("terminal"),
    "kitty": App("terminal", ["о, Kitty! красиво"]),
    "tilix": App("terminal"),
    "terminator": App("terminal"),
    "warp-terminal": App("terminal", ["о, Warp! красиво"]),
    "xterm": App("terminal"),
    "sublime_text": App("editor", ["Sublime!"]),
    "pycharm": App("editor", ["PyCharm!"]),
    "webstorm": App("editor"),
    "clion": App("editor"),
    "codium": App("editor", ["VS Code!", "а юнит-тесты?"]),
    "code": App("editor", ["VS Code!", "а юнит-тесты?"]),
    "spotify": App("music"),
    "rhythmbox": App("music"),
    "lollypop": App("music"),
    "gnome-music": App("music"),
    "telegram": App("messenger", ["Telegram!"]),
    "nautilus": App("files"),
    "thunar": App("files"),
    "claude": App("claude"),
    "gedit": App("writing"),
    "libreoffice": App("writing"),
    "eog": App("photos"),
}


def match_linux_process(proc_name):
    """Return the LINUX_APPS key matching a process name, or None."""
    proc_name = proc_name.lower()
    for key in LINUX_APPS:
        if key in proc_name:
            return key
    return None
