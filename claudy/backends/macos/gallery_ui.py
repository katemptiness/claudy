"""macOS gallery window: the paintings Claudy has given (AppKit UI).

What to show comes from core.gallery; this only lays it out: a grid of the
paintings, the newest first, each under its title, and below it the story
of whichever one is picked.
"""

import math

import AppKit
import objc

from claudy.backends.macos.canvas import make_image
from claudy.backends.macos.gifts_ui import _FlippedView, _make_label
from claudy.content.ui_text import gallery_header, label
from claudy.core import gallery
from claudy.core.memory import Memory
from claudy.core.settings import Settings
from claudy.render import art
from claudy.render.art import PixelImage

W = 480
MARGIN = 20
COLUMNS = 4
CELL_W = (W - 2 * MARGIN) // COLUMNS
FRAME = 70          # a painting's side in the window: twice its size on the Dock
BUTTON = FRAME + 8
TITLE_H = 30
CELL_H = BUTTON + 4 + TITLE_H + 10
STORY_H = 150


def _painting_image(item):
    """The painting as an NSImage FRAME points wide, drawn at twice that in
    pixels so it stays crisp on a Retina screen."""
    pixels = art.build(art.item_key(item))
    columns = len(pixels.rows[0])
    big = PixelImage(pixels.rows, 2 * FRAME // columns)
    return AppKit.NSImage.alloc().initWithCGImage_size_(
        make_image(big), (FRAME, FRAME))


class GalleryWindow(AppKit.NSObject):
    """An AppKit window showing the paintings in the user's gallery."""

    def init(self):
        self = objc.super(GalleryWindow, self).init()
        if self is None:
            return None
        self.window = None
        self._paintings = []
        self._highlight = None
        self._cells = []        # (x, y) of each painting's button
        self._story = None      # the NSTextView the picked story goes in
        return self

    def show(self):
        if self.window and self.window.isVisible():
            # Bring it forward with focus, not just to the top of an app
            # that isn't active
            self.window.makeKeyAndOrderFront_(None)
            AppKit.NSApp.activateIgnoringOtherApps_(True)
            return

        entries = Memory.shared().get_gallery()
        self._paintings = gallery.paintings(
            entries, name=Settings.shared().user_name or "")

        rows = math.ceil(len(self._paintings) / COLUMNS)
        grid_top = 60
        story_top = grid_top + rows * CELL_H + 6
        h = story_top + STORY_H + MARGIN if self._paintings else 150

        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((200, 200), (W, h)),
            AppKit.NSWindowStyleMaskTitled | AppKit.NSWindowStyleMaskClosable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setReleasedWhenClosed_(False)
        self.window.setTitle_(label("gallery_title"))
        self.window.center()

        content = _FlippedView.alloc().initWithFrame_(((0, 0), (W, h)))
        content.addSubview_(_make_label(
            gallery_header(gallery.copies_given(entries)),
            MARGIN - 4, 16, W - 2 * MARGIN, bold=True, size=16))
        sep = AppKit.NSBox.alloc().initWithFrame_(((MARGIN, 48),
                                                  (W - 2 * MARGIN, 1)))
        sep.setBoxType_(AppKit.NSBoxSeparator)
        content.addSubview_(sep)

        if not self._paintings:
            empty = _make_label(label("no_paintings"), MARGIN - 4, 70,
                                W - 2 * MARGIN, size=13, alpha=0.5)
            empty.setFrameSize_((W - 2 * MARGIN, 40))
            empty.cell().setWraps_(True)
            content.addSubview_(empty)
        else:
            self._add_grid(content, grid_top)
            self._add_story(content, story_top)
            self._select_painting(0)

        self.window.setContentView_(content)
        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)

    def _add_grid(self, content, top):
        # Behind the picked painting, like a spotlight on the wall
        self._highlight = AppKit.NSBox.alloc().initWithFrame_(
            ((0, 0), (BUTTON + 8, BUTTON + 8)))
        self._highlight.setBoxType_(AppKit.NSBoxCustom)
        self._highlight.setBorderWidth_(0)
        self._highlight.setCornerRadius_(10)
        self._highlight.setFillColor_(
            AppKit.NSColor.controlAccentColor().colorWithAlphaComponent_(0.18))
        content.addSubview_(self._highlight)

        self._cells = []
        for i, painting in enumerate(self._paintings):
            col, row = i % COLUMNS, i // COLUMNS
            x = MARGIN + col * CELL_W + (CELL_W - BUTTON) // 2
            y = top + row * CELL_H
            self._cells.append((x, y))

            button = AppKit.NSButton.alloc().initWithFrame_(
                ((x, y), (BUTTON, BUTTON)))
            button.setBordered_(False)
            button.setImage_(_painting_image(painting.item))
            button.setImagePosition_(AppKit.NSImageOnly)
            button.setImageScaling_(AppKit.NSImageScaleNone)
            button.setToolTip_(painting.title)
            button.setTag_(i)
            button.setTarget_(self)
            button.setAction_("pictureClicked:")
            content.addSubview_(button)

            title = painting.title
            if painting.count > 1:
                title += f"  ×{painting.count}"
            caption = _make_label(title, MARGIN + col * CELL_W + 3,
                                  y + BUTTON + 4, CELL_W - 6, size=11)
            caption.setFrameSize_((CELL_W - 6, TITLE_H))
            caption.setAlignment_(AppKit.NSTextAlignmentCenter)
            caption.cell().setWraps_(True)
            content.addSubview_(caption)

    def _add_story(self, content, top):
        sep = AppKit.NSBox.alloc().initWithFrame_(((MARGIN, top),
                                                  (W - 2 * MARGIN, 1)))
        sep.setBoxType_(AppKit.NSBoxSeparator)
        content.addSubview_(sep)

        frame = ((MARGIN - 4, top + 8), (W - 2 * MARGIN + 8, STORY_H - 8))
        scroll = AppKit.NSScrollView.alloc().initWithFrame_(frame)
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(True)
        scroll.setDrawsBackground_(False)
        self._story = AppKit.NSTextView.alloc().initWithFrame_(
            ((0, 0), frame[1]))
        # The usual setup for text that grows down inside a scroll view
        self._story.setMinSize_((0, 0))
        self._story.setMaxSize_((frame[1][0], 1e7))
        self._story.setVerticallyResizable_(True)
        self._story.setHorizontallyResizable_(False)
        self._story.setAutoresizingMask_(AppKit.NSViewWidthSizable)
        self._story.textContainer().setContainerSize_((frame[1][0], 1e7))
        self._story.textContainer().setWidthTracksTextView_(True)
        self._story.setEditable_(False)
        self._story.setDrawsBackground_(False)
        self._story.setTextContainerInset_((4, 4))
        scroll.setDocumentView_(self._story)
        content.addSubview_(scroll)

    def pictureClicked_(self, sender):
        self._select_painting(sender.tag())

    def _select_painting(self, index):
        x, y = self._cells[index]
        self._highlight.setFrameOrigin_((x - 4, y - 4))
        self._story.textStorage().setAttributedString_(
            _story_text(self._paintings[index]))
        self._story.scrollRangeToVisible_((0, 0))


def _story_text(painting):
    """The picked painting's title, then each copy's date and story."""
    def part(text, font, color):
        return AppKit.NSAttributedString.alloc().initWithString_attributes_(
            text, {AppKit.NSFontAttributeName: font,
                   AppKit.NSForegroundColorAttributeName: color})

    text = AppKit.NSMutableAttributedString.alloc().init()
    text.appendAttributedString_(part(
        painting.title + "\n", AppKit.NSFont.boldSystemFontOfSize_(14),
        AppKit.NSColor.labelColor()))
    for copy in painting.copies:
        text.appendAttributedString_(part(
            "\n" + copy.date + "\n", AppKit.NSFont.systemFontOfSize_(11),
            AppKit.NSColor.secondaryLabelColor()))
        text.appendAttributedString_(part(
            copy.story + "\n", AppKit.NSFont.systemFontOfSize_(13),
            AppKit.NSColor.labelColor()))
    return text
