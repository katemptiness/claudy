"""macOS settings window (AppKit UI)."""

import AppKit
import objc
from settings import (
    Settings, TERMINAL_OPTIONS, LANGUAGE_OPTIONS,
    _SCHEDULE_OPTIONS, _SPEECH_OPTIONS,
    _GIFT_DURATION_OPTIONS, _GIFT_LIMIT_OPTIONS,
    _loc, _l,
)


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
        self.name_field = None
        self.speech_popup = None
        self.gift_dur_popup = None
        self.gift_lim_popup = None
        self.dev_check = None
        return self

    def show(self):
        if self.window and self.window.isVisible():
            self.window.makeKeyAndOrderFront_(None)
            return

        lang = self.settings.language
        w, h = 320, 580
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((200, 200), (w, h)),
            AppKit.NSWindowStyleMaskTitled
            | AppKit.NSWindowStyleMaskClosable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setReleasedWhenClosed_(False)
        self.window.setTitle_(_l("title", lang))
        self.window.center()

        content = self.window.contentView()
        y = h - 50

        # Terminal
        self._add_label(content, _l("terminal", lang), 20, y)
        y -= 28
        self.terminal_popup = self._add_popup(
            content, TERMINAL_OPTIONS, 20, y, 270)
        idx = TERMINAL_OPTIONS.index(self.settings.terminal) \
            if self.settings.terminal in TERMINAL_OPTIONS else 0
        self.terminal_popup.selectItemAtIndex_(idx)
        y -= 40

        # Schedule
        self._add_label(content, _l("schedule", lang), 20, y)
        y -= 28
        sched = _loc(_SCHEDULE_OPTIONS, lang)
        self.schedule_popup = self._add_popup(
            content, [t for _, t in sched], 20, y, 270)
        sched_keys = [k for k, _ in sched]
        idx = sched_keys.index(self.settings.schedule) \
            if self.settings.schedule in sched_keys else 0
        self.schedule_popup.selectItemAtIndex_(idx)
        y -= 40

        # Language (always bilingual so user can find it)
        self._add_label(content, _l("language", lang), 20, y)
        y -= 28
        lang_titles = [title for _, title in LANGUAGE_OPTIONS]
        self.lang_popup = self._add_popup(
            content, lang_titles, 20, y, 270)
        lang_keys = [key for key, _ in LANGUAGE_OPTIONS]
        idx = lang_keys.index(self.settings.language) \
            if self.settings.language in lang_keys else 0
        self.lang_popup.selectItemAtIndex_(idx)
        y -= 40

        # Name
        self._add_label(content, _l("name", lang), 20, y)
        y -= 28
        self.name_field = AppKit.NSTextField.alloc().initWithFrame_(
            ((20, y), (270, 24)))
        self.name_field.setFont_(AppKit.NSFont.systemFontOfSize_(13))
        self.name_field.setStringValue_(self.settings.user_name or "")
        content.addSubview_(self.name_field)
        y -= 40

        # Speech frequency
        self._add_label(content, _l("speech", lang), 20, y)
        y -= 28
        speech = _loc(_SPEECH_OPTIONS, lang)
        self.speech_popup = self._add_popup(
            content, [t for _, t in speech], 20, y, 270)
        speech_keys = [k for k, _ in speech]
        idx = speech_keys.index(self.settings.speech_interval) \
            if self.settings.speech_interval in speech_keys else 1
        self.speech_popup.selectItemAtIndex_(idx)
        y -= 40

        # Gift duration
        self._add_label(content, _l("gift_dur", lang), 20, y)
        y -= 28
        gdur = _loc(_GIFT_DURATION_OPTIONS, lang)
        self.gift_dur_popup = self._add_popup(
            content, [t for _, t in gdur], 20, y, 270)
        gdur_keys = [k for k, _ in gdur]
        idx = gdur_keys.index(self.settings.gift_duration) \
            if self.settings.gift_duration in gdur_keys else 2
        self.gift_dur_popup.selectItemAtIndex_(idx)
        y -= 40

        # Gifts per day
        self._add_label(content, _l("gift_lim", lang), 20, y)
        y -= 28
        glim = _loc(_GIFT_LIMIT_OPTIONS, lang)
        self.gift_lim_popup = self._add_popup(
            content, [t for _, t in glim], 20, y, 270)
        glim_keys = [k for k, _ in glim]
        idx = glim_keys.index(self.settings.gift_limit) \
            if self.settings.gift_limit in glim_keys else 1
        self.gift_lim_popup.selectItemAtIndex_(idx)
        y -= 35

        # Dev mode
        self.dev_check = AppKit.NSButton.alloc().initWithFrame_(
            ((20, y), (270, 20)))
        self.dev_check.setButtonType_(AppKit.NSSwitchButton)
        self.dev_check.setTitle_(_l("dev", lang))
        self.dev_check.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        self.dev_check.setState_(
            AppKit.NSControlStateValueOn if self.settings.dev_mode
            else AppKit.NSControlStateValueOff)
        content.addSubview_(self.dev_check)

        # Save
        save_btn = AppKit.NSButton.alloc().initWithFrame_(((110, 12), (100, 32)))
        save_btn.setTitle_(_l("save", lang))
        save_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        save_btn.setTarget_(self)
        save_btn.setAction_("saveSettings:")
        content.addSubview_(save_btn)

        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)

    def saveSettings_(self, sender):
        self.settings.terminal = TERMINAL_OPTIONS[
            self.terminal_popup.indexOfSelectedItem()]

        sched_keys = [o[0] for o in _SCHEDULE_OPTIONS]
        self.settings.schedule = sched_keys[
            self.schedule_popup.indexOfSelectedItem()]

        lang_keys = [key for key, _ in LANGUAGE_OPTIONS]
        self.settings.language = lang_keys[
            self.lang_popup.indexOfSelectedItem()]

        self.settings.user_name = str(self.name_field.stringValue()).strip()

        speech_keys = [o[0] for o in _SPEECH_OPTIONS]
        self.settings.speech_interval = speech_keys[
            self.speech_popup.indexOfSelectedItem()]

        gdur_keys = [o[0] for o in _GIFT_DURATION_OPTIONS]
        self.settings.gift_duration = gdur_keys[
            self.gift_dur_popup.indexOfSelectedItem()]

        glim_keys = [o[0] for o in _GIFT_LIMIT_OPTIONS]
        self.settings.gift_limit = glim_keys[
            self.gift_lim_popup.indexOfSelectedItem()]

        self.settings.dev_mode = (
            self.dev_check.state() == AppKit.NSControlStateValueOn)

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
