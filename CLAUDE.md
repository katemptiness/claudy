# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claudy is an autonomous desktop companion — a pixel-art crab character that lives on top of the Dock, performs activities on its own, and reacts to user interactions and system events. It is **not** a tamagotchi: no needs, no health bars, no demands. The crab is self-sufficient.

**Supported platforms:** macOS (PyObjC/AppKit) and Linux (GTK3/Cairo).

> **On a Mac?** The macOS backend changed on 2026-09-29 without running on a Mac. Read `docs/macos-checklist.md` first.

## Running

**macOS:**
```bash
pip install pyobjc pyobjc-framework-Quartz
python3 app.py
```

**Build the macOS app:**
```bash
pip install py2app
tools/build_app.sh          # build, install to /Applications, relaunch
```
`assets/claudy.icns` is the app icon, drawn from the sprites by `tools/make_icon.py`
(needs Pillow, and `iconutil` from macOS); it is committed, so it only needs
regenerating when the icon changes.

**Linux (Ubuntu 24.04+):**
```bash
# GTK3, PyGObject, and Cairo are typically pre-installed on Ubuntu
# If not: sudo apt install python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-3.0
python3 app.py    # or /usr/bin/python3 if using system Python
```

**Tests** (standard library `unittest`; core, content, render and the Linux backend's logic):
```bash
python3 -m unittest discover -s tests -t .
```
Run exactly this, from the project root. Importing the `tests` package points
`CLAUDY_HOME` at a temp dir; run any other way, Claudy's modules would resolve
the real `~/.claudy`, so `tests/support.py` refuses to reset anything outside
that temp dir (it once deleted the user's memory). Any ad-hoc script that
imports `claudy` must set `CLAUDY_HOME` to a temp dir before the import.

Run `python3 app.py` from a terminal to see tracebacks. Exceptions raised inside
the frame loop are caught and logged as `tick failed` in `~/.claudy/error.log`;
Claudy keeps running but may freeze, so check the log whenever it looks stuck.
Uncaught exceptions elsewhere reach the log too (`log.install_excepthook()`).
AppKit swallows what its callbacks raise, so the macOS callbacks run their
bodies under `log.reported()`, which logs and prints instead. The log is capped
in size, and a traceback repeating every frame is written once, then counted.
Settings → developer mode adds an *Activities* submenu that starts any activity
on demand and offers a test gift.

## Tech Stack

- **Shared core**: Python 3, pure-logic state machine, pixel-art sprites
- **macOS backend**: PyObjC, AppKit, Quartz (CGContext drawing in NSViews)
- **Linux backend**: GTK3, PyGObject, Cairo
- Sprites: 16-row pixel grids, 16 columns wide (24 or 32 with a prop), drawn at 5x (a 16x16 sprite is 80x80)
- Window: borderless transparent always-on-top on both platforms
- Pyright will report false positives on all PyObjC dynamic attributes — these are expected

## Architecture

Everything lives in the `claudy` package; `app.py` is only the entry point.

### Core (`claudy/core/`, platform-independent)
- `controller.py` — `Controller`: the app logic shared by both backends. Owns the Character, particles, the Speech state, the gift Claudy offers and the dreams that surface while he sleeps; handles character events, speech timing (idle-chatter rate limit, pinned gift announcements), clicks/hover/drag, system sleep/wake, app launches, and builds the context menu as `MenuItem`s. Talks to the backend through the small `Platform` interface (open apps/windows, quit).
- `speech.py` — `Speech`: bubble state (typewriter text, fade in/out alpha)
- `character.py` — `Character` state machine and phased animation engine. Emits events (`message`, `particle`, `gift`, `gift_star`) collected with `take_events()`; `update(dt)` returns a view dict (sprite, x, y_offset, shake_dx, facing, friend, toy, juggle). A gift Claudy finds is offered when the activity ends, so the catch or spell it came from is seen first.
- `activities.py` — immutable activity scripts (`Phase` dataclasses), reactions, friend-visit pool, random outcomes (catches, magic results) and gift chances
- `animations.py` — Bounce, Shake, Hop, Fall, Juggle (ball arcs; the scene draws the balls behind Claudy)
- `particles.py` — 15 particle kinds (`Kind`: images, velocity, gravity, drag, sway, spawn at head/feet), `ParticleSystem` (dt-based, fades in/out)
- `schedule.py` — time-of-day weights (night owl / early bird modes), and `is_dark()` (19:00–6:00) for the named star
- `settings.py` — settings persistence (JSON, written atomically) via typed descriptors that validate every value in one place, cooldown/duration maps
- `memory.py` — per-session relationship state: clicks, app launches, the days counter, gifts, and the activity log dreams come from. All of it starts fresh on each launch, except the named star (which is also migrated from older builds, where it lived only as a gift) and the first launch date. An unreadable file is set aside as `memory.json.bad`, never silently overwritten.

### Top level (`claudy/`)
- `config.py` — palette, sizes, timing, and `DATA_DIR` (`~/.claudy`, or `CLAUDY_HOME`)
- `log.py` — the error log: size-capped, repeated tracebacks throttled, `install_excepthook()` (called first thing in `app.py`)

### Content (`claudy/content/`)
- `phrases.py` — Claudy's speech (Russian keys, English translations via `t()`), phrase pools, `pick()` helpers
- `ui_text.py` — bilingual labels for menus, settings and gifts windows
- `app_reactions.py` — app categories → phrases/activities; macOS bundle IDs and Linux process names
- `gift_stories.py` — backstories for collected gifts
- `sprites/` — sprites as text grids (`grid.py` documents the symbols); `SPRITES` dict; `particles.py` holds particle pixel art with its own colors; `items.py` holds the gifts Claudy leaves, the toy he sleeps with, the named star and how it twinkles (`STAR_TWINKLE`), the dream cloud and the things he dreams about, plus `GIFT_ART` (offered gift emoji → picture) and `DREAM_ART` (activity → pictures)

### Rendering (`claudy/render/`, platform-independent)
- `scene.py` — `Scene`: paints all four windows through a Canvas — crab window (Claudy, friend, toy), ground overlay (shadows, gift, particles, dreams), star window (the named star, `star_offset_x()` places it), speech bubble (`bubble_layout()` wraps and sizes it). `FEET_Y` / `GROUND_Y` is the ground line: sprites leave their last two rows empty, and everything standing beside Claudy stands on it.
- `canvas.py` — the `Canvas` interface backends implement (`image`, `rect`, `text`, `measure`; top-left origin) and `ImageCache`
- `art.py` — pixel art as `PixelImage`s, identified by hashable keys (`sprite_key(name, friend, flip)`, `particle_key(name, tint)`, `item_key(name)`). Applies the shading pass (highlight/shadow/eye glint).

### Backends (`claudy/backends/`)
Each backend creates the windows, forwards input, runs the frame loop and implements a Canvas.
- `macos/app.py` — `MacApp` (windows, frame loop) + thin ObjC subclasses (`AppDelegate`, `CrabView`, `MenuTarget`)
- `macos/canvas.py` (Quartz canvas), `views.py` (`DrawingView`, overlay windows), `bubble.py`, `events.py` (NSWorkspace), `settings_ui.py`, `gifts_ui.py`
  - AppKit is y-up and the views stay unflipped, so hit testing, tracking areas and mouse locations use AppKit's usual coordinates (`SPRITE_RECT` is y-up). The Scene paints top-left down; `QuartzCanvas._flip` converts, and `canvas.make_image` flips its bitmap so row 0 of the art ends up on top.
- `linux/app.py` — `CrabApp` (GTK windows, GLib loop) + `LinuxPlatform`. GTK is started on X11 (XWayland under Wayland, which doesn't let an app place its windows); `GDK_BACKEND` is set only for that and removed again, so apps Claudy launches don't inherit it. The windows follow monitor changes.
- `linux/windows.py` (the transparent, click-through overlay window factory; click-through is set on the `Gtk.Window`, because GTK resets a `GdkWindow`'s input shape when it is realized), `canvas.py` (Cairo/Pango canvas), `bubble.py`, `events.py` (logind D-Bus, whose connection must stay referenced, + process polling matched against whole process names), `settings_ui.py`, `gifts_ui.py`

## Key Concepts

- **Sprite symbols**: `.` transparent, `#` body (#D77757), `e` eyes (#2D2D2D), `b` blush, `w` brown, `c` cream, `u` blue, `p` purple, `g` gray, `y` gold, `s`/`S` sand, `o` flame orange, `r` red, `n` green, `k` shell pink, `d`/`l` dark/light metal, `+` Claudy's side face in three-quarter poses — mapped to palette indices 0–18 in `config.PALETTE` (see `content/sprites/grid.py`). Sprites are 16 rows tall and 16 columns wide, or wider in steps of two when a prop needs room; Claudy stays centered. Only `#` pixels get the body shading, so props should use other colors. Working, reading and painting turn Claudy three-quarters toward the prop, like Clawd in the Claude app: a 2-column `+` side face away from the prop, eyes shifted toward it. Painting pictures are composed from stages (`PICTURES` / `painting_sprites()` in `sprites/activities.py`); `Character._special_pick_painting` picks one per run.
- **Phased activities**: each activity is a tuple of `Phase` objects with frames, interval, duration, optional message/particle/effects/special. The Character copies the phases when an activity starts; per-run changes (catch reaction, marshmallow, friend visit) modify only that copy. `Phase.special = "x"` runs `Character._special_x()` on entry.
- **State machine**: idle/walking + 16 activities + reactions + `waking` (launch / system wake) + `dragging`. Weighted random transitions via `schedule.get_weights()`, avoiding the last two activities.
- **Windows**: the small crab window (takes clicks, moves up when Claudy hops), a taller click-through ground overlay (200x300) that stays on the Dock, the speech bubble, and a small square window for the named star. A single tall interactive window blocked clicks on macOS, hence the split. The star needs its own window because both of the others follow Claudy along the Dock, and a star that slid across the screen with him would not read as a star; its height is `settings.star_height` and its horizontal spot comes from the user's name, so it never moves.
- **Redrawing**: a view is marked dirty only when `Scene.crab_changed()` / `ground_changed()` / `star_changed()` says its drawing calls differ from the last frame. Claudy holds still most of the time, and repainting transparent always-on-top windows at 60 FPS costs several times the CPU. Both backends ask before redrawing, and the Linux backend moves a window only when its spot changes. The speech bubble redraws when its text, typing or fade changes on Linux, and every frame while shown on macOS.
- **PyObjC gotcha**: in `NSObject` subclasses, a method name without an inner underscore (e.g. `_draw(self, view)`, `show(self, text)`) becomes an ObjC selector and must take exactly as many args as its colons → `BadPrototypeError` otherwise. Keep logic in plain Python classes (like `MacApp`) or use names like `_draw_crab`.

## Deliberate choices, don't "fix" these

- Sprites have no outline.
- There is no squash/stretch and no breathing. It was tried and the user disliked it: cutting a body row made the head look clipped.
- Juggling balls are drawn by the scene behind Claudy, not as part of the sprite.
- Particles are pixel art, and so are the gifts and the toy (`content/sprites/items.py`). Emoji stay where they are text: in speech bubbles, in the menus and in the gifts window.
- Gifts and the toy are drawn on Claudy's own pixel grid (`ITEM_SCALE == PIXEL_SCALE`), not the finer particle grid. They are objects in his world, not effects; at particle size they read as icons borrowed from another game. They stand on the ground line and cast a shadow like his; the toy stands behind him, so his claw lies across it. The named star is the one exception (`ITEM_SCALES`, the particle grid): it is far away, and at his scale it would read as an object hanging in mid-air.
- The dream cloud (`ITEM_ART["dream_cloud"]`) is one fixed picture drawn with one opacity: round lobes, a cool mid-tone edge, a shaded underside, round bubbles trailing to the sleeper. It must never read as speech, so its edge is nowhere near the bubble's dark ink (a test checks). It used to be built from translucent rects around each picture: where they overlapped, the opacity doubled into seams, and cream with no edge vanished on light desktops. Particles go behind it, and no zzz rise while it shows.
- Claudy dreams only of activities that left a picture in `DREAM_ART`; the rest simply never turn up in a dream. `Memory.log_activity()` collapses runs of the same activity: in deep sleep "sleeping" is the only choice, so every click that wakes him at night, and every system sleep, logs it again, and would crowd everything dreamable out of the log by morning.
- The named star shows by real clock hours (`schedule.is_dark()`), not by schedule period — in owl mode "deep sleep" runs to 11:00, long after the stars are gone.
- Claudy names exactly one star, ever, and it outlives the session in `memory.json`. A second would silently replace the first in the sky, and a rebuild would wipe it.
- The star twinkles by shape, through a few uneven steps (`STAR_TWINKLE`), at full opacity: faded, its gold turned khaki over a dark sky, and a continuous fade would wake an always-on-top window every frame (`Scene.star_changed()` compares drawing calls). Claudy names it only after dark.
- The macOS windows use `FullScreenAuxiliary | Stationary` and deliberately not `CanJoinAllSpaces`. Claudy was checked on macOS 26.7: it stays visible across Spaces and over full-screen apps as it is.

## Reference Files (`docs/`)

- `macos-checklist.md` — what changed in the macOS backend without a Mac to test on, and what is left for one
- `prototypes/clawd-tamagotchi.jsx` — React prototype with base sprites, particle system, game loop
- `prototypes/clawd-activities.jsx` — React demo of 4 activities with phased animations
- `little-claude-spec.md` — full project specification (in Russian)
- `UPDATE-SPEC-v2.md` — v2 "Relationships" update spec (in Russian)

## Language

The spec and in-app phrases are in Russian. Code (variable names, comments, docs) should be in English.
