# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claudy is an autonomous desktop companion for macOS — a pixel-art crab character that lives on top of the Dock, performs activities on its own, and reacts to user interactions and system events. It is **not** a tamagotchi: no needs, no health bars, no demands. The crab is self-sufficient.

## Running

```bash
pip install pyobjc pyobjc-framework-Quartz
python3 app.py
```

## Tech Stack

- **Python 3 + PyObjC** (`pyobjc`, `pyobjc-framework-Quartz`)
- Pure AppKit rendering (no SpriteKit, no Metal)
- Sprites: 16x16 pixel grids rendered via `CGContext` → `CGImage`, displayed on `CALayer`
- Window: borderless `NSWindow` with transparent background, always-on-top
- Pyright will report false positives on all PyObjC dynamic attributes — these are expected

## Architecture

- `app.py` — entry point, NSApplication, NSWindow, 60fps update loop, CrabView (mouse events), particle rendering, context menu, startup animation
- `character.py` — state machine, phased animation engine, activity/reaction definitions, random outcomes (fishing catches, magic results)
- `sprite_renderer.py` — `render_sprite(grid) → CGImage` via CGBitmapContext, `SpriteCache` class
- `sprites/base.py` — idle, blink, walk_a, walk_b grids
- `sprites/activities.py` — all activity + reaction sprites (39 sprites)
- `animations.py` — BounceAnimation, ShakeAnimation, GravityDrop
- `particles.py` — 14 particle types (zzz, sparkle, heart, note, etc.), ParticleSystem with CATextLayer rendering
- `speech.py` — SpeechBubble: separate NSWindow, fade in/out, rate limiting (30s cooldown, 30% probability)
- `schedule.py` — time-of-day weights (night owl: deep_sleep 04-11, morning 11-13, day 13-20, evening 20-01, late_night 01-04)
- `system_events.py` — NSWorkspace notification subscriptions (sleep/wake, app launches with bundle ID → phrase lookup)
- `config.py` — palette (hex → RGBA), grid/pixel constants, window dimensions

## Key Concepts

- **Sprite palette**: `0`=transparent, `1`=body (#D77757), `2`=eyes (#2D2D2D), `3`=blush (#F0C0A0), `4`=brown prop, `5`=cream prop, `6`=blue prop, `7`=purple, `8`=gray, `9`=gold
- **Phased activities**: each activity is a list of `Phase` objects with frames, interval, duration, optional message/particle/effects. Character advances through phases automatically.
- **State machine**: idle/walking + 12 activities + reactions. Weighted random transitions via `schedule.get_weights()`.
- **Particles**: `CATextLayer` sublayers on a larger transparent window (200x300) — crab sits at bottom-center, particles float upward in the space above.

## Reference Files

- `clawd-tamagotchi.jsx` — React prototype with base sprites, particle system, game loop
- `clawd-activities.jsx` — React demo of 4 activities with phased animations
- `little-claude-spec.md` — full project specification (in Russian)

## Language

The spec and in-app phrases are in Russian. Code (variable names, comments, docs) should be in English.
