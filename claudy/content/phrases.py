"""Bilingual phrase system — Russian and English."""

import random

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
    "о, Kitty! красиво": "oh, Kitty! pretty",
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

    # Gift received (user -> Claudy): flower
    "цветочек! спасибо! 🌸": "a flower! thank you! 🌸",
    "какой красивый! спасибо!": "how beautiful! thank you!",
    "мне? правда? :3": "for me? really? :3",
    "поставлю у себя!": "i'll put it on display!",
    # Gift received: book
    "о! книжка! буду читать перед сном!": "oh! a book! i'll read it before bed!",
    "обожаю читать! спасибо!": "i love reading! thank you!",
    "какая интересная! :3": "how interesting! :3",
    "новая книжка! ура!": "a new book! yay!",
    # Gift received: song
    "мелодия! ♪♫♬": "a melody! ♪♫♬",
    "какая красивая песня!": "what a beautiful song!",
    "буду напевать! ♪": "i'll hum it! ♪",
    "запомню эту песню :3": "i'll remember this song :3",
    # Gift received: marshmallow
    "зефирка! пожарю на костре!": "a marshmallow! i'll roast it on the campfire!",
    "вкусняшка! сохраню для костра!": "yummy! saving it for the campfire!",
    "зефир! обожаю! :3": "marshmallow! love it! :3",
    "пожарю у костра! спасибо!": "i'll roast it at the campfire! thanks!",
    # Gift received: toy
    "мишка! буду с ним спать!": "a teddy! i'll sleep with it!",
    "какой мягкий! :3": "so soft! :3",
    "игрушка! положу рядом с подушкой!": "a toy! i'll put it next to my pillow!",
    "теперь не страшно засыпать!": "not scary to fall asleep now!",
    # Book idle phrases
    "интересная книжка...": "interesting book...",
    "надо дочитать книжку!": "gotta finish the book!",
    "а что там дальше в книге?": "what happens next in the book?",
    "хорошая книга :3": "good book :3",
    "*листает страницы*": "*turning pages*",
    "ещё одну главу...": "one more chapter...",

    # Campfire marshmallow override (user gave marshmallow)
    "а эта зефирка от {name} <3": "this marshmallow is from {name} <3",
    "жарю зефирку от {name}!": "roasting {name}'s marshmallow!",
    "зефирка от {name}... вкусно будет!": "{name}'s marshmallow... it's gonna be tasty!",
    "а эта зефирка — подарок <3": "this marshmallow is a gift <3",
    "жарю подаренную зефирку!": "roasting the gifted marshmallow!",
    "вкусно! спасибо, {name}! :3": "yummy! thanks, {name}! :3",
    "самая вкусная зефирка! :3": "the tastiest marshmallow! :3",
    "вкусно! спасибо за зефирку! :3": "yummy! thanks for the marshmallow! :3",
}

# --- Everyday phrase lists ---

IDLE_PHRASES = [
    "скучно...", "хм...", ":3", "думаю о рыбке...",
    "тут красиво", "*зевает*", "...", "когда же рыбалка?",
    "а что если...", "мне нравится тут", "интересно...",
    "ля-ля-ля", "*смотрит вдаль*", "о чём бы подумать...",
    "а облака красивые...", "*тихо напевает*", "где мой телескоп?",
    "надо бы порыбачить...", "*считает звёзды*", "хочу алмаз...",
    "*потягивается*", "какой хороший день", "моя клешня!",
    "а что там в интернете?",
]

GREETING_PHRASES = ["привет! :3", "о!", "рада тебя видеть", ":3"]
HOVER_PHRASES = ["хм?", "*машет*"]

SHELL_SEARCH_PHRASES = [
    "ищет ракушки...",
    "где-то тут была...",
    "красивая должна быть рядом...",
    "тут столько ракушек!",
]

# --- Friend (summoning) phrase lists ---

FRIEND_PHRASES = [
    "о! привет, друг!", "как дела?", "давно не виделись!",
    "что нового?", "привет-привет!",
]

FRIEND_AFTER = [
    "было весело!", "приходи ещё!", "скучаю уже...",
    "до встречи!", "хороший был день :3",
]

FRIEND_WALK_PHRASES = [
    "погуляем!", "пойдём!", "куда пойдём?",
    "прогулка!", "вперёд!",
]

FRIEND_WALK_END_PHRASES = [
    "хорошая прогулка!", "устал :3", "вернулись!",
]

FRIEND_PLAY_PHRASES = [
    "играем!", "догоняй!", "весело!",
    "ещё! ещё!", "прыг-прыг!",
]

FRIEND_SIT_PHRASES = [
    "тихо тут...", "красиво...", "просто посидим",
    "звёзды...", "*молчит вместе*",
]

FRIEND_CHAT_PHRASES = [
    "а ты знал?...", "слушай!", "расскажу историю!",
    "угадай что!", "а помнишь тот раз?",
    "*обнимаются*", "вместе веселее!", "ты мой лучший друг!",
    "расскажи что-нибудь!", "а помнишь?...",
]

FRIEND_CHAT_REPLY_PHRASES = [
    "ха-ха! да!", "правда?!", "это здорово!",
    "расскажи ещё!", "ого!",
]

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

# Gift received phrases (user -> Claudy)
GIFT_FLOWER_PHRASES = [
    "цветочек! спасибо! 🌸",
    "какой красивый! спасибо!",
    "мне? правда? :3",
    "поставлю у себя!",
]

GIFT_BOOK_PHRASES = [
    "о! книжка! буду читать перед сном!",
    "обожаю читать! спасибо!",
    "какая интересная! :3",
    "новая книжка! ура!",
]

GIFT_SONG_PHRASES = [
    "мелодия! ♪♫♬",
    "какая красивая песня!",
    "буду напевать! ♪",
    "запомню эту песню :3",
]

GIFT_MARSHMALLOW_PHRASES = [
    "зефирка! пожарю на костре!",
    "вкусняшка! сохраню для костра!",
    "зефир! обожаю! :3",
    "пожарю у костра! спасибо!",
]

GIFT_TOY_PHRASES = [
    "мишка! буду с ним спать!",
    "какой мягкий! :3",
    "игрушка! положу рядом с подушкой!",
    "теперь не страшно засыпать!",
]

BOOK_IDLE_PHRASES = [
    "интересная книжка...",
    "надо дочитать книжку!",
    "а что там дальше в книге?",
    "хорошая книга :3",
    "*листает страницы*",
    "ещё одну главу...",
]

GIFT_RECEIVE_PHRASES = {
    "flower": GIFT_FLOWER_PHRASES,
    "book": GIFT_BOOK_PHRASES,
    "song": GIFT_SONG_PHRASES,
    "marshmallow": GIFT_MARSHMALLOW_PHRASES,
    "toy": GIFT_TOY_PHRASES,
}

# Campfire marshmallow override phrases
CAMPFIRE_MARSHMALLOW_ROAST_PHRASES = [
    "а эта зефирка от {name} <3",
    "жарю зефирку от {name}!",
    "зефирка от {name}... вкусно будет!",
]

CAMPFIRE_MARSHMALLOW_ROAST_PHRASES_NAMELESS = [
    "а эта зефирка — подарок <3",
    "жарю подаренную зефирку!",
]

CAMPFIRE_MARSHMALLOW_DONE_PHRASES = [
    "вкусно! спасибо, {name}! :3",
    "самая вкусная зефирка! :3",
]

CAMPFIRE_MARSHMALLOW_DONE_PHRASES_NAMELESS = [
    "вкусно! спасибо за зефирку! :3",
    "самая вкусная зефирка! :3",
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


def pick(pool, name="", n=0, app=""):
    """Pick a random phrase from `pool`, translated and filled in."""
    return format_phrase(random.choice(pool), name=name, n=n, app=app)


def pick_personal(named_pool, nameless_pool, name=""):
    """Pick from `named_pool` when the user has a name, else `nameless_pool`."""
    return pick(named_pool if name else nameless_pool, name=name)
