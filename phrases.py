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

    # Activity: campfire
    "разжёг костёр!": "lit a campfire!",
    "тепло...": "warm...",
    "люблю смотреть на огонь...": "love watching the fire...",
    "жарит зефирку!": "roasting marshmallow!",
    "вкусно! :3": "yummy! :3",

    # Activity: sandcastle
    "строит замок...": "building a castle...",
    "лепит...": "shaping...",
    "какой красивый!": "how beautiful!",
    "ой, рассыпался...": "oh, it collapsed...",

    # Activity: shell collecting
    "ищет ракушки...": "looking for shells...",
    "где-то тут была...": "it was somewhere here...",
    "красивая должна быть рядом...": "a pretty one must be nearby...",
    "тут столько ракушек!": "so many shells here!",
    "о! нашёл!": "oh! found one!",
    "подбирает...": "picking it up...",
    "какая красивая ракушка!": "what a beautiful shell!",

    # Activity: candle
    "зажигает свечку...": "lighting the candle...",
    "огонёк мерцает...": "the flame flickers...",
    "так спокойно...": "so peaceful...",
    "можно так сидеть вечно...": "could sit like this forever...",

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

    # Summoning / friend
    "кого бы призвать...": "who should I summon...",
    "✨ ПРИЗЫВ!": "✨ SUMMON!",
    "о! привет, друг!": "oh! hi, friend!",
    "как дела?": "how are you?",
    "давно не виделись!": "long time no see!",
    "что нового?": "what's new?",
    "привет-привет!": "hello hello!",
    "*обнимаются*": "*hugging*",
    "вместе веселее!": "more fun together!",
    "ты мой лучший друг!": "you're my best friend!",
    "расскажи что-нибудь!": "tell me something!",
    "а помнишь?...": "remember when?...",
    "пока-пока!": "bye-bye!",
    "было весело!": "that was fun!",
    "приходи ещё!": "come back soon!",
    "скучаю уже...": "miss you already...",
    "до встречи!": "see you!",
    "хороший был день :3": "good day :3",

    # Friend together-activities: walk
    "погуляем!": "let's walk!",
    "пойдём!": "let's go!",
    "куда пойдём?": "where to?",
    "прогулка!": "walk time!",
    "вперёд!": "onwards!",
    "хорошая прогулка!": "nice walk!",
    "устал :3": "tired :3",
    "вернулись!": "we're back!",
    # Friend together-activities: play
    "играем!": "let's play!",
    "догоняй!": "catch me!",
    "весело!": "so fun!",
    "ещё! ещё!": "more! more!",
    "прыг-прыг!": "boing-boing!",
    # Friend together-activities: sit
    "тихо тут...": "it's quiet...",
    "красиво...": "beautiful...",
    "просто посидим": "let's just sit",
    "звёзды...": "stars...",
    "*молчит вместе*": "*quiet together*",
    # Friend together-activities: chat
    "а ты знал?...": "did you know?...",
    "слушай!": "listen!",
    "расскажу историю!": "let me tell a story!",
    "угадай что!": "guess what!",
    "а помнишь тот раз?": "remember that time?",
    "ха-ха! да!": "ha-ha! yeah!",
    "правда?!": "really?!",
    "это здорово!": "that's great!",
    "расскажи ещё!": "tell me more!",
    "ого!": "wow!",

    # Startup / system
    "*зевает*": "*yawns*",

    # Personal click phrases (attachment)
    "как дела, {name}?": "how's it going, {name}?",
    "чем занимаешься, {name}?": "whatcha doing, {name}?",
    "мне нравится проводить время с {name} :3": "i like spending time with {name} :3",
    "рада тебя видеть, {name}!": "happy to see you, {name}!",
    "{name}! :3": "{name}! :3",
    "а {name} сегодня внимательный": "{name} is generous with clicks today",
    # Personal click (nameless)
    "как дела?": "how's it going?",
    "чем занимаешься?": "whatcha doing?",
    "мне нравится проводить с тобой время :3": "i like spending time with you :3",

    # Sleep phrases (attachment)
    "засыпаю, {name}... 💤": "falling asleep, {name}... 💤",
    "посплю немного... не скучай, {name}": "gonna nap... don't miss me, {name}",
    "глазки закрываются...": "eyes closing...",
    "сон зовёт... до скорого, {name}": "sleep calls... see you soon, {name}",
    "{name}, я посплю чуть-чуть :3": "{name}, nap time :3",
    # Wake phrases (attachment)
    "хорошо поспал :3": "that was a nice nap :3",
    "о, {name}! я тут!": "oh, {name}! i'm here!",
    "выспался! {name}, привет!": "well-rested! hi, {name}!",
    "*потягивается* ...{name}!": "*stretches* ...{name}!",
    "а? что? ...о, {name}!": "huh? what? ...oh, {name}!",

    # Days-together phrases
    "мы уже {n} дней вместе": "we've been together for {n} days",
    "{n} дней! время летит": "{n} days! time flies",
    # Days-together milestones
    "ого, {n} дней! это что-то значит, {name}": "wow, {n} days! that means something, {name}",
    "{n} дней! мне нравится эта традиция, {name}": "{n} days! i like this tradition, {name}",

    # App launch counter
    "{app} в {n}-й раз за сегодня :)": "{app} for the {n}th time today :)",
    "опять {app}? это уже {n}-й раз": "{app} again? that's {n} times now",

    # Gift announcement
    "смотри, что я нашёл!": "look what i found!",
    "это тебе! :3": "this is for you! :3",
    "о! подарок для {name}!": "oh! a gift for {name}!",
    "нашёл кое-что...": "found something...",
    "тебе понравится!": "you'll like this!",

    # Gift expired
    "ну ладно, оставлю себе :p": "ok, keeping it for myself :p",
    "не заметил? ну и ладно...": "didn't notice? oh well...",
    "в следующий раз повезёт :3": "maybe next time :3",

    # Gift collection
    "тебе понравилось? :3": "you liked it? :3",
    "это тебе!": "this is for you!",
    "нашёл и подумал о тебе": "found it and thought of you",

    # Star naming (telescope gift)
    "назвал звезду в честь {name} ⭐": "named a star after {name} ⭐",
    "эта звезда теперь — {name} ⭐": "that star is now called {name} ⭐",
    "назвал звезду в честь тебя ⭐": "named a star after you ⭐",
}

# --- Phrase lists for the relationship system ---

PERSONAL_CLICK_PHRASES = [
    "как дела, {name}?", "чем занимаешься, {name}?",
    "мне нравится проводить время с {name} :3",
    "рада тебя видеть, {name}!", "{name}! :3",
    "а {name} сегодня внимательный",
]

PERSONAL_CLICK_PHRASES_NAMELESS = [
    "как дела?", "чем занимаешься?",
    "мне нравится проводить с тобой время :3",
]

SLEEP_PHRASES = [
    "засыпаю, {name}... 💤",
    "посплю немного... не скучай, {name}",
    "глазки закрываются...",
    "сон зовёт... до скорого, {name}",
    "{name}, я посплю чуть-чуть :3",
]

WAKE_PHRASES = [
    "хорошо поспал :3",
    "о, {name}! я тут!",
    "выспался! {name}, привет!",
    "*потягивается* ...{name}!",
    "а? что? ...о, {name}!",
]

DAYS_PHRASES = [
    "мы уже {n} дней вместе",
    "{n} дней! время летит",
]

DAYS_MILESTONE_PHRASES = [
    "ого, {n} дней! это что-то значит, {name}",
    "{n} дней! мне нравится эта традиция, {name}",
]

APP_COUNT_PHRASES = [
    "{app} в {n}-й раз за сегодня :)",
    "опять {app}? это уже {n}-й раз",
]

GIFT_ANNOUNCE_PHRASES = [
    "смотри, что я нашёл!",
    "это тебе! :3",
    "о! подарок для {name}!",
    "нашёл кое-что...",
    "тебе понравится!",
]

GIFT_EXPIRED_PHRASES = [
    "ну ладно, оставлю себе :p",
    "не заметил? ну и ладно...",
    "в следующий раз повезёт :3",
]

GIFT_COLLECT_PHRASES = [
    "тебе понравилось? :3",
    "это тебе!",
    "нашёл и подумал о тебе",
]

STAR_NAMING_PHRASES = [
    "назвал звезду в честь {name} ⭐",
    "эта звезда теперь — {name} ⭐",
]

STAR_NAMING_PHRASES_NAMELESS = [
    "назвал звезду в честь тебя ⭐",
]

# Claude.ai easter egg phrases (always English, no translation)
CLAUDE_AI_PHRASES = [
    "golden hour thinking",
    "{name} returns!",
    "coffee and Claude time?",
    "ready when you are, {name}",
    "let's think about this together",
]


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


def format_phrase(text, name="", n=0, app=""):
    """Translate and fill in {name}, {n}, {app} placeholders.

    If name is empty, strips surrounding punctuation/spaces around {name}."""
    result = t(text)
    if name:
        result = result.replace("{name}", name)
    else:
        # Clean removal of {name} with surrounding separators
        for pattern in [", {name}", " {name}", "{name} ", "{name}", "{name},", "{name}!"]:
            result = result.replace(pattern, "")
    result = result.replace("{n}", str(n))
    result = result.replace("{app}", app)
    return result.strip()
