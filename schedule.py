"""Time-of-day schedule — owl and lark modes."""

from datetime import datetime


def get_period(hour=None, mode=None):
    """Return the current day period name."""
    if hour is None:
        hour = datetime.now().hour
    if mode is None:
        from settings import Settings
        mode = Settings.shared().schedule

    if mode == "lark":
        if 22 <= hour or hour < 6:
            return "deep_sleep"
        elif 6 <= hour < 8:
            return "morning"
        elif 8 <= hour < 15:
            return "day"
        elif 15 <= hour < 20:
            return "evening"
        else:  # 20-22
            return "late_night"
    else:  # owl (default)
        if 4 <= hour < 11:
            return "deep_sleep"
        elif 11 <= hour < 13:
            return "morning"
        elif 13 <= hour < 20:
            return "day"
        elif 20 <= hour or hour < 1:
            return "evening"
        else:  # 1-4
            return "late_night"


# Activity weights by period.
# Higher weight = more likely to be chosen.
ACTIVITY_WEIGHTS = {
    "deep_sleep": {
        "sleeping": 1.0,
    },
    "morning": {
        "idle": 0.25,
        "walking": 0.28,
        "meditating": 0.2,
        "reading": 0.1,
        "sleeping": 0.1,
        "shell_collecting": 0.07,
    },
    "day": {
        "idle": 0.16,
        "walking": 0.16,
        "reading": 0.12,
        "working": 0.12,
        "magic": 0.07,
        "fishing": 0.07,
        "playing": 0.05,
        "painting": 0.04,
        "juggling": 0.03,
        "music": 0.04,
        "telescope": 0.02,
        "meditating": 0.02,
        "summoning": 0.04,
        "sandcastle": 0.03,
        "shell_collecting": 0.03,
    },
    "evening": {
        "idle": 0.07,
        "walking": 0.07,
        "reading": 0.14,
        "fishing": 0.1,
        "telescope": 0.1,
        "music": 0.08,
        "meditating": 0.08,
        "sleeping": 0.08,
        "summoning": 0.04,
        "campfire": 0.08,
        "sandcastle": 0.05,
        "shell_collecting": 0.05,
        "candle": 0.06,
    },
    "late_night": {
        "idle": 0.04,
        "reading": 0.16,
        "telescope": 0.16,
        "meditating": 0.12,
        "sleeping": 0.24,
        "music": 0.08,
        "campfire": 0.10,
        "candle": 0.10,
    },
}


def get_weights():
    """Return activity weights for the current time of day."""
    period = get_period()
    return ACTIVITY_WEIGHTS[period]
