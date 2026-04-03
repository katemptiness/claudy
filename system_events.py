"""System event subscriptions — app launches, sleep/wake, etc."""

import AppKit
import random

# Bundle ID → possible phrases
APP_PHRASES = {
    "com.apple.Safari": ["о, опять сидим в Интернете?", "Safari? ну ладно..."],
    "com.vivaldi.Vivaldi": ["о, опять сидим в Интернете?"],
    "com.google.Chrome": ["о, опять сидим в Интернете?"],
    "com.googlecode.iterm2": ["хакерское время!", "терминал? кодим!"],
    "com.apple.Terminal": ["хакерское время!"],
    "com.microsoft.VSCode": ["кодим? кодим.", "VS Code!"],
    "com.sublimetext.4": ["кодим? кодим."],
    "com.spotify.client": ["о, музыка! 🎵", "что слушаем?"],
    "com.apple.Music": ["о, музыка! 🎵"],
    "ru.keepcoder.Telegram": ["кто-то написал?", "Telegram!"],
    "com.tdesktop.Telegram": ["кто-то написал?"],
    "com.apple.finder": ["ищем что-то?"],
    "com.apple.Photos": ["о, фоточки!"],
    "com.anthropic.claudefordesktop": ["о, это же я! ну, почти...", ":3"],
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
        self.character.current_message = "*зевает*"
        self.character.events.append(("message", "*зевает*"))

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
            phrase = random.choice(phrases)
            if not self.character.state.startswith("reaction_"):
                self.character.current_message = phrase
                # Show speech bubble directly via app delegate
                delegate = AppKit.NSApp.delegate()
                if delegate and hasattr(delegate, 'speech'):
                    delegate.speech.show(
                        phrase, self.character.x,
                        delegate.dock_y
                    )
