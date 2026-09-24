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
- `animations.py` — Bounce, Shake, Hop, Fall
- `particles.py` — 15 particle types, `ParticleSystem` (dt-based)
- `schedule.py` — time-of-day weights (night owl / early bird modes)
- `settings.py` — settings persistence (JSON) via typed descriptors, cooldown/duration maps
- `memory.py` — relationship tracking, gift storage, click/day counters

### Content (`claudy/content/`)
- `phrases.py` — Claudy's speech (Russian keys, English translations via `t()`), phrase pools, `pick()` helpers
- `ui_text.py` — bilingual labels for menus, settings and gifts windows
- `app_reactions.py` — app categories → phrases/activities; macOS bundle IDs and Linux process names
- `gift_stories.py` — backstories for collected gifts
- `sprites/` — sprites as 16x16 text grids (`grid.py` documents the symbols); `SPRITES` dict

### Rendering (`claudy/render/`, platform-independent)
- `scene.py` — `Scene`: paints all three windows through a Canvas — crab window (Claudy, friend, toy), ground overlay (shadows, gift, particles), speech bubble (`bubble_layout()` wraps and sizes it)
- `canvas.py` — the `Canvas` interface backends implement (`image`, `rect`, `text`, `measure`; top-left origin) and `ImageCache`
- `art.py` — pixel art as `PixelImage`s, identified by hashable keys (`sprite_key(...)`)

### Backends (`claudy/backends/`)
Each backend creates the windows, forwards input, runs the frame loop and implements a Canvas.
- `macos/app.py` — `MacApp` (windows, frame loop) + thin ObjC subclasses (`AppDelegate`, `CrabView`, `MenuTarget`)
- `macos/canvas.py` (Quartz canvas), `views.py` (`DrawingView`, overlay windows), `bubble.py`, `events.py` (NSWorkspace), `settings_ui.py`, `gifts_ui.py`
- `linux/app.py` — `CrabApp` (GTK windows, GLib loop) + `LinuxPlatform`
- `linux/canvas.py` (Cairo/Pango canvas), `bubble.py`, `events.py` (logind D-Bus + process polling), `settings_ui.py`, `gifts_ui.py`

## Key Concepts

- **Sprite symbols**: `.` transparent, `#` body (#D77757), `e` eyes (#2D2D2D), `b` blush (#F0C0A0), `w` brown prop, `c` cream prop, `u` blue prop, `p` purple, `g` gray, `y` gold — mapped to palette indices 0–9 in `config.PALETTE`
- **Phased activities**: each activity is a tuple of `Phase` objects with frames, interval, duration, optional message/particle/effects/special. The Character copies the phases when an activity starts; per-run changes (catch reaction, marshmallow, friend visit) modify only that copy. `Phase.special = "x"` runs `Character._special_x()` on entry.
- **State machine**: idle/walking + 16 activities + reactions + `waking` (launch / system wake) + `dragging`. Weighted random transitions via `schedule.get_weights()`, avoiding the last two activities.
- **Windows**: the small crab window (takes clicks, moves up when Claudy hops), a taller click-through ground overlay (200x300) that stays on the Dock, and the speech bubble. A single tall interactive window blocked clicks on macOS, hence the split.
- **PyObjC gotcha**: in `NSObject` subclasses, a method name without an inner underscore (e.g. `_draw(self, view)`, `show(self, text)`) becomes an ObjC selector and must take exactly as many args as its colons → `BadPrototypeError` otherwise. Keep logic in plain Python classes (like `MacApp`) or use names like `_draw_crab`.

## Reference Files (`docs/`)

- `prototypes/clawd-tamagotchi.jsx` — React prototype with base sprites, particle system, game loop
- `prototypes/clawd-activities.jsx` — React demo of 4 activities with phased animations
- `little-claude-spec.md` — full project specification (in Russian)
- `UPDATE-SPEC-v2.md` — v2 "Relationships" update spec (in Russian)

## Language

The spec and in-app phrases are in Russian. Code (variable names, comments, docs) should be in English.
