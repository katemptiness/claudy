"""macOS settings window (AppKit UI)."""

import AppKit
import objc

from claudy.content.ui_text import (
    GIFT_COOLDOWN_OPTIONS, GIFT_DURATION_OPTIONS, GIFT_LIMIT_OPTIONS,
    LANGUAGE_OPTIONS, SCHEDULE_OPTIONS, SPEECH_OPTIONS, label, localized,
)
from claudy.core.settings import (
    DOCK_ICONS_MAX, DOCK_ICONS_MIN, TERMINAL_OPTIONS, Settings,
    VERTICAL_OFFSET_MAX, VERTICAL_OFFSET_MIN,
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
        self.gift_cd_popup = None
        self.height_slider = None
        self.height_value_label = None
        self.dock_icons_slider = None
        self.dock_icons_value_label = None
        self.dev_check = None
        self._orig_vertical_offset = None
        self._saved = False
        return self

    def show(self):
        if self.window and self.window.isVisible():
            self.window.makeKeyAndOrderFront_(None)
            return

        lang = self.settings.language
        # Remember the height so we can revert if the user closes without saving
        # (the slider previews live by mutating the shared settings).
        self._orig_vertical_offset = self.settings.vertical_offset
        self._saved = False
        w, h = 320, 800
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((200, 200), (w, h)),
            AppKit.NSWindowStyleMaskTitled
            | AppKit.NSWindowStyleMaskClosable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setReleasedWhenClosed_(False)
        self.window.setTitle_(label("title", lang))
        self.window.setDelegate_(self)
        self.window.center()

        content = self.window.contentView()
        y = h - 50

        # Terminal
        self._add_label(content, label("terminal", lang), 20, y)
        y -= 28
        self.terminal_popup = self._add_popup(
            content, TERMINAL_OPTIONS, 20, y, 270)
        idx = TERMINAL_OPTIONS.index(self.settings.terminal) \
            if self.settings.terminal in TERMINAL_OPTIONS else 0
        self.terminal_popup.selectItemAtIndex_(idx)
        y -= 40

        # Schedule
        self._add_label(content, label("schedule", lang), 20, y)
        y -= 28
        sched = localized(SCHEDULE_OPTIONS, lang)
        self.schedule_popup = self._add_popup(
            content, [t for _, t in sched], 20, y, 270)
        sched_keys = [k for k, _ in sched]
        idx = sched_keys.index(self.settings.schedule) \
            if self.settings.schedule in sched_keys else 0
        self.schedule_popup.selectItemAtIndex_(idx)
        y -= 40

        # Height above the Dock (slider previews live as you drag)
        self._add_label(content, label("height", lang), 20, y)
        self.height_value_label = self._add_value_label(
            content, self._format_height(self.settings.vertical_offset),
            190, y, 100)
        y -= 26
        self.height_slider = AppKit.NSSlider.alloc().initWithFrame_(
            ((20, y), (270, 22)))
        self.height_slider.setMinValue_(VERTICAL_OFFSET_MIN)
        self.height_slider.setMaxValue_(VERTICAL_OFFSET_MAX)
        self.height_slider.setDoubleValue_(self.settings.vertical_offset)
        self.height_slider.setContinuous_(True)
        self.height_slider.setTarget_(self)
        self.height_slider.setAction_("heightChanged:")
        content.addSubview_(self.height_slider)
        y -= 18
        self._add_hint(content, label("height_below", lang), 20, y, 80, left=True)
        self._add_hint(content, label("height_above", lang), 210, y, 80, left=False)
        y -= 34

        # Dock icons (estimates the Dock width so Claudy paces only across it)
        self._add_label(content, label("dock_icons", lang), 20, y)
        self.dock_icons_value_label = self._add_value_label(
            content, self._format_dock_icons(self.settings.dock_icons),
            190, y, 100)
        y -= 26
        self.dock_icons_slider = AppKit.NSSlider.alloc().initWithFrame_(
            ((20, y), (270, 22)))
        self.dock_icons_slider.setMinValue_(DOCK_ICONS_MIN)
        self.dock_icons_slider.setMaxValue_(DOCK_ICONS_MAX)
        self.dock_icons_slider.setDoubleValue_(self.settings.dock_icons)
        self.dock_icons_slider.setContinuous_(True)
        self.dock_icons_slider.setTarget_(self)
        self.dock_icons_slider.setAction_("dockIconsChanged:")
        content.addSubview_(self.dock_icons_slider)
        y -= 18
        self._add_hint(content, label("dock_icons_hint", lang), 20, y, 270, left=True)
        y -= 34

        # Language (always bilingual so user can find it)
        self._add_label(content, label("language", lang), 20, y)
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
        self._add_label(content, label("name", lang), 20, y)
        y -= 28
        self.name_field = AppKit.NSTextField.alloc().initWithFrame_(
            ((20, y), (270, 24)))
        self.name_field.setFont_(AppKit.NSFont.systemFontOfSize_(13))
        self.name_field.setStringValue_(self.settings.user_name or "")
        content.addSubview_(self.name_field)
        y -= 40

        # Speech frequency
        self._add_label(content, label("speech", lang), 20, y)
        y -= 28
        speech = localized(SPEECH_OPTIONS, lang)
        self.speech_popup = self._add_popup(
            content, [t for _, t in speech], 20, y, 270)
        speech_keys = [k for k, _ in speech]
        idx = speech_keys.index(self.settings.speech_interval) \
            if self.settings.speech_interval in speech_keys else 1
        self.speech_popup.selectItemAtIndex_(idx)
        y -= 40

        # Gift duration
        self._add_label(content, label("gift_dur", lang), 20, y)
        y -= 28
        gdur = localized(GIFT_DURATION_OPTIONS, lang)
        self.gift_dur_popup = self._add_popup(
            content, [t for _, t in gdur], 20, y, 270)
        gdur_keys = [k for k, _ in gdur]
        idx = gdur_keys.index(self.settings.gift_duration) \
            if self.settings.gift_duration in gdur_keys else 2
        self.gift_dur_popup.selectItemAtIndex_(idx)
        y -= 40

        # Gifts per day
        self._add_label(content, label("gift_lim", lang), 20, y)
        y -= 28
        glim = localized(GIFT_LIMIT_OPTIONS, lang)
        self.gift_lim_popup = self._add_popup(
            content, [t for _, t in glim], 20, y, 270)
        glim_keys = [k for k, _ in glim]
        idx = glim_keys.index(self.settings.gift_limit) \
            if self.settings.gift_limit in glim_keys else 1
        self.gift_lim_popup.selectItemAtIndex_(idx)
        y -= 40

        # Gift cooldown
        self._add_label(content, label("gift_cd", lang), 20, y)
        y -= 28
        gcd = localized(GIFT_COOLDOWN_OPTIONS, lang)
        self.gift_cd_popup = self._add_popup(
            content, [t for _, t in gcd], 20, y, 270)
        gcd_keys = [k for k, _ in gcd]
        idx = gcd_keys.index(self.settings.gift_cooldown) \
            if self.settings.gift_cooldown in gcd_keys else 3
        self.gift_cd_popup.selectItemAtIndex_(idx)
        y -= 35

        # Dev mode
        self.dev_check = AppKit.NSButton.alloc().initWithFrame_(
            ((20, y), (270, 20)))
        self.dev_check.setButtonType_(AppKit.NSSwitchButton)
        self.dev_check.setTitle_(label("dev", lang))
        self.dev_check.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        self.dev_check.setState_(
            AppKit.NSControlStateValueOn if self.settings.dev_mode
            else AppKit.NSControlStateValueOff)
        content.addSubview_(self.dev_check)

        # Save
        save_btn = AppKit.NSButton.alloc().initWithFrame_(((110, 12), (100, 32)))
        save_btn.setTitle_(label("save", lang))
        save_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        save_btn.setTarget_(self)
        save_btn.setAction_("saveSettings:")
        content.addSubview_(save_btn)

        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)

    def saveSettings_(self, sender):
        self.settings.terminal = TERMINAL_OPTIONS[
            self.terminal_popup.indexOfSelectedItem()]

        sched_keys = [o[0] for o in SCHEDULE_OPTIONS]
        self.settings.schedule = sched_keys[
            self.schedule_popup.indexOfSelectedItem()]

        lang_keys = [key for key, _ in LANGUAGE_OPTIONS]
        self.settings.language = lang_keys[
            self.lang_popup.indexOfSelectedItem()]

        self.settings.user_name = str(self.name_field.stringValue()).strip()

        speech_keys = [o[0] for o in SPEECH_OPTIONS]
        self.settings.speech_interval = speech_keys[
            self.speech_popup.indexOfSelectedItem()]

        gdur_keys = [o[0] for o in GIFT_DURATION_OPTIONS]
        self.settings.gift_duration = gdur_keys[
            self.gift_dur_popup.indexOfSelectedItem()]

        glim_keys = [o[0] for o in GIFT_LIMIT_OPTIONS]
        self.settings.gift_limit = glim_keys[
            self.gift_lim_popup.indexOfSelectedItem()]

        gcd_keys = [o[0] for o in GIFT_COOLDOWN_OPTIONS]
        self.settings.gift_cooldown = gcd_keys[
            self.gift_cd_popup.indexOfSelectedItem()]

        self.settings.vertical_offset = self.height_slider.doubleValue()
        self.settings.dock_icons = self.dock_icons_slider.doubleValue()

        self.settings.dev_mode = (
            self.dev_check.state() == AppKit.NSControlStateValueOn)

        self._saved = True
        self.settings.save()
        self.window.close()

    def heightChanged_(self, sender):
        # Preview live by mutating the shared settings; the running crab reads
        # vertical_offset every tick, so it rises/lowers as the slider moves.
        self.settings.vertical_offset = sender.doubleValue()
        self.height_value_label.setStringValue_(
            self._format_height(self.settings.vertical_offset))

    def windowWillClose_(self, notification):
        # Revert the live preview if the user closed without saving.
        if not self._saved and self._orig_vertical_offset is not None:
            self.settings.vertical_offset = self._orig_vertical_offset

    def _format_height(self, value):
        lang = self.settings.language
        v = int(round(value))
        if v == 0:
            return label("height_dock", lang)
        return "%+d %s" % (v, label("height_unit", lang))

    def dockIconsChanged_(self, sender):
        # Just update the readout; the count is applied on Save (no live preview
        # needed since it has no instant visual effect on the crab).
        self.dock_icons_value_label.setStringValue_(
            self._format_dock_icons(sender.doubleValue()))

    def _format_dock_icons(self, value):
        return str(int(round(value)))

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

    def _add_value_label(self, parent, text, x, y, width):
        label = AppKit.NSTextField.alloc().initWithFrame_(((x, y), (width, 20)))
        label.setStringValue_(text)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setBordered_(False)
        label.setDrawsBackground_(False)
        label.setAlignment_(AppKit.NSTextAlignmentRight)
        label.setFont_(AppKit.NSFont.systemFontOfSize_(13))
        label.setTextColor_(AppKit.NSColor.secondaryLabelColor())
        parent.addSubview_(label)
        return label

    def _add_hint(self, parent, text, x, y, width, left=True):
        label = AppKit.NSTextField.alloc().initWithFrame_(((x, y), (width, 16)))
        label.setStringValue_(text)
        label.setEditable_(False)
        label.setSelectable_(False)
        label.setBordered_(False)
        label.setDrawsBackground_(False)
        label.setAlignment_(
            AppKit.NSTextAlignmentLeft if left else AppKit.NSTextAlignmentRight)
        label.setFont_(AppKit.NSFont.systemFontOfSize_(10))
        label.setTextColor_(AppKit.NSColor.tertiaryLabelColor())
        parent.addSubview_(label)
        return label

    def _add_popup(self, parent, items, x, y, width):
        popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            ((x, y), (width, 26)), False)
        for item in items:
            popup.addItemWithTitle_(item)
        parent.addSubview_(popup)
        return popup
