# Claudy

<p align="center">
  <img src="https://img.shields.io/badge/platform-macOS-blue" alt="macOS">
  <img src="https://img.shields.io/badge/python-3.10+-yellow" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
</p>

A tiny pixel-art crab companion that lives on your macOS Dock. It reads books, catches fish, does magic, writes code, and generally goes about its little crab life — all on its own. Formerly known as Little Claude.

<p align="center">
  <img src="screens/screen1.png" width="280" alt="Claudy juggling">
  <img src="screens/screen2.png" width="280" alt="Claudy idle">
  <img src="screens/screen3.png" width="280" alt="Claudy on the Dock">
</p>

**Claudy is not a tamagotchi.** It has no needs, no health bars, no demands. It's a self-sufficient creature with its own schedule, moods, and activities. You're just an observer — and sometimes a friend.

## What it does

- Wanders along the Dock, performing 14 different activities: reading, fishing, magic, coding, sleeping, playing, painting, stargazing, meditating, juggling, listening to music, and summoning a friend
- Follows a configurable schedule — night owl (default) or early bird mode
- Reacts to clicks (sparkles + hearts!), hover (waves hello), and drag-and-drop (surprise + gravity bounce)
- Mirrors your activity — open a terminal or code editor and the crab starts coding; open Spotify and it listens to music
- Notices when you launch apps and comments on them
- Sleeps when your Mac sleeps, yawns when it wakes up
- Says things in cute speech bubbles — in Russian or English (configurable)
- Occasionally mutters to itself while idling ("thinking about fish...", "bored...", ":3")
- All rendered as pixel art: 16x16 sprite grids scaled to 80x80px

## Installation

```bash
# Clone the repo
git clone https://github.com/katemptiness/claudy.git
cd claudy

# Install dependencies
pip install pyobjc pyobjc-framework-Quartz

# Run
python3 app.py
```

### Standalone app

```bash
pip install py2app
python setup.py py2app
open "dist/Claudy.app"
```

Requires macOS with Python 3.10+ and the Dock positioned at the bottom of the screen.

## Interactions

| Action | What happens |
|--------|-------------|
| Hover | Waves hello |
| Click | Happy bounce + sparkles + hearts |
| Double-click | Opens Claude.app |
| Drag & drop | Surprised face, falls back to Dock with gravity |
| Right-click | Context menu (Open Claude, Open Claude Code, Activities, Settings, About Claudy, Quit) |

## Schedule & Activities

Claudy follows a daily routine based on the selected schedule mode. The day is split into periods, and each period has its own mix of possible activities — chosen randomly by weighted probability.

### Day periods

| Period | Night Owl | Early Bird |
|--------|-----------|------------|
| Deep sleep | 4:00–11:00 | 22:00–6:00 |
| Morning | 11:00–13:00 | 6:00–8:00 |
| Day | 13:00–20:00 | 8:00–15:00 |
| Evening | 20:00–1:00 | 15:00–20:00 |
| Late night | 1:00–4:00 | 20:00–22:00 |

### What happens when

| Period | Behavior |
|--------|----------|
| **Deep sleep** | Sleeps continuously (zzz...) |
| **Morning** | Wakes up slowly — idle, walking, meditating, reading, occasional nap |
| **Day** | Most active — all 12 activities available: reading, coding, fishing, magic, painting, juggling, music, telescope, meditating, playing, summoning a friend. Walks around the Dock frequently |
| **Evening** | Calmer — reading, fishing, stargazing, music, meditating, summoning. Short naps possible |
| **Late night** | Winding down — reading, telescope, meditating, music. Naps more often |

Every 8–20 seconds in idle, Claudy rolls the dice and picks a new activity based on the current period's weights. During deep sleep, it just keeps snoozing.

### Activities

Each activity is a **phased animation** — a sequence of sprites, particles, and speech bubbles that plays out automatically:

| Activity | What happens | Particles |
|----------|-------------|-----------|
| Reading | Grabs a book, reads, reacts with excitement | Pages |
| Working | Opens laptop, types furiously, thinks, ships code | Code snippets, sparkles |
| Fishing | Casts a line, waits, pulls — catches fish, boots, or diamonds | Exclaims, sparkles |
| Magic | Waves a wand — conjures flowers, rainbows, butterflies, or poof | Varies by result |
| Sleeping | Nods off (nap or deep sleep depending on time) | Zzz |
| Playing | Bounces around happily | Notes |
| Music | Plays a tune | Notes |
| Painting | Sets up an easel, paints, admires the result | — |
| Telescope | Pulls out a telescope, gazes at the stars | Stars |
| Meditating | Sits quietly for a long time | Sparkles |
| Juggling | Juggles with claws | — |
| Summoning | Casts a spell, summons a blue friend crab, hangs out, says goodbye | Poof, hearts |

## Architecture

Built with Python + PyObjC, pure AppKit — no game frameworks, no SpriteKit, no Metal.

```
app.py               # Entry point, NSWindow, update loop, input handling
character.py          # State machine, phased animation engine
sprite_renderer.py    # CGContext pixel rendering pipeline
sprites/
  base.py             # Idle, blink, walk sprites
  activities.py       # 39 activity & reaction sprites
animations.py         # Bounce, shake, gravity drop
particles.py          # 14 particle types (sparkles, hearts, notes, zzz...)
speech.py             # Floating speech bubbles
schedule.py           # Owl/lark time-of-day behavior weights
system_events.py      # macOS event reactions (app launches, sleep/wake)
settings.py           # Settings persistence + UI (terminal, schedule, language)
phrases.py            # Bilingual phrase system (RU/EN)
config.py             # Palette, constants
```

## Settings

Right-click → Settings to configure:

| Setting | Options | Default |
|---------|---------|---------|
| Claude Code terminal | Terminal, iTerm2, Warp | Terminal |
| Schedule mode | Night Owl (sleep 4am–11am) / Early Bird (sleep 10pm–6am) | Night Owl |
| Language | Русский / English | English |
| Speech frequency | Often (10s) / Normal (1 min) / Rarely (10 min) / Very rarely (30 min) / Almost never (1 hr) | Normal |

Settings are saved to `~/.claudy/settings.json`.

Right-click → Activities to immediately trigger any activity (useful for previewing animations).

## Credits

Made by katemptiness & Claude Opus.

Inspired by [pet-clawd](https://github.com/getcompanion-ai/pet-clawd) (MIT).

## License

MIT
