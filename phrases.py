"""Bilingual phrase system — Russian and English."""

_current_lang = "ru"

# English translations keyed by Russian originals
_EN = {
    # Activity: reading
    "берёт книжку...": "picks up a book...",
    "читает...": "reading...",
    "о! интересно!": "oh! interesting!",
    "читает дальше...": "keeps reading...",
    "закрыл книгу": "closed the book",

    # Activity: working
    "открывает ноутбук...": "opens laptop...",
    "тук-тук-тук...": "tap-tap-tap...",
    "хмм...": "hmm...",
    "ПИШЕТ КОД!!": "WRITING CODE!!",
    "готово! ✨": "done! ✨",

    # Activity: magic
    "достаёт палочку...": "grabs the wand...",
    "замахивается...": "winding up...",
    "✨ ВЗМАХ!": "✨ SWOOSH!",

    # Activity: fishing
    "забрасывает удочку...": "casts the line...",
    "ждёт...": "waiting...",
    "❗ клюёт!!": "❗ a bite!!",
    "тянет!!!": "pulling!!!",

    # Activity: playing
    "прыгает!": "bouncing!",

    # Activity: music
    "♪♫♬": "♪♫♬",

    # Activity: painting
    "ставит мольберт...": "sets up easel...",
    "рисует...": "painting...",
    "хмм... неплохо!": "hmm... not bad!",

    # Activity: telescope
    "достаёт телескоп...": "pulls out telescope...",
    "космос...": "space...",

    # Activity: meditating
    "ом...": "om...",

    # Activity: juggling
    "жонглирует!": "juggling!",

    # Fishing catches
    "рыбка!": "a fish!",
    "фугу!!": "pufferfish!!",
    "ботинок...": "a boot...",
    "водоросли": "seaweed",
    "АЛМАЗ!!": "DIAMOND!!",
    "коробка?!": "a box?!",
    "звезда!!!": "a star!!!",
    "носок.": "a sock.",

    # Magic results
    "букет! 💐": "bouquet! 💐",
    "радуга! 🌈": "rainbow! 🌈",
    "звездопад! ⭐": "shooting stars! ⭐",
    "бабочка! 🦋": "butterfly! 🦋",
    "пуф! 💨": "poof! 💨",

    # Reactions
    "привет! :3": "hi! :3",
    "о!": "oh!",
    "рада тебя видеть": "happy to see you",
    ":3": ":3",
    "♥": "♥",
    "хм?": "hm?",
    "*машет*": "*waves*",

    # Idle phrases
    "скучно...": "bored...",
    "хм...": "hm...",
    "думаю о рыбке...": "thinking about fish...",
    "тут красиво": "it's nice here",
    "*зевает*": "*yawns*",
    "...": "...",
    "когда же рыбалка?": "when's fishing time?",
    "а что если...": "what if...",
    "мне нравится тут": "I like it here",
    "интересно...": "interesting...",
    "ля-ля-ля": "la-la-la",
    "*смотрит вдаль*": "*gazes into distance*",
    "о чём бы подумать...": "what to think about...",

    # System events
    "о, опять сидим в Интернете?": "oh, browsing again?",
    "Safari? ну ладно...": "Safari? alright...",
    "хакерское время!": "hacker time!",
    "терминал? кодим!": "terminal? let's code!",
    "кодим? кодим.": "coding? coding.",
    "VS Code!": "VS Code!",
    "о, музыка! 🎵": "oh, music! 🎵",
    "что слушаем?": "what are we listening to?",
    "кто-то написал?": "someone messaged?",
    "Telegram!": "Telegram!",
    "ищем что-то?": "looking for something?",
    "о, фоточки!": "oh, photos!",
    "о, это же я! ну, почти...": "oh, that's me! well, almost...",

    # Startup / system
    "*зевает*": "*yawns*",
}


def set_language(lang):
    """Set the current language ('ru' or 'en')."""
    global _current_lang
    _current_lang = lang


def get_language():
    """Get the current language."""
    return _current_lang


def t(text):
    """Translate a phrase to the current language."""
    if _current_lang == "en":
        return _EN.get(text, text)
    return text
