# Claudy

<p align="center">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux-blue" alt="macOS | Linux">
  <img src="https://img.shields.io/badge/python-3.10+-yellow" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
</p>

A tiny pixel-art crab companion that lives on your Dock. It reads books, catches fish, does magic, writes code, and generally goes about its little crab life — all on its own. Formerly known as Little Claude.

<p align="center">
  <img src="screens/screen1.png" width="280" alt="Claudy juggling">
  <img src="screens/screen2.png" width="280" alt="Claudy idle">
  <img src="screens/screen3.png" width="280" alt="Claudy on the Dock">
</p>

**Claudy is not a tamagotchi.** It has no needs, no health bars, no demands. It's a self-sufficient creature with its own schedule, moods, and activities. You're just an observer — and sometimes a friend.

## What it does

- Wanders along the Dock, performing 12 different activities: reading, fishing, magic, coding, sleeping, playing, painting, stargazing, meditating, juggling, listening to music, and summoning a friend
- Follows a configurable schedule — night owl (default) or early bird mode
- Reacts to clicks (sparkles → hearts!), hover (waves hello), and drag-and-drop (macOS: surprise + gravity bounce)
- Mirrors your activity — open a terminal or code editor and the crab starts coding; open Spotify and it listens to music
- Notices when you launch apps and comments on them (remembers how many times you opened the same app today)
- Sleeps when your machine sleeps, greets you when it wakes up
- Gives you gifts — catches a fish? Finds a star? Might leave it on the Dock for you
- Gradually notices you — click enough and Claudy starts using your name, showing hearts, and saying personal things
- Remembers how many days you've been together and occasionally mentions it
- Says things in cute speech bubbles — in Russian or English (configurable)
- All rendered as pixel art: 16x16 sprite grids scaled to 80x80px

## Installation

### macOS

```bash
git clone https://github.com/katemptiness/claudy.git
cd claudy
pip install pyobjc pyobjc-framework-Quartz
python3 app.py
```

#### Standalone app (macOS)

```bash
pip install py2app
python setup.py py2app
open "dist/Claudy.app"
```

Requires macOS with Python 3.10+ and the Dock positioned at the bottom of the screen.

### Linux (Ubuntu 24.04+)

```bash
git clone https://github.com/katemptiness/claudy.git
cd claudy

# GTK3, PyGObject, and Cairo are typically pre-installed on Ubuntu.
# If not: sudo apt install python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-3.0
python3 app.py    # or /usr/bin/python3 if using system Python
```

Requires Python 3.10+, GTK3, and a bottom panel/dock. Tested on Ubuntu 24.04 LTS (GNOME/Wayland + X11).

## Interactions

| Action | What happens |
|--------|-------------|
| Hover | Waves hello |
| Click | Happy bounce + sparkles (before attachment) or hearts (after) |
| Click (with gift) | Collects the gift — Claudy reacts happily |
| Double-click | Opens Claude.app (macOS) / claude.ai (Linux) |
| Drag & drop | Surprised face, falls back to Dock with gravity (macOS only) |
| Right-click | Context menu (Open Claude, Open Claude Code, Settings, About Claudy, Quit) |

## Relationships

Claudy doesn't demand attention — but it notices when you're there.

### Attachment

There's an invisible threshold: **5 clicks per day** (resets each session). Before the threshold, clicks produce sparkles. After it, you unlock:

- **Hearts** instead of sparkles on click
- **Personal phrases** that use your name ("how's it going, Kate?", "i like spending time with Kate :3")
- **Sleep/wake greetings** ("falling asleep, Kate... 💤", "that was a nice nap :3")

If you don't click — nothing changes. Claudy is perfectly happy on its own.

### Gifts

During some activities, Claudy may find something and leave it on the Dock for you:

| Activity | Gift | Chance |
|----------|------|--------|
| Fishing | Caught fish, pufferfish, diamond, star | ~30% on good catch |
| Magic | Flower, butterfly, rainbow | ~20% on successful spell |
| Telescope | Names a star after you | ~20% per session |

When a gift appears, Claudy pauses activities and announces it ("look what i found!", "this is for you! :3"). Click Claudy to collect. If you don't collect in time, Claudy keeps it ("ok, keeping it for myself :p").

### Memory

Claudy remembers things in `~/.claudy/memory.json`:

- **Days together** — occasionally says "we've been together for 47 days" (special phrases for milestones: 10, 50, 100...)
- **App launches** — "Spotify for the 3rd time today :)"
- **Gifts** — keeps a history of all gifts given and collected
- **Claude.ai easter eggs** — sometimes quotes claude.ai headlines ("golden hour thinking", "ready when you are, Kate")

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

Built with Python — shared core logic with platform-specific backends. No game frameworks.

```
app.py                        # Cross-platform entry point (detects OS)

# Shared core (platform-independent)
character.py                  # State machine, phased animation engine
sprites/
  base.py                     # Idle, blink, walk sprites
  activities.py               # 39 activity & reaction sprites
animations.py                 # Bounce, shake, gravity drop
particles.py                  # 14 particle types (sparkles, hearts, notes, zzz...)
schedule.py                   # Owl/lark time-of-day behavior weights
settings.py                   # Settings persistence (JSON)
phrases.py                    # Bilingual phrase system (RU/EN) + relationship phrases
memory.py                     # Relationship memory (clicks, days, gifts, app launches)
config.py                     # Palette, constants

# macOS backend (PyObjC / AppKit / Quartz)
backends/macos/
  app.py                      # NSWindow, CALayer, update loop, input, gifts
  renderer.py                 # CGContext pixel rendering
  speech.py                   # NSWindow speech bubbles
  events.py                   # NSWorkspace notifications (app launches, sleep/wake)
  settings_ui.py              # AppKit settings window

# Linux backend (GTK3 / PyGObject / Cairo)
backends/linux/
  app.py                      # GTK3 windows, Cairo rendering, GLib main loop
  renderer.py                 # Cairo pixel rendering
  speech.py                   # GTK3 speech bubbles
  events.py                   # D-Bus logind + process-based app detection
  settings_ui.py              # GTK3 settings dialog
```

## Settings

Right-click → Settings to configure:

| Setting | Options | Default |
|---------|---------|---------|
| Claude Code terminal | Terminal / iTerm2 / Warp (macOS), gnome-terminal / kitty / alacritty (Linux) | Terminal (macOS) / gnome-terminal (Linux) |
| Schedule mode | Night Owl / Early Bird | Night Owl |
| Language | Русский / English | English |
| Your name | Text field | — |
| Speech frequency | Often (10s) / Normal (1 min) / Rarely / Very rarely / Almost never | Normal |
| Gift duration | 10s / 1 min / 5 min / 15 min / 30 min / 1 hr | 5 min |
| Gifts per day | 1 / 3 / 5 / 10 / Unlimited | 3 |
| Developer mode | Checkbox | Off |

Settings UI is fully localized — labels and options appear in the selected language.

Settings are saved to `~/.claudy/settings.json`. Relationship memory is saved to `~/.claudy/memory.json`.

Developer mode enables an Activities submenu for previewing animations and testing gifts.

## Credits

Made by katemptiness & Claude Opus.

Inspired by [pet-clawd](https://github.com/getcompanion-ai/pet-clawd) (MIT).

## License

MIT
