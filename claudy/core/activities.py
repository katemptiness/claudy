"""Activity scripts: phased animations, reactions and random outcomes.

Everything here is immutable data. The Character copies an activity's phase
list when it starts one, so per-run tweaks (the catch of the day, a gifted
marshmallow, which games to play with a friend) never leak into the next run.
"""

import random
from dataclasses import dataclass
from typing import Optional

from claudy.core.animations import Juggle


@dataclass(frozen=True)
class Phase:
    """A single phase within an activity sequence."""

    frames: tuple
    interval_ms: int = 500          # time per frame when there are several
    duration_ms: int = 2000
    duration_max_ms: Optional[int] = None  # if set, duration is randomized
    message: Optional[str] = None   # phrase key (translated when shown)
    particle: Optional[str] = None
    particle_interval_ms: int = 1000
    bounce: bool = False
    shake: bool = False
    special: Optional[str] = None   # hook run on entry, e.g. "cast_magic"

    def __post_init__(self):
        object.__setattr__(self, "frames", tuple(self.frames))

    def pick_duration(self):
        if self.duration_max_ms:
            return random.uniform(self.duration_ms, self.duration_max_ms)
        return self.duration_ms


ACTIVITIES = {
    "reading": (
        Phase(["read_a"], 500, 800, message="берёт книжку..."),
        Phase(["read_a", "read_b"], 600, 60000, duration_max_ms=120000,
              message="читает...", particle="page", particle_interval_ms=3000),
        Phase(["read_react"], 200, 1200, message="о! интересно!",
              particle="exclaim", bounce=True),
        Phase(["read_a", "read_b"], 600, 60000, duration_max_ms=120000,
              message="читает дальше...", particle="page", particle_interval_ms=3000),
        Phase(["idle"], 500, 1500, message="закрыл книгу"),
    ),
    "sleeping": (
        Phase(["sleep_transition"], 500, 1000),
        Phase(["sleep_a", "sleep_b"], 800, 15000,
              particle="zzz", particle_interval_ms=2000),
    ),
    "magic": (
        Phase(["magic_hold"], 500, 1000, message="достаёт палочку..."),
        Phase(["magic_raise"], 300, 1200, message="замахивается...", bounce=True),
        Phase(["magic_cast"], 150, 800, message="✨ ВЗМАХ!",
              shake=True, special="cast_magic"),
        Phase(["magic_done"], 500, 2500),
        Phase(["idle"], 500, 1000),
    ),
    "working": (
        Phase(["work_a"], 400, 800, message="открывает ноутбук..."),
        Phase(["work_a", "work_b"], 180, 60000, duration_max_ms=100000,
              message="тук-тук-тук...", particle="code", particle_interval_ms=1500),
        Phase(["work_think"], 500, 5000, duration_max_ms=15000,
              message="хмм...", particle="question", particle_interval_ms=2000),
        Phase(["work_a", "work_b"], 150, 60000, duration_max_ms=100000,
              message="ПИШЕТ КОД!!", particle="code", particle_interval_ms=800,
              shake=True),
        Phase(["magic_done"], 500, 3000, message="готово! ✨",
              particle="sparkle", particle_interval_ms=400),
        Phase(["idle"], 500, 1000),
    ),
    "fishing": (
        Phase(["fish_wait"], 500, 800, message="забрасывает удочку..."),
        Phase(["fish_wait", "fish_wait_b"], 800, 3500, message="ждёт...",
              particle="zzz", particle_interval_ms=1500),
        Phase(["fish_bite"], 120, 1000, message="❗ клюёт!!",
              particle="exclaim", particle_interval_ms=600, shake=True),
        Phase(["fish_pull", "fish_bite"], 150, 1200, message="тянет!!!",
              shake=True),
        Phase(["fish_happy"], 500, 2500, special="fish_reveal"),
        Phase(["idle"], 500, 1000),
    ),
    "playing": (
        Phase(["play_a", "play_b"], 200, 4000, message="прыгает!",
              particle="note", particle_interval_ms=500, special="play_jump"),
        Phase(["idle"], 500, 1000),
    ),
    "music": (
        Phase(["music_a", "music_b"], 400, 5000, message="♪♫♬",
              particle="note", particle_interval_ms=800),
        Phase(["idle"], 500, 1000),
    ),
    "painting": (
        Phase(["paint_a"], 500, 1500, message="ставит мольберт..."),
        Phase(["paint_a", "paint_b"], 400, 20000, duration_max_ms=30000,
              message="рисует..."),
        Phase(["paint_c"], 500, 2500, message="хмм... неплохо!"),
        Phase(["idle"], 500, 1000),
    ),
    "telescope": (
        Phase(["telescope_a"], 500, 1000, message="достаёт телескоп..."),
        Phase(["telescope_a", "telescope_b"], 600, 4000, message="космос...",
              particle="star", particle_interval_ms=1500),
        Phase(["idle"], 500, 1000, special="star_gaze"),
    ),
    "meditating": (
        Phase(["meditate_a"], 500, 120000, duration_max_ms=300000,
              message="ом...", particle="sparkle", particle_interval_ms=3000),
        Phase(["idle"], 500, 1000),
    ),
    "juggling": (
        # Claudy flicks a claw up on every throw (see animations.Juggle)
        Phase(["juggle_toss", "juggle_catch"], Juggle.BEAT_MS // 2, 4000,
              message="жонглирует!", special="juggle"),
        Phase(["idle"], 500, 1000),
    ),
    "summoning": (
        Phase(["magic_hold"], 500, 1000, message="достаёт палочку..."),
        Phase(["magic_raise"], 300, 1200, message="кого бы призвать...",
              bounce=True),
        # summon_friend appends the hangout (FRIEND_ACTIVITY_POOL) and goodbye
        Phase(["magic_cast"], 150, 800, message="✨ ПРИЗЫВ!",
              shake=True, special="summon_friend"),
    ),
    "campfire": (
        Phase(["campfire_a", "campfire_b"], 600, 8000,
              message="разжёг костёр!", particle="flame",
              particle_interval_ms=1000),
        Phase(["campfire_a", "campfire_b"], 600, 20000, duration_max_ms=40000,
              message="тепло...", particle="flame", particle_interval_ms=2500),
        Phase(["campfire_a", "campfire_b"], 600, 5000,
              message="люблю смотреть на огонь...", particle="flame",
              particle_interval_ms=2500),
        Phase(["campfire_roast"], 500, 5000, message="жарит зефирку!"),
        Phase(["campfire_done"], 500, 3000, message="вкусно! :3",
              particle="heart", particle_interval_ms=800, bounce=True),
        Phase(["idle"], 500, 1000),
    ),
    "sandcastle": (
        Phase(["sand_a"], 500, 2000, message="строит замок..."),
        Phase(["sand_a", "sand_b"], 500, 4000, duration_max_ms=6000,
              message="лепит..."),
        Phase(["sand_c"], 500, 2500, special="sand_result"),
        Phase(["idle"], 500, 1000),
    ),
    "shell_collecting": (
        Phase(["walk_a", "walk_b"], 250, 4000, duration_max_ms=6000,
              special="shell_search"),
        Phase(["shell_look"], 500, 2000),
        Phase(["shell_find"], 300, 1500, message="о! нашёл!",
              particle="exclaim", bounce=True),
        Phase(["shell_pick"], 500, 1500, message="подбирает..."),
        Phase(["shell_admire"], 500, 3000, message="какая красивая ракушка!",
              particle="sparkle", particle_interval_ms=600,
              special="shell_gift_chance"),
        Phase(["idle"], 500, 1000),
    ),
    "candle": (
        Phase(["lantern_light"], 500, 2000, message="зажигает свечку..."),
        Phase(["lantern_a", "lantern_b"], 800, 15000, duration_max_ms=30000,
              message="огонёк мерцает...", particle="sparkle",
              particle_interval_ms=5000),
        Phase(["lantern_a", "lantern_b"], 800, 15000, duration_max_ms=40000,
              message="так спокойно...", particle="sparkle",
              particle_interval_ms=5000),
        Phase(["lantern_a", "lantern_b"], 800, 5000,
              message="можно так сидеть вечно..."),
        Phase(["idle"], 500, 1000),
    ),
}

# Not picked at random: played on launch and when the computer wakes up.
# The last phase's message is filled in by Character.wake_up().
WAKING = (
    Phase(["sleep_a"], 500, 1000),
    Phase(["blink"], 500, 500),
    Phase(["idle"], 500, 1500),
)

# How many most-recent activities to exclude from the next random pick
RECENT_ACTIVITY_BLOCK = 2

# Together-activities for a summoned friend; 2-3 are picked per visit.
FRIEND_ACTIVITY_POOL = {
    "walk": (
        Phase(["walk_a", "walk_b"], 200, 6000, duration_max_ms=10000,
              special="friend_walk_start"),
        Phase(["idle"], 500, 2000, special="friend_walk_stop"),
    ),
    "play": (
        Phase(["play_a", "play_b"], 200, 4000, bounce=True,
              special="friend_play_bounce",
              particle="note", particle_interval_ms=600),
    ),
    "sit": (
        Phase(["idle"], 500, 5000, duration_max_ms=8000,
              special="friend_sit",
              particle="star", particle_interval_ms=2500),
    ),
    "chat": (
        Phase(["happy"], 500, 3000, special="friend_chat"),
        Phase(["idle"], 500, 2000, special="friend_chat_reply"),
    ),
}

FRIEND_GOODBYE = (
    Phase(["happy"], 500, 2500, special="friend_bye"),
    Phase(["idle"], 500, 2000, special="friend_gone"),
)

# Frame cycles the friend plays while walking or playing along
FRIEND_ANIMATIONS = {
    "walk": ("walk_a", "walk_b"),
    "play": ("play_a", "play_b"),
}
FRIEND_FRAME_MS = 200


@dataclass(frozen=True)
class Reaction:
    """A short response to the user. `sprites` is a list of
    (show_until_ms, sprite) pairs; the last one lasts until the end."""

    duration_ms: int
    sprites: tuple
    bounce: bool = False
    hearts: bool = False  # keep puffing hearts while it lasts

    def sprite_at(self, elapsed_ms):
        for until, sprite in self.sprites[:-1]:
            if elapsed_ms < until:
                return sprite
        return self.sprites[-1][1]


REACTIONS = {
    "happy": Reaction(2000, ((None, "happy"),), bounce=True),
    "happy_love": Reaction(3000, ((1500, "happy"), (None, "love")),
                           bounce=True, hearts=True),
    "wave": Reaction(1500, ((None, "wave"),)),
    "surprise": Reaction(1000, ((None, "surprise"),)),
    "gift_received": Reaction(
        3000, ((500, "surprise"), (1500, "happy"), (None, "love")),
        bounce=True, hearts=True),
}
REACTION_HEART_INTERVAL_MS = 400


# --- Random outcomes ---

CATCHES = (
    {"emoji": "🐟", "name": "рыбка!", "good": True, "particles": "sparkle"},
    {"emoji": "🐡", "name": "фугу!!", "good": True, "particles": "sparkle"},
    {"emoji": "👢", "name": "ботинок...", "good": False, "particles": "sweat"},
    {"emoji": "🌿", "name": "водоросли", "good": False, "particles": "sweat"},
    {"emoji": "💎", "name": "АЛМАЗ!!", "good": True, "particles": "heart"},
    {"emoji": "📦", "name": "коробка?!", "good": False, "particles": "question"},
    {"emoji": "⭐", "name": "звезда!!!", "good": True, "particles": "star"},
    {"emoji": "🧦", "name": "носок.", "good": False, "particles": "sweat"},
)

# gift_emoji: what Claudy may leave for the user (None: nothing to give)
MAGIC_RESULTS = (
    {"text": "букет! 💐", "particles": "flower", "gift_emoji": "🌸"},
    {"text": "радуга! 🌈", "particles": "rainbow", "gift_emoji": "🌈"},
    {"text": "звездопад! ⭐", "particles": "star", "gift_emoji": "⭐"},
    {"text": "бабочка! 🦋", "particles": "butterfly", "gift_emoji": "🦋"},
    {"text": "пуф! 💨", "particles": "poof", "gift_emoji": None},
)

# Chances that an activity ends with a gift for the user (when attached)
MAGIC_GIFT_CHANCE = 0.2
FISH_GIFT_CHANCE = 0.3
SHELL_GIFT_CHANCE = 0.1
STAR_NAMING_CHANCE = 0.1
SANDCASTLE_SUCCESS_CHANCE = 0.7
