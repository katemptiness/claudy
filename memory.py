"""Memory system — tracks relationship data (clicks, days, gifts)."""

import json
import os
from datetime import date

MEMORY_DIR = os.path.expanduser("~/.claudy")
MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.json")

ATTACHMENT_THRESHOLD = 5  # clicks per day to unlock personal phrases/hearts


class Memory:
    """Persistent relationship memory — singleton."""

    _instance = None

    @classmethod
    def shared(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._data = {
            "first_launch": None,
            "total_days": 0,
            "today": {
                "date": None,
                "clicks": 0,
                "app_launches": {},
                "days_phrase_shown": False,
            },
            "gifts": [],
        }
        self._load()
        self._check_new_day()
        # Reset per-session state — each launch is a fresh start
        self._data["today"]["clicks"] = 0
        self._data["today"]["app_launches"] = {}
        self._data["gifts"] = []
        self.save()

    def _load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge saved data, keeping defaults for missing keys
                for k in self._data:
                    if k in saved:
                        self._data[k] = saved[k]
                # Ensure today has all expected keys
                today = self._data["today"]
                today.setdefault("clicks", 0)
                today.setdefault("app_launches", {})
                today.setdefault("days_phrase_shown", False)
            except (json.JSONDecodeError, IOError):
                pass

    def save(self):
        try:
            os.makedirs(MEMORY_DIR, exist_ok=True)
            content = json.dumps(self._data, indent=2, ensure_ascii=False)
            tmp = MEMORY_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, MEMORY_FILE)
        except Exception:
            # Log but never crash — memory is best-effort
            import traceback
            try:
                with open(os.path.join(MEMORY_DIR, "error.log"), "a") as ef:
                    traceback.print_exc(file=ef)
            except Exception:
                pass

    def _check_new_day(self):
        """Reset daily counters if the date has changed."""
        today_str = date.today().isoformat()

        if self._data["first_launch"] is None:
            self._data["first_launch"] = today_str

        if self._data["today"].get("date") != today_str:
            # New day
            if self._data["today"].get("date") is not None:
                self._data["total_days"] += 1
            elif self._data["first_launch"] == today_str:
                # Very first launch ever
                self._data["total_days"] = 1
            self._data["today"] = {
                "date": today_str,
                "clicks": 0,
                "app_launches": {},
                "days_phrase_shown": False,
            }
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

    def record_app_launch(self, bundle_id):
        """Record an app launch. Returns the count for today."""
        self._check_new_day()
        launches = self._data["today"]["app_launches"]
        launches[bundle_id] = launches.get(bundle_id, 0) + 1
        self.save()
        return launches[bundle_id]

    def get_app_launches_today(self, bundle_id):
        self._check_new_day()
        return self._data["today"]["app_launches"].get(bundle_id, 0)

    # --- Days ---

    def get_total_days(self):
        self._check_new_day()
        return self._data["total_days"]

    def is_milestone_day(self):
        days = self.get_total_days()
        return days in (10, 25, 50, 100, 200, 365, 500, 1000)

    def days_phrase_shown_today(self):
        self._check_new_day()
        return self._data["today"].get("days_phrase_shown", False)

    def mark_days_phrase_shown(self):
        self._data["today"]["days_phrase_shown"] = True
        self.save()

    # --- Gifts ---

    def get_pending_gift(self):
        """Return the first uncollected gift, or None."""
        for gift in self._data["gifts"]:
            if not gift.get("collected", False):
                return gift
        return None

    def add_gift(self, gift_type, emoji, name=None, collected=False):
        """Add a new gift. Returns the gift dict."""
        from gift_stories import random_story_id
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
        for gift in self._data["gifts"]:
            if not gift.get("collected", False):
                gift["collected"] = True
                self.save()
                return gift
        return None

    def get_collected_gifts(self):
        """Return all collected gifts, newest first. Backfills missing story_id."""
        from gift_stories import random_story_id
        changed = False
        result = []
        for gift in self._data["gifts"]:
            if gift.get("collected", False):
                if "story_id" not in gift:
                    gift["story_id"] = random_story_id(gift.get("type", "fish"))
                    changed = True
                result.append(gift)
        if changed:
            self.save()
        result.reverse()
        return result
