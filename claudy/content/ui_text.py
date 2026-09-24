"""Bilingual text for Claudy's UI chrome: menus, settings, gifts window.

Claudy's own speech lives in phrases.py; this module holds the labels of the
windows and menus around it. Entries are (English, Russian) pairs.
"""

from claudy.content.phrases import get_language

_LABELS = {
    # Context menu
    "open_claude": ("Open Claude", "Открыть Claude"),
    "open_claude_code": ("Open Claude Code", "Открыть Claude Code"),
    "give_gift": ("Give a gift", "Подарить подарок"),
    "wait_a_bit": ("Wait a bit...", "Подожди немножко..."),
    "activities": ("Activities", "Активности"),
    "test_gift": ("Test Gift", "Тест подарка"),
    "gifts": ("Gifts", "Подарки"),
    "settings": ("Settings", "Настройки"),
    "about": ("About Claudy", "О Claudy"),
    "quit": ("Quit", "Выход"),

    # Settings window
    "terminal": ("Open Claude Code in:", "Открывать Claude Code в:"),
    "schedule": ("Schedule mode:", "Режим расписания:"),
    "language": ("Language:", "Язык / Language:"),
    "name": ("Your name:", "Ваше имя:"),
    "speech": ("Speech frequency:", "Частота фраз:"),
    "gift_dur": ("Gift duration:", "Время подарка:"),
    "gift_lim": ("Gifts per day:", "Подарков в день:"),
    "gift_cd": ("Gift cooldown:", "Кулдаун подарков:"),
    "height": ("Claudy's height:", "Высота Claudy:"),
    "height_below": ("Lower", "Ниже"),
    "height_dock": ("Dock", "Док"),
    "height_above": ("Higher", "Выше"),
    "height_unit": ("px", "пикс"),
    "dock_icons": ("Dock icons:", "Иконок в доке:"),
    "dock_icons_hint": ("count apps, folders & Trash",
                        "приложения, папки и корзина"),
    "dev": ("Developer mode", "Режим разработчика"),
    "save": ("Save", "Сохранить"),
    "title": ("Claudy — Settings", "Claudy — Настройки"),

    # Gifts window
    "gifts_title": ("Gifts", "Подарки"),
    "no_gifts": ("No gifts yet. I'll find something soon!",
                 "Пока нет подарков. Скоро найду что-нибудь!"),
}

# User-to-Claudy gifts offered in the context menu: (type, EN, RU)
GIFT_MENU = [
    ("flower", "Flower 🌸", "Цветок 🌸"),
    ("book", "Book 📖", "Книжку 📖"),
    ("song", "Song 🎵", "Песенку 🎵"),
    ("marshmallow", "Marshmallow 🍡", "Зефирку 🍡"),
    ("toy", "Toy 🧸", "Игрушку 🧸"),
]

# Settings option lists: (key, EN title, RU title)
SCHEDULE_OPTIONS = [
    ("owl", "Night Owl", "Сова"),
    ("lark", "Early Bird", "Жаворонок"),
]
SPEECH_OPTIONS = [
    ("10s", "Often (10s)", "Часто (10с)"),
    ("1m", "Normal (1 min)", "Обычно (1 мин)"),
    ("10m", "Rarely (10 min)", "Редко (10 мин)"),
    ("30m", "Very rarely (30 min)", "Оч. редко (30 мин)"),
    ("1h", "Almost never (1 hr)", "Почти никогда (1 ч)"),
]
GIFT_DURATION_OPTIONS = [
    ("10s", "10 sec", "10 сек"),
    ("1m", "1 min", "1 мин"),
    ("5m", "5 min", "5 мин"),
    ("15m", "15 min", "15 мин"),
    ("30m", "30 min", "30 мин"),
    ("1h", "1 hour", "1 час"),
]
GIFT_LIMIT_OPTIONS = [
    (1, "1", "1"),
    (3, "3", "3"),
    (5, "5", "5"),
    (10, "10", "10"),
    (0, "Unlimited", "Безлимит"),
]
GIFT_COOLDOWN_OPTIONS = [
    ("off", "No cooldown", "Без кулдауна"),
    ("1m", "1 min", "1 мин"),
    ("5m", "5 min", "5 мин"),
    ("10m", "10 min", "10 мин"),
    ("30m", "30 min", "30 мин"),
]
# Language names are shown in their own language, whatever the UI language.
LANGUAGE_OPTIONS = [("ru", "Русский"), ("en", "English")]

_GIFT_TYPE_NAMES = {
    "fish": ("Catch", "Улов"),
    "magic": ("Magic", "Магия"),
    "star": ("Star", "Звезда"),
    "shell": ("Shell", "Ракушка"),
    "test": ("Test", "Тест"),
}

_MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "ru": ["янв", "фев", "мар", "апр", "май", "июн",
           "июл", "авг", "сен", "окт", "ноя", "дек"],
}


def _is_en(lang=None):
    return (lang or get_language()) == "en"


def label(key, lang=None):
    """A UI label in the given (default: current) language."""
    en, ru = _LABELS[key]
    return en if _is_en(lang) else ru


def localized(options, lang=None):
    """(key, title) pairs of an option list in the given language."""
    idx = 1 if _is_en(lang) else 2
    return [(o[0], o[idx]) for o in options]


def about_text(toolkit):
    if _is_en():
        return ("A little pixel crab companion for your desktop.\n\n"
                "Made by katemptiness & Claude Opus\n"
                f"with love and {toolkit}.")
    return ("Маленький пиксельный краб-компаньон.\n\n"
            "Сделано katemptiness & Claude Opus\n"
            f"с любовью и {toolkit}.")


def gift_type_name(gift_type):
    en, ru = _GIFT_TYPE_NAMES.get(gift_type, ("Gift", "Подарок"))
    return en if _is_en() else ru


def gifts_header(count):
    """'3 gifts collected' / '3 подарка собрано'."""
    if _is_en():
        return f"{count} gift{'s' if count != 1 else ''} collected"
    if 11 <= count % 100 <= 19:
        noun = "подарков собрано"
    elif count % 10 == 1:
        noun = "подарок собран"
    elif 2 <= count % 10 <= 4:
        noun = "подарка собрано"
    else:
        noun = "подарков собрано"
    return f"{count} {noun}"


def format_date(date_str):
    """Format an ISO date ('2026-09-24') for the gifts window."""
    try:
        year, month, day = date_str.split("-")
        month_name = _MONTHS["en" if _is_en() else "ru"][int(month) - 1]
        if _is_en():
            return f"{month_name} {int(day)}, {year}"
        return f"{int(day)} {month_name} {year}"
    except (AttributeError, ValueError, IndexError):
        return date_str or ""
