"""Memory system — tracks relationship data (clicks, days, gifts)."""

import json
import os
from datetime import date

from claudy.config import DATA_DIR
from claudy.content.gift_stories import random_story_id
from claudy.log import log

MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")

ATTACHMENT_THRESHOLD = 5  # clicks per day to unlock personal phrases/hearts
MILESTONE_DAYS = (10, 25, 50, 100, 200, 365, 500, 1000)


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
    counter and gifts reset. Only the very first launch date survives.
    """

    _instance = None

    @classmethod
    def shared(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        today_str = date.today().isoformat()
        first_launch = self._load_first_launch() or today_str
        self._data = {
            "first_launch": first_launch,
            "total_days": 1,
            "today": _fresh_day(today_str),
            "gifts": [],
        }
        self.save()

    @staticmethod
    def _load_first_launch():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("first_launch")
        except (OSError, json.JSONDecodeError, AttributeError):
            return None

    def save(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            content = json.dumps(self._data, indent=2, ensure_ascii=False)
            tmp = MEMORY_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, MEMORY_FILE)
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

    def get_app_launches_today(self, app_id):
        self._check_new_day()
        return self._data["today"]["app_launches"].get(app_id, 0)

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

    def count_session_gifts(self, gift_type):
        """Count gifts of a given type this session (collected + pending)."""
        return sum(1 for g in self._data["gifts"] if g["type"] == gift_type)

    def count_gifts_today(self):
        """Gifts Claudy offered today, not counting named stars."""
        today = date.today().isoformat()
        return sum(1 for g in self._data["gifts"]
                   if g["date"] == today and g["type"] != "star")

    def get_collected_gifts(self):
        """Return all collected gifts, newest first."""
        return [g for g in reversed(self._data["gifts"]) if g["collected"]]
