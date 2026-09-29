# macOS checklist — for the Mac-side Claude

On 2026-09-29 the whole project was reviewed and fixed from Linux. The macOS
backend changed along the way, but nobody could run it: it was only
exercised with AppKit, Quartz and objc stubbed out. Everything below needs
a real Mac. Delete this file once it is done, and move anything lasting
into `CLAUDE.md`.

Run the tests first, exactly as `CLAUDE.md` says. Run `python3 app.py` from a
terminal: macOS callbacks now log to `~/.claudy/error.log` *and* print
their traceback.

## Changed today — check that each works

1. **Frame timer in common run-loop modes.** Right-click Claudy and leave the
   menu open: he keeps moving and the bubble keeps typing. In Settings, drag
   the Height and Star height sliders: Claudy and the star move while the
   knob is still held. Open About: Claudy keeps moving behind it.
2. **Clicks.**
   - A single click fires after the system double-click interval.
   - A slow double-click opens Claude once, without a greeting.
   - A triple-click opens Claude only once.
   - Click, then quickly grab and drag: he follows the pointer all the way.
   - Click, then right-click within the interval: the greeting happens
     *before* the menu opens. A menu choice such as Give a gift → Flower must
     not be followed by a stray greeting.
3. **Control-click** opens the context menu and does not greet.
4. **Dragging.**
   - While held, the shadow on the Dock shrinks and fades, and it does not
     snap on release.
   - He can't be dragged off his screen sideways.
   - Dropped from high up, a "!" pops above his head as he falls into view.
5. **Geometry comes from the primary display** (`NSScreen.screens()[0]`).
   - With two displays, Claudy, his bubble and the star all live on the
     primary one.
   - The star doesn't jump when focus moves between displays.
6. **Activation.**
   - About, and Settings or Gifts reopened while already open, come to the
     front with keyboard focus.
   - Return dismisses About.
7. **Double-click opens Claude** through `openApplicationAtURL_…` (bundle id
   `com.anthropic.claudefordesktop`), or claude.ai if the app is missing.
   Check that passing `None` as the completion handler raises nothing.
8. **Errors reach the log.** Callbacks run under `log.reported()`: mouse,
   menu, sleep/wake, app launch and startup. A failed launch should log,
   print, and quit, not leave a process with no windows.
9. **Settings.** A hand-edited `gift_limit` that isn't a preset (say 7)
   survives Save unless another preset is picked.
10. **Build.**
    - `tools/build_app.sh` still bundles libffi. It is now looked for next
      to the building Python.
    - It relaunches `/Applications/Claudy.app` by path.
11. **Icon.** `tools/make_icon.py` now draws the 32 and 64 px sizes on the
    pixel grid. Regenerate `assets/claudy.icns` (it needs `iconutil`) and
    commit it; the committed file predates the change. Check the 32 px icon
    in Finder's list view.
12. **Visuals shared with Linux** (already checked there):
    - the dream's thought cloud;
    - the teddy standing behind a sleeping Claudy on his ground line;
    - shadows under gifts;
    - the star twinkling by shape.

## Left for you — each needs a real Mac to get right

- **Clicks through the crab window.** It takes clicks across its whole
  200x90 frame, because `setIgnoresMouseEvents_(False)` is set explicitly
  and `hitTest_` returning None can't hand a click to another app. That
  leaves a dead zone over nearby Dock icons.
  - Suggested fix, matching Linux: in `MacApp.tick`, flip
    `setIgnoresMouseEvents_` whenever `NSEvent.mouseLocation()` enters or
    leaves the sprite rect.
  - Hover tracking and dragging must keep working.
- **Clicking Claudy activates the app** and takes keyboard focus from
  whatever the user was typing in.
  - Suggested fix: make the crab window an `NSPanel` with
    `NSWindowStyleMaskNonactivatingPanel`, and use `orderFront_` instead of
    `makeKeyAndOrderFront_`.
  - Check that the menu, dragging and Spaces behaviour stay as they are.
- **Screen changes.** Linux follows a monitor change through
  `Controller.set_screen_width()`, but macOS reads its geometry once.
  Listen for `NSApplicationDidChangeScreenParametersNotification`, then
  re-read the screen and the Dock line and call `set_screen_width`.
- **Settings form.**
  - `form_h = 878` is summed by hand, and the popup block is copy-pasted
    seven times.
  - Lay the form out top-down on a flipped document view. Add one choice
    helper that falls back to the setting's own default, for example
    `Settings.fields()[name].default`.
- **Warp.** "Open Claude Code" only opens a tab; there is no documented way
  to run a command in it. The README says so. If this should work,
  consider a launch configuration.
- **Bubble redraws** (optional). The Linux bubble now redraws only when its
  text, typing or fade changes; the macOS one redraws every frame while
  shown.
