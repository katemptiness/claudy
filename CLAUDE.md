# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claudy is an autonomous desktop companion — a pixel-art crab character that lives on top of the Dock, performs activities on its own, and reacts to user interactions and system events. It is **not** a tamagotchi: no needs, no health bars, no demands. The crab is self-sufficient.

**Supported platforms:** macOS (PyObjC/AppKit) and Linux (GTK3/Cairo).

## Running

**macOS:**
```bash
pip install pyobjc pyobjc-framework-Quartz
python3 app.py
```

**Linux (Ubuntu 24.04+):**
```bash
# GTK3, PyGObject, and Cairo are typically pre-installed on Ubuntu
# If not: sudo apt install python3-gi python3-cairo gir1.2-gtk-3.0
python3 app.py    # or /usr/bin/python3 if using system Python
```

**Tests** (core only, standard library `unittest`):
```bash
python3 -m unittest discover -s tests -t .
```
Tests set `CLAUDY_HOME` to a temp dir so they never touch the real `~/.claudy`.

Run `python3 app.py` from a terminal to see tracebacks. Exceptions raised inside
the frame loop are caught and logged as `tick failed` in `~/.claudy/error.log`;
Claudy keeps running but may freeze, so check the log whenever it looks stuck.
Settings → developer mode adds an *Activities* submenu that starts any activity
on demand and offers a test gift.

## Tech Stack

- **Shared core**: Python 3, pure-logic state machine, pixel-art sprites
- **macOS backend**: PyObjC, AppKit, Quartz (CALayer, CGContext)
- **Linux backend**: GTK3, PyGObject, Cairo
- Sprites: 16x16 pixel grids rendered via platform-specific backends, displayed at 5x scale (80x80)
- Window: borderless transparent always-on-top on both platforms
- Pyright will report false positives on all PyObjC dynamic attributes — these are expected

## Architecture

Everything lives in the `claudy` package; `app.py` is only the entry point.

### Core (`claudy/core/`, platform-independent)
- `controller.py` — `Controller`: the app logic shared by both backends. Owns the Character, particles, the Speech state and the gift Claudy offers; handles character events, speech timing (idle-chatter rate limit, pinned gift announcements), clicks/hover/drag, system sleep/wake, app launches, and builds the context menu as `MenuItem`s. Talks to the backend through the small `Platform` interface (open apps/windows, quit).
- `speech.py` — `Speech`: bubble state (typewriter text, fade in/out alpha)
- `character.py` — `Character` state machine and phased animation engine. Emits events (`message`, `particle`, `gift`, `gift_star`) collected with `take_events()`; `update(dt)` returns a view dict (sprite, x, y_offset, shake_dx, facing, friend, toy).
- `activities.py` — immutable activity scripts (`Phase` dataclasses), reactions, friend-visit pool, random outcomes (catches, magic results) and gift chances
- `animations.py` — Bounce, Shake, Hop, Fall, Juggle (ball arcs; the scene draws the balls behind Claudy)
- `particles.py` — 15 particle kinds (`Kind`: images, velocity, gravity, drag, sway, spawn at head/feet), `ParticleSystem` (dt-based, fades in/out)
- `schedule.py` — time-of-day weights (night owl / early bird modes)
- `settings.py` — settings persistence (JSON) via typed descriptors, cooldown/duration maps
- `memory.py` — relationship tracking, gift storage, click/day counters

### Content (`claudy/content/`)
- `phrases.py` — Claudy's speech (Russian keys, English translations via `t()`), phrase pools, `pick()` helpers
- `ui_text.py` — bilingual labels for menus, settings and gifts windows
- `app_reactions.py` — app categories → phrases/activities; macOS bundle IDs and Linux process names
- `gift_stories.py` — backstories for collected gifts
- `sprites/` — sprites as text grids (`grid.py` documents the symbols); `SPRITES` dict; `particles.py` holds particle pixel art with its own colors

### Rendering (`claudy/render/`, platform-independent)
- `scene.py` — `Scene`: paints all three windows through a Canvas — crab window (Claudy, friend, toy), ground overlay (shadows, gift, particles), speech bubble (`bubble_layout()` wraps and sizes it)
- `canvas.py` — the `Canvas` interface backends implement (`image`, `rect`, `text`, `measure`; top-left origin) and `ImageCache`
- `art.py` — pixel art as `PixelImage`s, identified by hashable keys (`sprite_key(name, friend, flip)`, `particle_key(name, tint)`). Applies the shading pass (highlight/shadow/eye glint).

### Backends (`claudy/backends/`)
Each backend creates the windows, forwards input, runs the frame loop and implements a Canvas.
- `macos/app.py` — `MacApp` (windows, frame loop) + thin ObjC subclasses (`AppDelegate`, `CrabView`, `MenuTarget`)
- `macos/canvas.py` (Quartz canvas), `views.py` (`DrawingView`, overlay windows), `bubble.py`, `events.py` (NSWorkspace), `settings_ui.py`, `gifts_ui.py`
  - AppKit is y-up and the views stay unflipped, so hit testing, tracking areas and mouse locations use AppKit's usual coordinates (`SPRITE_RECT` is y-up). The Scene paints top-left down; `QuartzCanvas._flip` converts, and `canvas.make_image` flips its bitmap so row 0 of the art ends up on top.
- `linux/app.py` — `CrabApp` (GTK windows, GLib loop) + `LinuxPlatform`
- `linux/canvas.py` (Cairo/Pango canvas), `bubble.py`, `events.py` (logind D-Bus + process polling), `settings_ui.py`, `gifts_ui.py`

## Key Concepts

- **Sprite symbols**: `.` transparent, `#` body (#D77757), `e` eyes (#2D2D2D), `b` blush, `w` brown, `c` cream, `u` blue, `p` purple, `g` gray, `y` gold, `s`/`S` sand, `o` flame orange, `r` red, `n` green, `k` shell pink, `d`/`l` dark/light metal, `+` Claudy's side face in three-quarter poses — mapped to palette indices 0–18 in `config.PALETTE` (see `content/sprites/grid.py`). Sprites are 16 rows tall and 16 columns wide, or wider in steps of two when a prop needs room; Claudy stays centered. Only `#` pixels get the body shading, so props should use other colors. Working, reading and painting turn Claudy three-quarters toward the prop, like Clawd in the Claude app: a 2-column `+` side face away from the prop, eyes shifted toward it. Painting pictures are composed from stages (`PICTURES` / `painting_sprites()` in `sprites/activities.py`); `Character._special_pick_painting` picks one per run.
- **Phased activities**: each activity is a tuple of `Phase` objects with frames, interval, duration, optional message/particle/effects/special. The Character copies the phases when an activity starts; per-run changes (catch reaction, marshmallow, friend visit) modify only that copy. `Phase.special = "x"` runs `Character._special_x()` on entry.
- **State machine**: idle/walking + 16 activities + reactions + `waking` (launch / system wake) + `dragging`. Weighted random transitions via `schedule.get_weights()`, avoiding the last two activities.
- **Windows**: the small crab window (takes clicks, moves up when Claudy hops), a taller click-through ground overlay (200x300) that stays on the Dock, and the speech bubble. A single tall interactive window blocked clicks on macOS, hence the split.
- **Redrawing**: a view is marked dirty only when `Scene.crab_changed()` / `ground_changed()` says its drawing calls differ from the last frame. Claudy holds still most of the time, and repainting two transparent always-on-top windows at 60 FPS costs several times the CPU. Linux still redraws every frame and could adopt the same two calls.
- **PyObjC gotcha**: in `NSObject` subclasses, a method name without an inner underscore (e.g. `_draw(self, view)`, `show(self, text)`) becomes an ObjC selector and must take exactly as many args as its colons → `BadPrototypeError` otherwise. Keep logic in plain Python classes (like `MacApp`) or use names like `_draw_crab`.

## Deliberate choices, don't "fix" these

- Sprites have no outline.
- There is no squash/stretch and no breathing. It was tried and the user disliked it: cutting a body row made the head look clipped.
- Juggling balls are drawn by the scene behind Claudy, not as part of the sprite.
- Particles are pixel art. The gift on the Dock is still an emoji, on purpose.

## Reference Files (`docs/`)

- `prototypes/clawd-tamagotchi.jsx` — React prototype with base sprites, particle system, game loop
- `prototypes/clawd-activities.jsx` — React demo of 4 activities with phased animations
- `little-claude-spec.md` — full project specification (in Russian)
- `UPDATE-SPEC-v2.md` — v2 "Relationships" update spec (in Russian)

## Language

The spec and in-app phrases are in Russian. Code (variable names, comments, docs) should be in English.
