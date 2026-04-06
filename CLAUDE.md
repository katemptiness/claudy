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

## Tech Stack

- **Shared core**: Python 3, pure-logic state machine, pixel-art sprites
- **macOS backend**: PyObjC, AppKit, Quartz (CALayer, CGContext)
- **Linux backend**: GTK3, PyGObject, Cairo
- Sprites: 16x16 pixel grids rendered via platform-specific backends, displayed at 5x scale (80x80)
- Window: borderless transparent always-on-top on both platforms
- Pyright will report false positives on all PyObjC dynamic attributes — these are expected

## Architecture

### Cross-platform entry point
- `app.py` — detects OS, delegates to the correct platform backend

### Shared core (platform-independent)
- `character.py` — state machine, phased animation engine, activity/reaction definitions, random outcomes
- `sprites/base.py` — idle, blink, walk_a, walk_b grids
- `sprites/activities.py` — all activity + reaction sprites (39 sprites)
- `animations.py` — BounceAnimation, ShakeAnimation, GravityDrop
- `particles.py` — 14 particle types (zzz, sparkle, heart, note, etc.), ParticleSystem
- `schedule.py` — time-of-day weights (night owl / early bird modes)
- `settings.py` — settings persistence (JSON), constants, cooldown/duration maps
- `phrases.py` — bilingual phrase system (Russian/English)
- `memory.py` — relationship tracking, gift system, click/day counters
- `config.py` — palette (hex → RGBA), grid/pixel constants, window dimensions

### Platform backends
- `backends/macos/app.py` — NSApplication, NSWindow, 60fps update loop, CrabView, particle rendering, context menu
- `backends/macos/renderer.py` — `render_sprite(grid) → CGImage` via CGBitmapContext
- `backends/macos/speech.py` — SpeechBubble via NSWindow
- `backends/macos/events.py` — NSWorkspace notifications (sleep/wake, app launches via bundle ID)
- `backends/macos/settings_ui.py` — AppKit settings window
- `backends/linux/app.py` — GTK3 application, transparent windows, GLib main loop, Cairo rendering
- `backends/linux/renderer.py` — `render_sprite(grid) → cairo.ImageSurface`
- `backends/linux/speech.py` — SpeechBubble via GTK3 popup
- `backends/linux/events.py` — D-Bus logind (sleep/wake), process-based app detection
- `backends/linux/settings_ui.py` — GTK3 settings dialog

## Key Concepts

- **Sprite palette**: `0`=transparent, `1`=body (#D77757), `2`=eyes (#2D2D2D), `3`=blush (#F0C0A0), `4`=brown prop, `5`=cream prop, `6`=blue prop, `7`=purple, `8`=gray, `9`=gold
- **Phased activities**: each activity is a list of `Phase` objects with frames, interval, duration, optional message/particle/effects. Character advances through phases automatically.
- **State machine**: idle/walking + 12 activities + reactions. Weighted random transitions via `schedule.get_weights()`.
- **Particles**: Text/emoji rendered on a larger transparent overlay window (200x300) — crab sits at bottom-center, particles float in the space above. macOS uses CATextLayer, Linux uses Pango/Cairo.

## Reference Files

- `clawd-tamagotchi.jsx` — React prototype with base sprites, particle system, game loop
- `clawd-activities.jsx` — React demo of 4 activities with phased animations
- `little-claude-spec.md` — full project specification (in Russian)

## Language

The spec and in-app phrases are in Russian. Code (variable names, comments, docs) should be in English.
