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
    # What Claudy calls the app when he counts how often it was opened
    # today. Only Linux needs one: macOS names every app itself.
    name: str = ""

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

# Linux apps by process name (see match_linux_process)
LINUX_APPS = {
    "firefox": App("browser", ["Firefox! олдскул"], name="Firefox"),
    "chrome": App("browser", ["Chrome съел всю память!"], name="Chrome"),
    "chromium": App("browser", ["Chrome съел всю память!"], name="Chromium"),
    "vivaldi": App("browser", ["опять мемы?"], name="Vivaldi"),
    "gnome-terminal": App("terminal", name="GNOME Terminal"),
    "kgx": App("terminal", name="GNOME Console"),
    "ptyxis": App("terminal", name="Ptyxis"),
    "alacritty": App("terminal", name="Alacritty"),
    "kitty": App("terminal", ["о, Kitty! красиво"], name="Kitty"),
    "tilix": App("terminal", name="Tilix"),
    "terminator": App("terminal", name="Terminator"),
    "warp-terminal": App("terminal", ["о, Warp! красиво"], name="Warp"),
    "xterm": App("terminal", name="XTerm"),
    "sublime_text": App("editor", ["Sublime!"], name="Sublime Text"),
    "pycharm": App("editor", ["PyCharm!"], name="PyCharm"),
    "webstorm": App("editor", name="WebStorm"),
    "clion": App("editor", name="CLion"),
    "codium": App("editor", ["VS Code!", "а юнит-тесты?"], name="VSCodium"),
    "code": App("editor", ["VS Code!", "а юнит-тесты?"], name="VS Code"),
    "spotify": App("music", name="Spotify"),
    "rhythmbox": App("music", name="Rhythmbox"),
    "lollypop": App("music", name="Lollypop"),
    "gnome-music": App("music", name="GNOME Music"),
    "telegram": App("messenger", ["Telegram!"], name="Telegram"),
    "nautilus": App("files", name="Nautilus"),
    "thunar": App("files", name="Thunar"),
    "claude": App("claude", name="Claude"),
    "gedit": App("writing", name="gedit"),
    "gnome-text-editor": App("writing", name="GNOME Text Editor"),
    # LibreOffice runs as soffice.bin; "libreoffice" only starts it
    "soffice": App("writing", name="LibreOffice"),
    "eog": App("photos", name="Eye of GNOME"),
    "loupe": App("photos", name="Loupe"),
}

# ps shows only the first 15 characters of a process name
PROCESS_NAME_MAX = 15


def match_linux_process(proc_name):
    """Return the LINUX_APPS key matching a process name, or None.

    A key matches the whole name, or its first part before a "-" or ".":
    "gnome-terminal-server", "vivaldi-bin" and "soffice.bin" are those apps,
    but "chrome_crashpad", which every Electron app runs (Claude's desktop
    app among them), is not Chrome. A name cut off at PROCESS_NAME_MAX also
    matches the longer key it begins ("gnome-text-edit").
    """
    name = proc_name.lower()
    for key in LINUX_APPS:
        if name == key or name.startswith((key + "-", key + ".")):
            return key
        if len(name) == PROCESS_NAME_MAX and key.startswith(name):
            return key
    return None
