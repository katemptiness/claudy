"""Time-of-day schedule — night owl mode."""

from datetime import datetime


def get_period(hour=None):
    """Return the current day period name."""
    if hour is None:
        hour = datetime.now().hour

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
        "idle": 0.3,
        "walking": 0.3,
        "meditating": 0.2,
        "reading": 0.1,
        "sleeping": 0.1,
    },
    "day": {
        "idle": 0.2,
        "walking": 0.2,
        "reading": 0.12,
        "working": 0.12,
        "magic": 0.08,
        "fishing": 0.08,
        "playing": 0.05,
        "painting": 0.04,
        "juggling": 0.03,
        "music": 0.04,
        "telescope": 0.02,
        "meditating": 0.02,
    },
    "evening": {
        "idle": 0.1,
        "walking": 0.1,
        "reading": 0.2,
        "fishing": 0.15,
        "telescope": 0.15,
        "music": 0.1,
        "meditating": 0.1,
        "sleeping": 0.1,
    },
    "late_night": {
        "idle": 0.05,
        "reading": 0.2,
        "telescope": 0.2,
        "meditating": 0.15,
        "sleeping": 0.3,
        "music": 0.1,
    },
}


def get_weights():
    """Return activity weights for the current time of day."""
    period = get_period()
    return ACTIVITY_WEIGHTS[period]
