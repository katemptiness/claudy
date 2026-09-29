"""Memory system — tracks relationship data (clicks, days, gifts)."""

import os
from datetime import date

from claudy.config import DATA_DIR
from claudy.content.gift_stories import random_story_id
from claudy.core.settings import read_json, write_json_atomic
from claudy.log import log

MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")

ATTACHMENT_THRESHOLD = 5  # clicks per day to unlock personal phrases/hearts
# How many activities back Claudy's dreams reach. Deliberately a rolling list
# and not a per-day count: he sleeps deepest in the small hours, and a counter
# that reset at midnight would only ever hold the hour before he dozed off.
ACTIVITY_LOG = 40
MILESTONE_DAYS = (10, 25, 50, 100, 200, 365, 500, 1000)


def _saved_star(saved):
    """The star named in an earlier session, checked, or None.

    It is the one thing in the file meant to last for good, so a hand edit
    that broke it must not crash every night frame that places it, nor block
    naming a real one.
    """
    star = saved.get("star")
    if not (isinstance(star, dict) and isinstance(star.get("name"), str)):
        star = _star_from_gifts(saved.get("gifts"))
        if star is None:
            return None
    named_on = star.get("date")
    return {"name": star["name"],
            "date": named_on if isinstance(named_on, str) else None}


def _star_from_gifts(gifts):
    """The newest star in the gift list, or None.

    Builds before the star had a key of its own kept it only as a gift,
    and a crash between recording the gift and the star leaves the same
    shape, so the gift is where such a star is found.
    """
    if not isinstance(gifts, list):
        return None
    for gift in reversed(gifts):
        if isinstance(gift, dict) and gift.get("type") == "star":
            name = gift.get("name", "")     # no name when the user had none
            if not isinstance(name, str):
                return None
            return {"name": name, "date": gift.get("date")}
    return None


def _fresh_day(today_str):
    return {
        "date": today_str,
        "clicks": 0,
        "app_launches": {},
        "days_phrase_shown": False,
    }


class Memory:
    """Persistent relationship memory. Use Memory.shared().

    Each launch starts a fresh session: clicks, app launches, the days
    counter and gifts reset. Only two things survive: the very first launch
    date, and the star Claudy named after the user — that one hangs in the
    sky for good, so it has to outlive a rebuild.
    """

    _instance = None

    @classmethod
    def shared(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        today_str = date.today().isoformat()
        # An unreadable file is set aside rather than overwritten by the
        # save below: the star in it can only be recovered by hand
        saved = read_json(MEMORY_FILE)
        first_launch = saved.get("first_launch")
        if not (isinstance(first_launch, str) and first_launch):
            first_launch = today_str
        self._data = {
            "first_launch": first_launch,
            "total_days": 1,
            "today": _fresh_day(today_str),
            "gifts": [],
            "activities": [],
            "star": _saved_star(saved),
        }
        self.save()

    def save(self):
        try:
            write_json_atomic(MEMORY_FILE, self._data)
        except Exception:
            # Memory is best-effort — never crash over it
            log.exception("failed to save memory")

    def _check_new_day(self):
        """Bump the days counter if the date changed during the session."""
        today_str = date.today().isoformat()
        if self._data["today"]["date"] != today_str:
            self._data["total_days"] += 1
            self._data["today"] = _fresh_day(today_str)
            self.save()

    # --- Clicks ---

    def record_click(self):
        self._check_new_day()
        self._data["today"]["clicks"] += 1
        self.save()

    def get_clicks_today(self):
        self._check_new_day()
        return self._data["today"]["clicks"]

    def is_attached(self):
        """True if user clicked enough today to unlock personal phrases."""
        return self.get_clicks_today() >= ATTACHMENT_THRESHOLD

    # --- App launches ---

    def record_app_launch(self, app_id):
        """Record an app launch. Returns the count for today."""
        self._check_new_day()
        launches = self._data["today"]["app_launches"]
        launches[app_id] = launches.get(app_id, 0) + 1
        self.save()
        return launches[app_id]

    # --- Days ---

    def get_total_days(self):
        self._check_new_day()
        return self._data["total_days"]

    def is_milestone_day(self):
        return self.get_total_days() in MILESTONE_DAYS

    def days_phrase_shown_today(self):
        self._check_new_day()
        return self._data["today"]["days_phrase_shown"]

    def mark_days_phrase_shown(self):
        self._data["today"]["days_phrase_shown"] = True
        self.save()

    # --- Gifts ---

    def get_pending_gift(self):
        """Return the first uncollected gift, or None."""
        for gift in self._data["gifts"]:
            if not gift["collected"]:
                return gift
        return None

    def add_gift(self, gift_type, emoji, name=None, collected=False):
        """Add a new gift. Returns the gift dict."""
        gift = {
            "type": str(gift_type),
            "emoji": str(emoji),
            "date": date.today().isoformat(),
            "collected": collected,
            "story_id": random_story_id(gift_type),
        }
        if name:
            gift["name"] = name
        self._data["gifts"].append(gift)
        self.save()
        return gift

    def collect_gift(self):
        """Mark the pending gift as collected."""
        gift = self.get_pending_gift()
        if gift:
            gift["collected"] = True
            self.save()
        return gift

    def discard_pending_gift(self):
        """Remove the pending gift without collecting it (expired unclaimed).

        Discarded gifts never appear in the collection and don't count
        toward the daily limit, so Claudy will try offering again later.
        """
        gift = self.get_pending_gift()
        if gift:
            self._data["gifts"].remove(gift)
            self.save()
        return gift

    def count_gifts_today(self):
        """Gifts Claudy offered today, not counting named stars."""
        today = date.today().isoformat()
        return sum(1 for g in self._data["gifts"]
                   if g["date"] == today and g["type"] != "star")

    # --- What Claudy has been doing ---

    def log_activity(self, name):
        """Note what Claudy just started, for the things he dreams about.

        Runs of the same activity count once. Deep sleep itself loops in
        place and is logged once, but "sleeping" is all Claudy can choose
        then, so every hover or click that wakes him in the night, and every
        time the computer sleeps and wakes, sends him back to it. Without
        this, a night of the mouse passing over the Dock would fill the log
        with "sleeping" and push out everything he could dream of — just
        when he sleeps long enough to dream.
        """
        log = self._data["activities"]
        if log and log[-1] == name:
            return
        log.append(name)
        del log[:-ACTIVITY_LOG]
        self.save()

    def recent_activities(self):
        """The last few things Claudy did, oldest first, repeats included."""
        return list(self._data["activities"])

    # --- The named star ---

    def name_star(self, name):
        """Remember the star Claudy named after the user.

        The star also goes into the collection as a gift, like everything
        else Claudy gives away; this is the copy that stays in the sky, so
        it is stored on its own and survives a relaunch.
        """
        self._data["star"] = {"name": name or "",
                              "date": date.today().isoformat()}
        self.save()

    def get_star(self):
        """The named star, or None if Claudy hasn't named one yet."""
        return self._data.get("star")

    def get_collected_gifts(self):
        """Return all collected gifts, newest first."""
        return [g for g in reversed(self._data["gifts"]) if g["collected"]]
