# Little Claude

<p align="center">
  <img src="https://img.shields.io/badge/platform-macOS-blue" alt="macOS">
  <img src="https://img.shields.io/badge/python-3.10+-yellow" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
</p>

A tiny pixel-art crab companion that lives on your macOS Dock. It reads books, catches fish, does magic, writes code, and generally goes about its little crab life — all on its own.

**Little Claude is not a tamagotchi.** It has no needs, no health bars, no demands. It's a self-sufficient creature with its own schedule, moods, and activities. You're just an observer — and sometimes a friend.

## What it does

- Wanders along the Dock, performing 13 different activities: reading, fishing, magic, coding, sleeping, playing, painting, stargazing, meditating, juggling, and listening to music
- Follows a night-owl schedule — sleeps from 4am to 11am, most active during the day, calms down in the evening
- Reacts to clicks (sparkles + hearts!), hover (waves hello), and drag-and-drop (surprise + gravity bounce)
- Notices when you launch apps and comments on them
- Sleeps when your Mac sleeps, yawns when it wakes up
- Occasionally says things in cute speech bubbles (in Russian)
- All rendered as pixel art: 16x16 sprite grids scaled to 80x80px

## Installation

```bash
# Clone the repo
git clone https://github.com/katemptiness/little-Claude.git
cd little-Claude

# Install dependencies
pip install pyobjc pyobjc-framework-Quartz

# Run
python3 app.py
```

Requires macOS with Python 3.10+ and the Dock positioned at the bottom of the screen.

## Interactions

| Action | What happens |
|--------|-------------|
| Hover | Waves hello |
| Click | Happy bounce + sparkles + hearts |
| Double-click | Opens Claude.app |
| Drag & drop | Surprised face, falls back to Dock with gravity |
| Right-click | Context menu (Open Claude, About, Quit) |

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
schedule.py           # Night-owl time-of-day behavior weights
system_events.py      # macOS event reactions (app launches, sleep/wake)
config.py             # Palette, constants
```

## Credits

Inspired by [pet-clawd](https://github.com/getcompanion-ai/pet-clawd) (MIT).

Built with love, PyObjC, and Claude.

## License

MIT
