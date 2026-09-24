"""macOS gifts collection window (AppKit UI)."""

import AppKit
import objc

from claudy.content.gift_stories import get_story
from claudy.content.ui_text import (
    format_date, gift_type_name, gifts_header, label,
)
from claudy.core.memory import Memory
from claudy.core.settings import Settings


class GiftsWindow(AppKit.NSObject):
    """An AppKit window showing the user's gift collection."""

    def init(self):
        self = objc.super(GiftsWindow, self).init()
        if self is None:
            return None
        self.window = None
        return self

    def show(self):
        if self.window and self.window.isVisible():
            self.window.makeKeyAndOrderFront_(None)
            return

        gifts = Memory.shared().get_collected_gifts()
        user_name = Settings.shared().user_name or ""

        w = 360
        h = 460

        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((200, 200), (w, h)),
            AppKit.NSWindowStyleMaskTitled
            | AppKit.NSWindowStyleMaskClosable
            | AppKit.NSWindowStyleMaskResizable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setReleasedWhenClosed_(False)
        self.window.setTitle_(label("gifts_title"))
        self.window.setMinSize_((320, 300))
        self.window.center()

        # --- Scroll view with flipped document ---
        scroll = AppKit.NSScrollView.alloc().initWithFrame_(
            ((0, 0), (w, h)))
        scroll.setHasVerticalScroller_(True)
        scroll.setHasHorizontalScroller_(False)
        scroll.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)

        doc = _FlippedView.alloc().initWithFrame_(((0, 0), (w, 0)))
        doc.setAutoresizingMask_(AppKit.NSViewWidthSizable)
        y = 16  # top padding (flipped coords: y goes downward)

        # Header: gift count
        header = _make_label(gifts_header(len(gifts)), 16, y, w - 32,
                             bold=True, size=16)
        doc.addSubview_(header)
        y += 32

        # Separator line
        sep = AppKit.NSBox.alloc().initWithFrame_(((16, y), (w - 32, 1)))
        sep.setBoxType_(AppKit.NSBoxSeparator)
        doc.addSubview_(sep)
        y += 12

        if not gifts:
            empty = _make_label(label("no_gifts"), 16, y + 20, w - 32,
                                size=13, alpha=0.5)
            doc.addSubview_(empty)
            y += 80
        else:
            for i, gift in enumerate(gifts):
                y = self._add_gift_row(doc, gift, user_name, y, w)
                if i < len(gifts) - 1:
                    sep = AppKit.NSBox.alloc().initWithFrame_(
                        ((20, y), (w - 40, 1)))
                    sep.setBoxType_(AppKit.NSBoxSeparator)
                    doc.addSubview_(sep)
                    y += 8

        y += 16  # bottom padding
        doc.setFrameSize_((w, max(y, h)))
        scroll.setDocumentView_(doc)
        self.window.setContentView_(scroll)
        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)

    def _add_gift_row(self, parent, gift, user_name, y, w):
        """Add a gift row to the document view. Returns new y position."""
        # Emoji
        emoji_label = _make_label(gift["emoji"], 16, y, 30, size=20)
        parent.addSubview_(emoji_label)

        # Type name
        type_label = _make_label(gift_type_name(gift["type"]), 48, y + 2, 150,
                                 bold=True, size=13)
        parent.addSubview_(type_label)

        # Date
        date_label = _make_label(format_date(gift["date"]), w - 120, y + 3, 100,
                                 size=11, alpha=0.5)
        date_label.setAlignment_(AppKit.NSTextAlignmentRight)
        parent.addSubview_(date_label)

        y += 28

        # Story text (wrapping)
        story_text = get_story(gift["type"], gift["story_id"], name=user_name)

        story_label = _make_label(story_text, 20, y, w - 44, size=12, alpha=0.7)
        # Calculate height needed for wrapping text
        text_storage = AppKit.NSTextStorage.alloc().initWithString_attributes_(
            story_text, {AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(12)})
        layout = AppKit.NSLayoutManager.alloc().init()
        text_container = AppKit.NSTextContainer.alloc().initWithContainerSize_(
            (w - 44, 10000))
        text_container.setLineFragmentPadding_(0)
        layout.addTextContainer_(text_container)
        text_storage.addLayoutManager_(layout)
        layout.glyphRangeForTextContainer_(text_container)
        text_rect = layout.usedRectForTextContainer_(text_container)
        text_h = max(18, int(text_rect.size.height) + 4)

        story_label.setFrame_(((20, y), (w - 44, text_h)))
        parent.addSubview_(story_label)

        y += text_h + 12
        return y


# --- Helpers ---

class _FlippedView(AppKit.NSView):
    """NSView subclass with flipped coordinates (origin at top-left)."""
    def isFlipped(self):
        return True


def _make_label(text, x, y, width, bold=False, size=13, alpha=1.0):
    """Create a non-editable text field label."""
    label = AppKit.NSTextField.alloc().initWithFrame_(((x, y), (width, 20)))
    label.setStringValue_(text)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setBordered_(False)
    label.setDrawsBackground_(False)
    if bold:
        label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(size))
    else:
        label.setFont_(AppKit.NSFont.systemFontOfSize_(size))
    if alpha < 1.0:
        label.setTextColor_(
            AppKit.NSColor.labelColor().colorWithAlphaComponent_(alpha))
    return label

