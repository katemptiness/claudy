# macOS first run — notes for Claude

A handoff note for whoever runs Claudy on a Mac for the first time after the
v3 overhaul (September 2026). Read this before touching the macOS backend.

## Why this matters

- The v3 overhaul (package layout, shared `Controller`, shared `Scene` /
  `Canvas` rendering, shading, new animations and particles) was built and
  tested on **Linux only**.
- The macOS backend (`claudy/backends/macos/`) was rewritten **without a Mac**.
  It was only exercised on Linux against stubbed AppKit/Quartz/objc modules.
  That catches Python-level mistakes (wrong names, wrong arguments, broken
  flows) but says nothing about how Cocoa actually behaves. Expect some fixes.
- The Linux build is verified and the user is happy with it. Treat the
  shared code (`claudy/core`, `claudy/content`, `claudy/render`) as correct:
  a macOS bug most likely lives in `claudy/backends/macos/`.
- The last commit that ran on a real Mac is `67c9f24`. It used the old flat
  layout and drew with CALayers (`git show 67c9f24:backends/macos/app.py`).
  It is handy for comparison when something Cocoa-specific misbehaves.

## Running and debugging

```bash
pip install pyobjc pyobjc-framework-Quartz
python3 -m unittest discover -s tests -t .   # pure Python; run these first
python3 app.py                                # from a terminal, to see tracebacks
tail -f ~/.claudy/error.log                   # errors inside the frame loop
```

- Errors raised inside the frame loop are caught and logged as `tick failed`
  in `~/.claudy/error.log`. Claudy keeps running but may freeze, so check
  the log whenever something looks stuck.
- **Settings → developer mode** adds an *Activities* submenu to the context
  menu. It starts any activity on demand and also offers a test gift.
- For screenshots, run `screencapture -x /tmp/claudy.png` and read the image.
  The terminal needs the Screen Recording permission for this; if it doesn't
  have it, ask the user to describe what they see.

## How the macOS backend works

- **Three windows.** All three are borderless, transparent and sit at the
  maximum window level. Each one's content is a `DrawingView` whose
  `drawRect_` lets the shared `Scene` paint through a `QuartzCanvas`.
  - **Crab window** (200×90): moves up when Claudy hops. `CrabView.hitTest_`
    makes only the 80×80 sprite clickable; the rest passes clicks through.
  - **Ground overlay** (200×300): ignores mouse events and stays on the
    Dock. It draws the shadow, the gift and the particles.
  - **Speech bubble** (`bubble.py`): ignores mouse events. It is resized
    to `Scene.bubble_layout()` and fades via `setAlphaValue_`.
  - The windows are split because a single tall interactive window blocked
    clicks on macOS.
- **Coordinates.** AppKit is y-up, and the views stay unflipped, so hit
  testing, tracking areas and mouse locations use AppKit's usual coordinates
  (`SPRITE_RECT` is y-up). The Scene paints with a top-left origin;
  `QuartzCanvas._flip` converts. `canvas.make_image` flips its bitmap so
  that row 0 of the art ends up on top.
- **Frame loop.** An `NSTimer` (`TICK_INTERVAL`) calls `AppDelegate.tick_`,
  which calls `MacApp.tick`. That runs `controller.tick(dt)`, moves the
  windows, calls `bubble.sync(...)` and sets `setNeedsDisplay_` on both
  views.
- **Input.** `CrabView` forwards events to the controller:
  - a single click waits 0.35 s to tell it apart from a double click;
  - hover, drag and drop are forwarded as they happen.
- **Context menu.** On right-click, `controller.menu()` returns `MenuItem`s
  and `MacApp.build_menu` turns them into an `NSMenu`. Each item's tag
  indexes `MenuTarget.actions`, and every item uses the `invoke:` selector.
- **System events.** `events.SystemEventObserver` subscribes to NSWorkspace
  sleep, wake and app-launch notifications and forwards them to the
  controller.
- **Settings and gifts windows** (`settings_ui.py`, `gifts_ui.py`): only
  their imports and label source (`content/ui_text.py`) changed since the
  Mac-tested version.

## Checklist

Go in order. Each item names the most likely culprit when it fails.

1. **Launch.** No traceback; Claudy stands on top of the Dock. If the
   height is off, check `get_dock_top_y`, `DOCK_Y_ADJUST` and
   Settings → height.
2. **Claudy looks like on Linux.**
   - What to expect: upright, crisp pixels (no blur), shading (a lighter
     top edge, a darker bottom row and legs, a white glint in the top-left
     of each eye).
   - Upside down or shifted: `QuartzCanvas._flip` or the flip in
     `make_image`.
   - Blurry on Retina: interpolation, or the layer's `contentsScale` or
     magnification filter.
   - Nothing drawn: `drawRect_` never runs (`setNeedsDisplay_`,
     `setWantsLayer_`), or `NSGraphicsContext.CGContext()` is missing.
3. **Ground overlay.** The pixel shadow sits under the feet and stays on the
   Dock while Claudy hops. It shrinks when Claudy is dragged up high.
   Particles float up from the right places and fade: hearts on a double
   click, dust on landing.
4. **Click-through.** Clicks on the transparent parts of all three windows
   reach the apps underneath. Only the sprite takes clicks.
5. **Input.**
   - Click: a happy hop.
   - Double click: love.
   - Hover: a wave.
   - Drag: surprise. Dropping from a height makes Claudy fall, bounce and
     kick up dust.
   - Right click: the menu opens, and every item and submenu works.
6. **Speech bubble.** It sits above Claudy, and its tail reaches down into
   the empty top of the crab window. The text sits inside the box and is
   not shifted by a line (watch `drawInRect_` in unflipped views). The text
   types out, the bubble fades in and out, and long text wraps.
7. **Activities** (through the developer menu).
   - Start with the wide sprites: reading and painting (32 columns),
     working (24), fishing, telescope, campfire, sandcastle, shells. Claudy
     must stay centered and nothing may be clipped.
   - After Claudy walks left, everything must mirror.
   - Juggling: the balls fly *behind* Claudy.
   - Summoning: a blue friend appears on the left.
8. **Gifts.** A test gift shows on the Dock as an emoji. Clicking it
   collects it, and the gifts window lists it.
9. **Settings.** Every control saves, the height slider moves Claudy live,
   and switching the language changes phrases and menus.
10. **System events.**
    - Launching Terminal or VS Code makes Claudy react.
    - When the Mac sleeps, Claudy falls asleep, and wakes up with it.
11. **Everywhere, cheaply.**
    - Claudy stays visible on other Spaces and over full-screen apps.
    - CPU in Activity Monitor stays low. Both views redraw at 60 FPS; if
      that turns out costly, redraw only when the view changes.

## PyObjC rules that bite

- **Selector names.** In an `NSObject` subclass, a method whose name has no
  inner underscore (or ends with one) becomes an Objective-C selector. The
  argument count must match the number of colons, otherwise the class
  definition raises `BadPrototypeError`.
  - `_draw(self, view)` fails.
  - `_draw_crab(self, view)` and `show(self)` are fine.
  - Keep logic in plain Python classes (`MacApp`) and keep the ObjC
    subclasses thin.
- Call superclass methods with `objc.super(Class, self)`.
- Plain Python attributes on instances of these subclasses are fine
  (`CrabView.app`, `MenuTarget.actions`).
- Pyright reports false positives on PyObjC's dynamic attributes; ignore
  them.

## Deliberate choices, don't "fix" these

- Sprites have no outline.
- There is no squash/stretch and no breathing. It was tried and the user
  disliked it: cutting a body row made the head look clipped.
- Working, reading and painting turn Claudy three-quarters toward the prop,
  like Clawd in the Claude app. The pose uses the `+` side-face color.
- Juggling balls are drawn by the scene behind Claudy, not as part of the
  sprite.
- Particles are pixel art. The gift on the Dock is still an emoji, on
  purpose.

## Working with the user

- Commit straight to `main`, with no branches or PRs. Push only when the
  user asks.
- Code, comments and docs are in English. The user writes in Russian, and
  the in-app phrases are Russian, with English translations in
  `content/phrases.py`.
- Keep fixes inside `claudy/backends/macos/` when you can. If shared code
  must change, run the tests and say so, since Linux can't be checked from
  the Mac.
- When macOS is confirmed working, delete this file and move anything
  lasting into `CLAUDE.md`.
