"""Settings persistence and UI for Claudy."""

import json
import os
import AppKit
import objc
from phrases import set_language

SETTINGS_DIR = os.path.expanduser("~/.claudy")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULTS = {
    "terminal": "Terminal",
    "schedule": "owl",
    "language": "en",
    "speech_interval": "1m",
}

TERMINAL_OPTIONS = ["Terminal", "iTerm2", "Warp"]
SCHEDULE_OPTIONS = [("owl", "Сова / Night Owl"), ("lark", "Жаворонок / Early Bird")]
LANGUAGE_OPTIONS = [("ru", "Русский"), ("en", "English")]
SPEECH_OPTIONS = [
    ("10s", "Часто / Often (10s)"),
    ("1m", "Обычно / Normal (1 min)"),
    ("10m", "Редко / Rarely (10 min)"),
    ("30m", "Оч. редко / Very rarely (30 min)"),
    ("1h", "Почти никогда / Almost never (1 hr)"),
]

# Cooldown ranges in ms for each speech interval
SPEECH_COOLDOWNS = {
    "10s": (8000, 12000),
    "1m": (45000, 75000),
    "10m": (500000, 700000),
    "30m": (1500000, 2100000),
    "1h": (3000000, 4200000),
}


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


class SettingsWindow(AppKit.NSObject):
    """A simple settings panel."""

    def init(self):
        self = objc.super(SettingsWindow, self).init()
        if self is None:
            return None
        self.window = None
        self.settings = Settings.shared()
        self.terminal_popup = None
        self.schedule_popup = None
        self.lang_popup = None
        self.speech_popup = None
        return self

    def show(self):
        if self.window and self.window.isVisible():
            self.window.makeKeyAndOrderFront_(None)
            return

        w, h = 320, 310
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((200, 200), (w, h)),
            AppKit.NSWindowStyleMaskTitled
            | AppKit.NSWindowStyleMaskClosable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setReleasedWhenClosed_(False)
        self.window.setTitle_("Claudy — Settings")
        self.window.center()

        content = self.window.contentView()
        y = h - 50

        # Terminal picker
        self._add_label(content, "Open Claude Code in:", 20, y)
        y -= 28
        self.terminal_popup = self._add_popup(
            content, TERMINAL_OPTIONS, 20, y, 270)
        idx = TERMINAL_OPTIONS.index(self.settings.terminal) \
            if self.settings.terminal in TERMINAL_OPTIONS else 0
        self.terminal_popup.selectItemAtIndex_(idx)
        y -= 40

        # Schedule picker
        self._add_label(content, "Schedule mode:", 20, y)
        y -= 28
        schedule_titles = [title for _, title in SCHEDULE_OPTIONS]
        self.schedule_popup = self._add_popup(
            content, schedule_titles, 20, y, 270)
        schedule_keys = [key for key, _ in SCHEDULE_OPTIONS]
        idx = schedule_keys.index(self.settings.schedule) \
            if self.settings.schedule in schedule_keys else 0
        self.schedule_popup.selectItemAtIndex_(idx)
        y -= 40

        # Language picker
        self._add_label(content, "Language / Язык:", 20, y)
        y -= 28
        lang_titles = [title for _, title in LANGUAGE_OPTIONS]
        self.lang_popup = self._add_popup(
            content, lang_titles, 20, y, 270)
        lang_keys = [key for key, _ in LANGUAGE_OPTIONS]
        idx = lang_keys.index(self.settings.language) \
            if self.settings.language in lang_keys else 0
        self.lang_popup.selectItemAtIndex_(idx)
        y -= 40

        # Speech frequency picker
        self._add_label(content, "Speech frequency / Частота фраз:", 20, y)
        y -= 28
        speech_titles = [title for _, title in SPEECH_OPTIONS]
        self.speech_popup = self._add_popup(
            content, speech_titles, 20, y, 270)
        speech_keys = [key for key, _ in SPEECH_OPTIONS]
        idx = speech_keys.index(self.settings.speech_interval) \
            if self.settings.speech_interval in speech_keys else 1
        self.speech_popup.selectItemAtIndex_(idx)

        # Save button
        save_btn = AppKit.NSButton.alloc().initWithFrame_(((110, 12), (100, 32)))
        save_btn.setTitle_("Save")
        save_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        save_btn.setTarget_(self)
        save_btn.setAction_("saveSettings:")
        content.addSubview_(save_btn)

        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)

    def saveSettings_(self, sender):
        # Terminal
        self.settings.terminal = TERMINAL_OPTIONS[
            self.terminal_popup.indexOfSelectedItem()]

        # Schedule
        schedule_keys = [key for key, _ in SCHEDULE_OPTIONS]
        self.settings.schedule = schedule_keys[
            self.schedule_popup.indexOfSelectedItem()]

        # Language
        lang_keys = [key for key, _ in LANGUAGE_OPTIONS]
        self.settings.language = lang_keys[
            self.lang_popup.indexOfSelectedItem()]

        # Speech frequency
        speech_keys = [key for key, _ in SPEECH_OPTIONS]
        self.settings.speech_interval = speech_keys[
            self.speech_popup.indexOfSelectedItem()]

        self.settings.save()
        self.window.close()

    def _add_label(self, parent, text, x, y):
        label = AppKit.NSTextField.alloc().initWithFrame_(((x, y), (270, 20)))
        label.setStringValue_(text)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setBordered_(False)
        label.setDrawsBackground_(False)
        label.setFont_(AppKit.NSFont.systemFontOfSize_(13))
        parent.addSubview_(label)
        return label

    def _add_popup(self, parent, items, x, y, width):
        popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            ((x, y), (width, 26)), False)
        for item in items:
            popup.addItemWithTitle_(item)
        parent.addSubview_(popup)
        return popup
