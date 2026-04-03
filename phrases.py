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
    "а облака красивые...": "the clouds are pretty...",
    "*тихо напевает*": "*hums quietly*",
    "где мой телескоп?": "where's my telescope?",
    "надо бы порыбачить...": "should go fishing...",
    "*считает звёзды*": "*counting stars*",
    "хочу алмаз...": "I want a diamond...",
    "*потягивается*": "*stretches*",
    "какой хороший день": "what a nice day",
    "моя клешня!": "my claw!",
    "а что там в интернете?": "what's on the internet?",

    # System events — browsers
    "о, опять сидим в Интернете?": "oh, browsing again?",
    "Safari? ну ладно...": "Safari? alright...",
    "что гуглим?": "what are we googling?",
    "интернет! бесконечный...": "internet! endless...",
    "опять мемы?": "memes again?",
    "Chrome съел всю память!": "Chrome ate all the memory!",
    "Firefox! олдскул": "Firefox! old school",
    "Arc! стильно": "Arc! stylish",
    # System events — terminals
    "хакерское время!": "hacker time!",
    "терминал? кодим!": "terminal? let's code!",
    "sudo краб!": "sudo crab!",
    "о, командная строка!": "oh, command line!",
    "о, Warp! красиво": "oh, Warp! pretty",
    # System events — code editors
    "кодим? кодим.": "coding? coding.",
    "VS Code!": "VS Code!",
    "Sublime!": "Sublime!",
    "PyCharm!": "PyCharm!",
    "время писать код!": "time to code!",
    "баги не ждут!": "bugs won't wait!",
    "а юнит-тесты?": "what about unit tests?",
    # System events — music
    "о, музыка! 🎵": "oh, music! 🎵",
    "что слушаем?": "what are we listening to?",
    "♪ ля-ля-ля ♪": "♪ la-la-la ♪",
    "потанцуем?": "shall we dance?",
    "хороший вкус!": "good taste!",
    # System events — messengers
    "кто-то написал?": "someone messaged?",
    "Telegram!": "Telegram!",
    "сплетни? 👀": "gossip? 👀",
    "кому отвечаем?": "who are we replying to?",
    # System events — finder/photos
    "ищем что-то?": "looking for something?",
    "где же этот файл...": "where is that file...",
    "столько папок!": "so many folders!",
    "порядок наведём?": "shall we tidy up?",
    "о, фоточки!": "oh, photos!",
    "красивое!": "pretty!",
    "а это кто? 👀": "who's that? 👀",
    "📸!": "📸!",
    # System events — Claude
    "о, это же я! ну, почти...": "oh, that's me! well, almost...",
    "привет, другая я!": "hi, other me!",
    "мы похожи!": "we look alike!",
    # System events — text editors
    "пишем роман?": "writing a novel?",
    "вдохновение пришло?": "feeling inspired?",
    "слова, слова, слова...": "words, words, words...",
    "творим!": "creating!",
    "markdown! красиво": "markdown! beautiful",
    "минимализм! нравится": "minimalism! love it",

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
