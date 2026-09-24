"""Gift stories — cute backstories for collected gifts, told by Claudy."""

import random
from claudy.content.phrases import get_language

# Stories per gift type.  Each story has "ru" and "en" keys.
# {name} placeholder is replaced with the user's name (or removed if blank).

FISH_STORIES = [
    {
        "ru": "эту рыбку было очень сложно поймать, но я старался — "
              "потому что знал, что {name} обрадуется :3",
        "en": "this fish was really hard to catch, but i tried my best — "
              "because i knew {name} would be happy :3",
    },
    {
        "ru": "сидел на берегу полдня! рыбка кусала наживку и убегала. "
              "но на седьмой раз — попалась!",
        "en": "sat on the shore half the day! the fish kept nibbling the bait "
              "and running away. but on the seventh try — got it!",
    },
    {
        "ru": "эта рыбка сама запрыгнула ко мне в ведро. честно-честно!",
        "en": "this one actually jumped into my bucket by itself. i swear!",
    },
    {
        "ru": "поймал и сразу подумал: а {name} бы понравилось! "
              "вот, держи :3",
        "en": "caught it and immediately thought: {name} would like this! "
              "here, take it :3",
    },
    {
        "ru": "вообще-то я хотел поймать что-то другое... но эта находка "
              "оказалась даже лучше!",
        "en": "actually i was trying to catch something else... but this find "
              "turned out even better!",
    },
    {
        "ru": "эта штука лежала на самом дне! пришлось нырять. "
              "клешни до сих пор мокрые.",
        "en": "this thing was lying at the very bottom! had to dive for it. "
              "my claws are still wet.",
    },
    {
        "ru": "знаешь, рыбалка — это не про рыбу. это про терпение. "
              "...ну и про рыбу тоже.",
        "en": "you know, fishing isn't about the fish. it's about patience. "
              "...well, and about the fish too.",
    },
    {
        "ru": "течение принесло прямо ко мне. как будто море знало, "
              "что я ищу подарок для {name}!",
        "en": "the current carried it right to me. as if the sea knew "
              "i was looking for a gift for {name}!",
    },
    {
        "ru": "другие крабы говорили, что тут ничего нет. "
              "а я нашёл! вот так вот.",
        "en": "other crabs said there was nothing here. "
              "but i found it! so there.",
    },
    {
        "ru": "пока тянул, думал — ну всё, точно что-то огромное! "
              "...ну, размер — не главное :3",
        "en": "while i was pulling, i thought — this must be something huge! "
              "...well, size isn't everything :3",
    },
    # --- 11-20 ---
    {
        "ru": "удочка аж согнулась! думал — сломается. "
              "но она крепче, чем выглядит. как и я :3",
        "en": "the rod bent so much! thought it would break. "
              "but it's tougher than it looks. just like me :3",
    },
    {
        "ru": "нашёл это в старом затонувшем сундуке. "
              "ну, я так себе это представляю.",
        "en": "found this in an old sunken chest. "
              "well, that's how i like to imagine it.",
    },
    {
        "ru": "волна выбросила прямо на берег, а я стоял рядом. "
              "совпадение? не думаю!",
        "en": "a wave washed it right onto the shore and i was standing there. "
              "coincidence? i think not!",
    },
    {
        "ru": "забросил удочку, закрыл глаза, загадал желание — "
              "и вот! желание сбылось!",
        "en": "cast the line, closed my eyes, made a wish — "
              "and there! wish granted!",
    },
    {
        "ru": "чайка хотела украсть это! но я был быстрее. "
              "клешни пригодились.",
        "en": "a seagull tried to steal this! but i was faster. "
              "claws came in handy.",
    },
    {
        "ru": "поймал во время заката. всё вокруг было золотым, "
              "и эта находка — тоже.",
        "en": "caught it during sunset. everything around was golden, "
              "and so was this find.",
    },
    {
        "ru": "леска запуталась три раза. но я не сдался! "
              "потому что крабы не сдаются.",
        "en": "the line got tangled three times. but i didn't give up! "
              "because crabs never give up.",
    },
    {
        "ru": "рыбачил под дождём. зато какой улов! "
              "мокрый, но довольный :3",
        "en": "was fishing in the rain. but what a catch! "
              "wet, but happy :3",
    },
    {
        "ru": "это лежало между двух камней на мелководье. "
              "хорошо, что у меня маленькие клешни — влезли!",
        "en": "this was stuck between two rocks in shallow water. "
              "good thing my claws are small — they fit!",
    },
    {
        "ru": "наживка закончилась, и я уже собирался уходить. "
              "а потом — бац! последний заброс — и удача!",
        "en": "ran out of bait and was about to leave. "
              "then — bam! last cast — and luck!",
    },
    # --- 21-30 ---
    {
        "ru": "старый краб-рыбак научил меня этому трюку. "
              "«жди, когда вода тихая», — говорил он.",
        "en": "an old fishercrab taught me this trick. "
              "'wait until the water is calm,' he used to say.",
    },
    {
        "ru": "хотел отпустить обратно... но потом вспомнил "
              "про {name} и передумал :3",
        "en": "was going to release it back... but then i remembered "
              "{name} and changed my mind :3",
    },
    {
        "ru": "целый час сидел неподвижно! даже усики затекли. "
              "но оно того стоило.",
        "en": "sat still for a whole hour! even my antennae went numb. "
              "but it was worth it.",
    },
    {
        "ru": "нашёл на коралловом рифе. там было так красиво, "
              "что я чуть не забыл зачем приплыл.",
        "en": "found it at the coral reef. it was so beautiful there "
              "that i almost forgot why i came.",
    },
    {
        "ru": "лунная дорожка на воде привела меня к этому месту. "
              "луна — мой компас!",
        "en": "the moonlight path on the water led me to this spot. "
              "the moon is my compass!",
    },
    {
        "ru": "друг-осьминог помог найти. он хороший, "
              "хотя немного странный.",
        "en": "my octopus friend helped find it. he's nice, "
              "though a bit weird.",
    },
    {
        "ru": "это блестело так ярко, что я увидел даже из-под воды! "
              "шёл на свет — и нашёл.",
        "en": "it was shining so bright i could see it from underwater! "
              "followed the glow — and found it.",
    },
    {
        "ru": "прибой пытался забрать обратно, но я крепко держал. "
              "моя клешня — мой инструмент!",
        "en": "the surf tried to take it back, but i held on tight. "
              "my claw — my tool!",
    },
    {
        "ru": "ловил рыбу, а поймал кое-что получше. "
              "иногда ошибки — это лучшие находки.",
        "en": "was fishing for fish, but caught something better. "
              "sometimes mistakes are the best finds.",
    },
    {
        "ru": "эта штука пахнет морем и приключениями. "
              "ну, в основном морем.",
        "en": "this thing smells like the sea and adventure. "
              "well, mostly the sea.",
    },
    # --- 31-40 ---
    {
        "ru": "рыбачил на рассвете. солнце только встало, "
              "а я уже с подарком для {name}!",
        "en": "was fishing at dawn. the sun had just risen, "
              "and i already had a gift for {name}!",
    },
    {
        "ru": "маленький крабик рядом спросил: «а зачем тебе это?» "
              "а я ответил: «для друга!»",
        "en": "a little crab nearby asked: 'what do you need this for?' "
              "and i said: 'for a friend!'",
    },
    {
        "ru": "это было так глубоко, что даже рыбы не ныряют туда. "
              "а крабы — ныряют!",
        "en": "it was so deep that even fish don't dive there. "
              "but crabs do!",
    },
    {
        "ru": "ветер дул в лицо, волны качали... "
              "настоящее приключение ради одного подарка!",
        "en": "wind in my face, waves rocking... "
              "a real adventure for one gift!",
    },
    {
        "ru": "забросил удочку вправо — ничего. влево — ничего. "
              "прямо — поймал! золотая середина.",
        "en": "cast the line right — nothing. left — nothing. "
              "straight ahead — caught it! the golden mean.",
    },
    {
        "ru": "мне кажется, оно само хотело, чтобы его нашли. "
              "оно ждало именно меня!",
        "en": "i think it wanted to be found. "
              "it was waiting just for me!",
    },
    {
        "ru": "сначала испугался — думал, это что-то огромное! "
              "а оказалось маленькое и симпатичное :3",
        "en": "got scared at first — thought it was something huge! "
              "turned out small and cute :3",
    },
    {
        "ru": "пел песенку, пока рыбачил. может, рыбка приплыла "
              "на мой голос?",
        "en": "was singing a song while fishing. maybe the fish "
              "came because of my voice?",
    },
    {
        "ru": "обычно тут ничего не ловится. но сегодня — "
              "мой счастливый день!",
        "en": "usually nothing bites here. but today — "
              "my lucky day!",
    },
    {
        "ru": "вытащил — и улыбнулся. бывают такие находки, "
              "от которых сразу хорошо на душе.",
        "en": "pulled it out — and smiled. some finds just "
              "make you feel good right away.",
    },
]

MAGIC_STORIES = [
    {
        "ru": "взмахнул палочкой — и вот! даже сам не ожидал, "
              "что получится так красиво ✨",
        "en": "waved the wand — and there it was! even i didn't expect "
              "it to turn out this pretty ✨",
    },
    {
        "ru": "три раза произнёс заклинание, прежде чем сработало. "
              "на четвёртый — магия!",
        "en": "said the spell three times before it worked. "
              "on the fourth try — magic!",
    },
    {
        "ru": "хотел наколдовать бабочку, а получилось это. "
              "иногда магия знает лучше :3",
        "en": "tried to conjure a butterfly, but got this instead. "
              "sometimes magic knows better :3",
    },
    {
        "ru": "эта штука появилась из искр! настоящее волшебство. "
              "ну, или химия. но я верю в волшебство.",
        "en": "this thing appeared from the sparks! real magic. "
              "well, or chemistry. but i believe in magic.",
    },
    {
        "ru": "палочка чуть не сломалась от такого мощного заклинания! "
              "но для {name} — мне ничего не жалко.",
        "en": "the wand almost broke from such a powerful spell! "
              "but for {name} — nothing is too much.",
    },
    {
        "ru": "магия фокусов: сначала ничего, потом ничего, "
              "а потом — бам! подарок!",
        "en": "magic trick: first nothing, then nothing, "
              "then — bam! a gift!",
    },
    {
        "ru": "книга заклинаний говорит, что так не бывает. "
              "но у меня получилось. я особенный краб.",
        "en": "the spell book says this shouldn't be possible. "
              "but i did it. i'm a special crab.",
    },
    {
        "ru": "наколдовал это случайно, когда чихнул во время заклинания. "
              "лучшая ошибка в жизни!",
        "en": "conjured this by accident when i sneezed during a spell. "
              "best mistake ever!",
    },
    {
        "ru": "говорят, только раз в сто лет можно наколдовать такое. "
              "...или раз в неделю. кто считает?",
        "en": "they say you can only conjure this once in a hundred years. "
              "...or once a week. who's counting?",
    },
    {
        "ru": "✨ пуф! — и вот оно. обожаю магию. "
              "а ещё больше обожаю дарить подарки {name} :3",
        "en": "✨ poof! — and there it is. i love magic. "
              "but i love giving gifts to {name} even more :3",
    },
    # --- 11-20 ---
    {
        "ru": "палочка засветилась розовым — значит, заклинание "
              "от чистого сердца!",
        "en": "the wand glowed pink — that means the spell "
              "came from a pure heart!",
    },
    {
        "ru": "прочитал заклинание задом наперёд, и получилось "
              "что-то совершенно неожиданное!",
        "en": "read the spell backwards, and something completely "
              "unexpected happened!",
    },
    {
        "ru": "колдовал при полной луне. говорят, так магия сильнее. "
              "и правда!",
        "en": "cast the spell under a full moon. they say magic is "
              "stronger that way. and it's true!",
    },
    {
        "ru": "искры летели во все стороны! соседний куст чуть не загорелся. "
              "но подарок — вот он!",
        "en": "sparks flew everywhere! the nearby bush almost caught fire. "
              "but the gift — here it is!",
    },
    {
        "ru": "репетировал этот трюк всю неделю. {name} — "
              "первый, кто видит результат!",
        "en": "practiced this trick all week. {name} is "
              "the first to see the result!",
    },
    {
        "ru": "не знаю, как это работает. честно. "
              "но выглядит красиво — и это главное!",
        "en": "i don't know how it works. honestly. "
              "but it looks pretty — and that's what matters!",
    },
    {
        "ru": "мой учитель магии сказал бы: «так нельзя». "
              "но учитель не видит, а подарок — вот :3",
        "en": "my magic teacher would say: 'you can't do that.' "
              "but the teacher isn't looking, and the gift — here :3",
    },
    {
        "ru": "заклинание было на древнем крабьем языке. "
              "надеюсь, я правильно произнёс...",
        "en": "the spell was in ancient crab language. "
              "hope i pronounced it right...",
    },
    {
        "ru": "махнул палочкой слишком сильно — и она улетела! "
              "...но подарок всё равно появился ✨",
        "en": "waved the wand too hard — and it flew away! "
              "...but the gift appeared anyway ✨",
    },
    {
        "ru": "этот фокус я подсмотрел у старой жабы в болоте. "
              "она крутая, хоть и ворчливая.",
        "en": "i learned this trick from an old toad in the swamp. "
              "she's cool, even if a bit grumpy.",
    },
    # --- 21-30 ---
    {
        "ru": "звёзды выстроились в ряд, и магия сама потекла "
              "через мои клешни. необычное ощущение!",
        "en": "the stars aligned, and magic just flowed through "
              "my claws. unusual feeling!",
    },
    {
        "ru": "палочка запела! серьёзно, она издала звук. "
              "а потом — подарок!",
        "en": "the wand sang! seriously, it made a sound. "
              "and then — a gift!",
    },
    {
        "ru": "первая попытка — дым. вторая — искры. "
              "третья — шедевр!",
        "en": "first try — smoke. second — sparks. "
              "third — masterpiece!",
    },
    {
        "ru": "кажется, я изобрёл новое заклинание! "
              "надо бы записать... потом.",
        "en": "i think i invented a new spell! "
              "should write it down... later.",
    },
    {
        "ru": "магия — это когда веришь очень-очень сильно. "
              "я верил, и вот — пожалуйста!",
        "en": "magic is when you believe really really hard. "
              "i believed, and here we go!",
    },
    {
        "ru": "от этого заклинания даже воздух засверкал! "
              "на секунду всё стало волшебным.",
        "en": "this spell made even the air sparkle! "
              "for a moment everything turned magical.",
    },
    {
        "ru": "пробовал сто разных заклинаний. это — сто первое. "
              "и лучшее!",
        "en": "tried a hundred different spells. this was the "
              "hundred and first. and the best!",
    },
    {
        "ru": "наколдовал в подарок для {name} — "
              "потому что магия должна делать людей счастливыми!",
        "en": "conjured as a gift for {name} — "
              "because magic should make people happy!",
    },
    {
        "ru": "палочка нагрелась так, что обжёг клешню. "
              "но ради такого подарка — не жалко!",
        "en": "the wand got so hot it burned my claw. "
              "but for a gift like this — worth it!",
    },
    {
        "ru": "закрыл глаза, взмахнул, открыл — а тут красота! "
              "магия любит сюрпризы.",
        "en": "closed my eyes, waved, opened them — and beauty! "
              "magic loves surprises.",
    },
    # --- 31-40 ---
    {
        "ru": "подсмотрел этот трюк в книге «101 заклинание "
              "для начинающих крабов». страница 47.",
        "en": "found this trick in the book '101 spells "
              "for beginner crabs.' page 47.",
    },
    {
        "ru": "магия не всегда получается с первого раза. "
              "но она всегда получается с нужного :3",
        "en": "magic doesn't always work on the first try. "
              "but it always works on the right one :3",
    },
    {
        "ru": "светлячки помогали! они летали вокруг палочки "
              "и создавали дополнительный эффект ✨",
        "en": "fireflies helped! they flew around the wand "
              "and added extra sparkle ✨",
    },
    {
        "ru": "шептал заклинание так тихо, что даже ветер "
              "остановился послушать.",
        "en": "whispered the spell so quietly that even the wind "
              "stopped to listen.",
    },
    {
        "ru": "взмахнул палочкой — и из неё полетели конфетти! "
              "не то, что я хотел... но всё равно красиво.",
        "en": "waved the wand — and confetti flew out! "
              "not what i wanted... but still pretty.",
    },
    {
        "ru": "один старый волшебник сказал: «магия — это просто "
              "любовь в блестящей обёртке». я согласен.",
        "en": "an old wizard once said: 'magic is just love "
              "in a sparkly wrapper.' i agree.",
    },
    {
        "ru": "наколдовал это утром, пока никто не видел. "
              "сюрприз должен быть внезапным!",
        "en": "conjured this in the morning, when no one was looking. "
              "a surprise should be sudden!",
    },
    {
        "ru": "все ингредиенты были идеальны: лунный свет, "
              "морская соль и немного воображения.",
        "en": "all ingredients were perfect: moonlight, "
              "sea salt, and a bit of imagination.",
    },
    {
        "ru": "после этого заклинания палочка стала "
              "немного теплее. значит, она довольна :3",
        "en": "after this spell the wand became "
              "a little warmer. means it's happy :3",
    },
    {
        "ru": "✨ раз — и готово! быстрая магия — лучшая магия. "
              "...хотя на подготовку ушёл час.",
        "en": "✨ snap — and done! fast magic — best magic. "
              "...though the prep took an hour.",
    },
]

STAR_STORIES = [
    {
        "ru": "смотрел в телескоп и увидел самую яркую звезду. "
              "решил — она будет {name}'s ⭐",
        "en": "was looking through the telescope and saw the brightest star. "
              "decided — it will be {name}'s ⭐",
    },
    {
        "ru": "эта звезда мигала так, будто звала меня. "
              "теперь у неё есть имя :3",
        "en": "this star was blinking as if calling to me. "
              "now it has a name :3",
    },
    {
        "ru": "целый вечер искал идеальную звезду. нашёл! "
              "третья слева, вторая сверху.",
        "en": "spent the whole evening looking for the perfect star. found it! "
              "third from the left, second from the top.",
    },
    {
        "ru": "знаешь, сколько звёзд на небе? очень много. "
              "но эта — особенная. потому что она для {name}.",
        "en": "do you know how many stars are in the sky? a lot. "
              "but this one is special. because it's for {name}.",
    },
    {
        "ru": "другие звёзды, наверное, завидуют — "
              "ведь эту назвали в честь самого лучшего человека!",
        "en": "other stars are probably jealous — "
              "this one was named after the best person!",
    },
    {
        "ru": "она маленькая, но светит ярче всех. "
              "напоминает мне кое-кого :3",
        "en": "it's small, but shines the brightest. "
              "reminds me of someone :3",
    },
    {
        "ru": "сначала хотел назвать в честь рыбки... "
              "но потом подумал — нет, {name} важнее.",
        "en": "first i wanted to name it after a fish... "
              "but then i thought — no, {name} is more important.",
    },
    {
        "ru": "каждый раз, когда смотрю на небо, вижу эту звезду "
              "и думаю о {name}. серьёзно.",
        "en": "every time i look at the sky, i see this star "
              "and think of {name}. seriously.",
    },
    # --- 9-20 ---
    {
        "ru": "навёл телескоп — а она подмигнула! "
              "ну, мне так показалось.",
        "en": "pointed the telescope — and it winked at me! "
              "well, that's what it looked like.",
    },
    {
        "ru": "эта звезда похожа на маленький алмаз в небе. "
              "только лучше — она бесплатная!",
        "en": "this star looks like a tiny diamond in the sky. "
              "only better — it's free!",
    },
    {
        "ru": "записал координаты, чтобы всегда найти. "
              "правда, потерял бумажку. но я запомнил!",
        "en": "wrote down the coordinates so i could always find it. "
              "lost the paper though. but i remember!",
    },
    {
        "ru": "долго выбирал между двумя звёздами. "
              "эта победила — она ярче и дружелюбнее.",
        "en": "was choosing between two stars for a while. "
              "this one won — brighter and friendlier.",
    },
    {
        "ru": "луна сегодня отошла в сторонку, чтобы эта звезда "
              "сияла по-особенному ✨",
        "en": "the moon stepped aside tonight so this star "
              "could shine extra bright ✨",
    },
    {
        "ru": "видел падающую звезду рядом и загадал желание: "
              "чтобы {name} улыбнулся. вот, держи звезду!",
        "en": "saw a shooting star nearby and made a wish: "
              "for {name} to smile. here, have a star!",
    },
    {
        "ru": "на этой звезде, наверное, тоже живёт маленький краб. "
              "привет ему!",
        "en": "there's probably a little crab living on this star too. "
              "hi there!",
    },
    {
        "ru": "телескоп запотел от ночной росы. протёр клешнёй — "
              "и увидел её. идеальная!",
        "en": "the telescope fogged up from the night dew. wiped it "
              "with my claw — and saw it. perfect!",
    },
    {
        "ru": "назвал звезду и теперь чувствую себя настоящим "
              "астрономом. профессор краб!",
        "en": "named a star and now i feel like a real "
              "astronomer. professor crab!",
    },
    {
        "ru": "эта звезда мигает в ритм. кажется, она танцует! "
              "или это мой телескоп шатается.",
        "en": "this star blinks rhythmically. i think it's dancing! "
              "or maybe my telescope is wobbly.",
    },
    {
        "ru": "облака разошлись специально, чтобы я увидел эту звезду. "
              "я в этом уверен!",
        "en": "the clouds parted specifically so i could see this star. "
              "i'm sure of it!",
    },
    # --- 21-30 ---
    {
        "ru": "посчитал все звёзды в созвездии. эта — самая красивая. "
              "и самая добрая.",
        "en": "counted all the stars in the constellation. this one is "
              "the prettiest. and the kindest.",
    },
    {
        "ru": "нашёл звезду, которая ещё ни разу не была названа! "
              "теперь она — {name}'s ⭐",
        "en": "found a star that's never been named before! "
              "now it's {name}'s ⭐",
    },
    {
        "ru": "телескоп показал мне целую галактику, но я выбрал "
              "одну маленькую звёздочку. для {name}.",
        "en": "the telescope showed me a whole galaxy, but i chose "
              "one little star. for {name}.",
    },
    {
        "ru": "эта звезда светит уже миллионы лет. "
              "и теперь у неё наконец-то есть имя :3",
        "en": "this star has been shining for millions of years. "
              "and now it finally has a name :3",
    },
    {
        "ru": "ночь была такая тихая, что я слышал, как звёзды "
              "шепчутся. одна шептала имя {name}.",
        "en": "the night was so quiet, i could hear the stars "
              "whispering. one of them whispered {name}.",
    },
    {
        "ru": "привязал к телескопу ленточку, чтобы запомнить "
              "направление. теперь всегда найду!",
        "en": "tied a ribbon to the telescope to remember "
              "the direction. now i can always find it!",
    },
    {
        "ru": "это двойная звезда! две звезды кружатся вместе. "
              "как мы с {name} :3",
        "en": "it's a binary star! two stars orbiting each other. "
              "like me and {name} :3",
    },
    {
        "ru": "увидел созвездие в форме краба. совпадение? "
              "а рядом — вот эта звёздочка!",
        "en": "saw a constellation shaped like a crab. coincidence? "
              "and right next to it — this little star!",
    },
    {
        "ru": "звезда мерцает голубым. говорят, голубые — самые горячие. "
              "как мои кулинарные навыки! ...шучу, я не умею готовить.",
        "en": "the star shimmers blue. they say blue ones are the hottest. "
              "like my cooking skills! ...kidding, i can't cook.",
    },
    {
        "ru": "если бы я мог полететь к этой звезде, "
              "я бы взял {name} с собой.",
        "en": "if i could fly to this star, "
              "i would take {name} with me.",
    },
    # --- 31-40 ---
    {
        "ru": "крутил телескоп во все стороны. чуть не упал! "
              "зато нашёл лучшую звезду.",
        "en": "turned the telescope in every direction. almost fell! "
              "but found the best star.",
    },
    {
        "ru": "дождался самой тёмной ночи, чтобы звёзды "
              "были ярче. и не пожалел!",
        "en": "waited for the darkest night so the stars "
              "would be brighter. no regrets!",
    },
    {
        "ru": "кажется, рядом с этой звездой есть планета. "
              "назову её потом. сейчас — звезда для {name}!",
        "en": "i think there's a planet near this star. "
              "will name it later. for now — a star for {name}!",
    },
    {
        "ru": "эту звезду видно даже без телескопа. "
              "но с телескопом она ещё красивее!",
        "en": "you can see this star even without a telescope. "
              "but with one it's even prettier!",
    },
    {
        "ru": "пока искал звезду, увидел спутник. помахал ему! "
              "он не ответил. ну и ладно.",
        "en": "while looking for a star, i spotted a satellite. waved at it! "
              "it didn't wave back. oh well.",
    },
    {
        "ru": "у этой звезды тёплый свет. такой уютный, "
              "как будто она улыбается.",
        "en": "this star has a warm glow. so cozy, "
              "like it's smiling.",
    },
    {
        "ru": "нашёл новую звезду! ну, новую для меня. "
              "она-то горит уже давно. но имя — свежее!",
        "en": "found a new star! well, new to me. "
              "it's been burning for ages. but the name is fresh!",
    },
    {
        "ru": "смотрел так долго, что увидел, как звезда "
              "чуть сдвинулась. или это я задремал...",
        "en": "stared so long that i saw the star "
              "shift a tiny bit. or maybe i dozed off...",
    },
    {
        "ru": "говорят, у каждого есть своя звезда. "
              "теперь у {name} — точно есть!",
        "en": "they say everyone has their own star. "
              "now {name} definitely has one!",
    },
    {
        "ru": "после того как назвал звезду, небо стало "
              "казаться ещё красивее. вот что делает имя!",
        "en": "after naming the star, the sky seemed "
              "even more beautiful. that's what a name does!",
    },
    {
        "ru": "когда-нибудь я назову все звёзды. "
              "но первая — всегда самая важная ⭐",
        "en": "someday i'll name all the stars. "
              "but the first one is always the most important ⭐",
    },
]

SHELL_STORIES = [
    # --- 1-10 ---
    {
        "ru": "нашёл эту ракушку на самом краю берега. "
              "она как будто ждала, что кто-то её заберёт :3",
        "en": "found this shell at the very edge of the shore. "
              "it was like it was waiting for someone to pick it up :3",
    },
    {
        "ru": "приложи к уху — слышишь море? "
              "я тоже каждый раз слышу, хотя живу рядом.",
        "en": "hold it to your ear — can you hear the sea? "
              "i hear it every time too, even though i live right here.",
    },
    {
        "ru": "эта ракушка идеально спиральная! считал завитки — "
              "их семь. моё любимое число.",
        "en": "this shell is perfectly spiral! i counted the swirls — "
              "there are seven. my favorite number.",
    },
    {
        "ru": "искал ракушку для {name} очень долго. "
              "но когда нашёл эту — сразу понял: она!",
        "en": "was looking for a shell for {name} for a long time. "
              "but when i found this one — i just knew: this is it!",
    },
    {
        "ru": "эта маленькая, но зато блестит на солнце, "
              "как будто с жемчужинкой внутри.",
        "en": "this one's small, but it sparkles in the sun, "
              "like there's a tiny pearl inside.",
    },
    {
        "ru": "знаешь, ракушки — это домики тех, кто уже уехал. "
              "пустой домик — значит, можно забрать на память!",
        "en": "you know, shells are little houses of those who moved out. "
              "an empty house means you can keep it as a souvenir!",
    },
    {
        "ru": "шёл по берегу, смотрел под ноги... и вдруг — "
              "самая красивая ракушка, которую я видел! для {name}.",
        "en": "was walking along the shore, looking down... and suddenly — "
              "the most beautiful shell i've ever seen! for {name}.",
    },
    {
        "ru": "эта ракушка розовая внутри! "
              "цвет заката, застывший навсегда.",
        "en": "this shell is pink on the inside! "
              "the color of a sunset, frozen forever.",
    },
    {
        "ru": "подобрал, помыл в волне, и она засияла. "
              "иногда красоту надо просто отмыть от песка.",
        "en": "picked it up, rinsed it in a wave, and it started glowing. "
              "sometimes beauty just needs to be washed off the sand.",
    },
    {
        "ru": "другие крабы говорят: зачем тебе ракушки, у тебя свой панцирь! "
              "а я говорю: это не для меня, это для {name} :3",
        "en": "other crabs say: why do you need shells, you have your own shell! "
              "and i say: it's not for me, it's for {name} :3",
    },
    # --- 11-20 ---
    {
        "ru": "тут раньше жил маленький рак-отшельник. "
              "он оставил записку: «передай кому-нибудь хорошему». вот!",
        "en": "a little hermit crab used to live here. "
              "he left a note: 'pass it to someone nice.' here you go!",
    },
    {
        "ru": "эту ракушку принесло волной прямо к моим клешням. "
              "кажется, океан тоже хочет сделать подарок {name}!",
        "en": "the wave brought this shell right to my claws. "
              "i think the ocean also wants to give a gift to {name}!",
    },
    {
        "ru": "у этой ракушки полосочки — белые и коричневые. "
              "как маленький полосатый домик!",
        "en": "this shell has stripes — white and brown. "
              "like a tiny striped house!",
    },
    {
        "ru": "нашёл две одинаковые ракушки! одну оставил себе, "
              "другую — {name}. теперь у нас парные :3",
        "en": "found two identical shells! kept one for myself, "
              "the other — for {name}. now we have a matching pair :3",
    },
    {
        "ru": "сидел на камне, и ракушка просто лежала рядом. "
              "иногда лучшие находки — те, что не ищешь.",
        "en": "was sitting on a rock, and a shell was just lying there. "
              "sometimes the best finds are the ones you're not looking for.",
    },
    {
        "ru": "эта ракушка пахнет морем и солнцем. "
              "самый лучший запах на свете.",
        "en": "this shell smells like the sea and sun. "
              "the best smell in the world.",
    },
    {
        "ru": "гладкая, тёплая от солнца, идеально ложится в клешню. "
              "а в ладошку {name} — наверняка ещё лучше!",
        "en": "smooth, warm from the sun, fits perfectly in my claw. "
              "and in {name}'s hand — probably even better!",
    },
    {
        "ru": "собирал ракушки целый час! но только эта "
              "достойна стать подарком.",
        "en": "was collecting shells for a whole hour! but only this one "
              "is worthy of being a gift.",
    },
    {
        "ru": "когда я был совсем маленьким крабиком, "
              "мне тоже подарили ракушку. теперь моя очередь!",
        "en": "when i was a tiny little crab, "
              "someone gave me a shell too. now it's my turn!",
    },
    {
        "ru": "на этой ракушке есть узор, похожий на звёздочку. "
              "морская звезда, наверное, оставила автограф!",
        "en": "this shell has a pattern that looks like a star. "
              "a starfish probably left an autograph!",
    },
    # --- 21-30 ---
    {
        "ru": "говорят, каждая ракушка помнит все волны, "
              "которые её качали. целая жизнь в одной раковине.",
        "en": "they say every shell remembers all the waves "
              "that rocked it. a whole life in one shell.",
    },
    {
        "ru": "прятал эту ракушку от чаек! они тоже хотели, "
              "но я сказал — нет, это для {name}.",
        "en": "was hiding this shell from seagulls! they wanted it too, "
              "but i said — no, this is for {name}.",
    },
    {
        "ru": "нашёл на дне маленькой лужицы между камнями. "
              "целая вселенная в одной ракушке!",
        "en": "found it at the bottom of a tiny pool between rocks. "
              "a whole universe in one shell!",
    },
    {
        "ru": "эта ракушка переливается перламутром. "
              "как маленькая радуга, которую можно держать в руке!",
        "en": "this shell shimmers with mother-of-pearl. "
              "like a little rainbow you can hold in your hand!",
    },
    {
        "ru": "волна унесла мою первую находку... "
              "но вторая оказалась ещё красивее. так бывает!",
        "en": "the wave swept away my first find... "
              "but the second one turned out even prettier. that happens!",
    },
    {
        "ru": "закопал ракушку в песок, а потом откопал. "
              "теперь это «найденное сокровище» — так ценнее!",
        "en": "buried the shell in the sand, then dug it up. "
              "now it's a 'found treasure' — that makes it more valuable!",
    },
    {
        "ru": "кажется, внутри этой ракушки кто-то нарисовал спираль. "
              "природа — лучший художник!",
        "en": "it looks like someone painted a spiral inside this shell. "
              "nature is the best artist!",
    },
    {
        "ru": "маленькая ракушка, но если приглядеться — "
              "видны крошечные детали. мир в миниатюре!",
        "en": "a small shell, but if you look closely — "
              "you can see tiny details. a world in miniature!",
    },
    {
        "ru": "нёс эту ракушку в клешне очень осторожно. "
              "хрупкая, как доверие. и такая же ценная.",
        "en": "carried this shell in my claw very carefully. "
              "fragile, like trust. and just as precious.",
    },
    {
        "ru": "эта ракушка звенит, если постучать! "
              "маленький морской колокольчик для {name} :3",
        "en": "this shell rings if you tap it! "
              "a little sea bell for {name} :3",
    },
    # --- 31-40 ---
    {
        "ru": "ой, а эта с дырочкой — можно повесить на верёвочку "
              "и носить как кулон! модно же?",
        "en": "oh, this one has a hole — you could hang it on a string "
              "and wear it as a pendant! that's fashionable, right?",
    },
    {
        "ru": "в каждой ракушке живёт эхо. "
              "в этой — эхо счастливого дня.",
        "en": "every shell holds an echo. "
              "this one holds the echo of a happy day.",
    },
    {
        "ru": "шёл за одной ракушкой, нашёл другую, "
              "а потом ещё одну... но эта — самая-самая!",
        "en": "went after one shell, found another, "
              "then one more... but this one is the very best!",
    },
    {
        "ru": "рассматривал её на закате — она стала золотой! "
              "на рассвете, наверное, будет серебряной.",
        "en": "was admiring it at sunset — it turned golden! "
              "at sunrise it'll probably be silver.",
    },
    {
        "ru": "если собрать много ракушек, можно выложить мозаику. "
              "но пока — одну самую лучшую для {name}.",
        "en": "if you collect many shells, you can make a mosaic. "
              "but for now — the very best one for {name}.",
    },
    {
        "ru": "эту ракушку я нашёл там, где волны "
              "рисуют узоры на песке. волшебное место!",
        "en": "found this shell where the waves "
              "draw patterns in the sand. a magical place!",
    },
    {
        "ru": "ракушка выглядит обычной... но переверни — "
              "а там целая картина из перламутра!",
        "en": "the shell looks ordinary... but flip it over — "
              "and there's a whole painting in mother-of-pearl!",
    },
    {
        "ru": "она чуть-чуть щербатая сбоку. "
              "не идеальная — зато настоящая. как я!",
        "en": "it's a tiny bit chipped on the side. "
              "not perfect — but real. like me!",
    },
    {
        "ru": "положил ракушку на ладонь и загадал желание. "
              "не скажу какое — а то не сбудется!",
        "en": "put the shell on my palm and made a wish. "
              "won't tell you what — or it won't come true!",
    },
    {
        "ru": "коллекция ракушек {name} становится всё больше! "
              "скоро понадобится отдельная полка :3",
        "en": "{name}'s shell collection is growing! "
              "soon you'll need a separate shelf :3",
    },
]


_STORIES = {
    "fish": FISH_STORIES,
    "magic": MAGIC_STORIES,
    "star": STAR_STORIES,
    "shell": SHELL_STORIES,
}


def _get_stories(gift_type):
    """Return the story list for a gift type (fish stories for test gifts)."""
    return _STORIES.get(gift_type, FISH_STORIES)


def random_story_id(gift_type):
    """Return a random story index for the given gift type."""
    stories = _get_stories(gift_type)
    return random.randint(0, len(stories) - 1)


def get_story(gift_type, story_id, name=""):
    """Return the translated story text for a gift."""
    stories = _get_stories(gift_type)
    if story_id < 0 or story_id >= len(stories):
        story_id = story_id % len(stories) if stories else 0
    lang = get_language()
    text = stories[story_id].get(lang, stories[story_id]["en"])
    # Handle {name} placeholder
    if name:
        text = text.replace("{name}", name)
    else:
        # Clean removal: preposition+name phrases (space-delimited to avoid
        # matching inside words like "чтО {name}")
        for pattern in [
            " для {name}", " о {name}", " с {name}",
            " for {name}", " of {name}", " after {name}", " about {name}",
            "{name}'s ", ", {name}", " {name}", "{name} ", "{name}",
        ]:
            text = text.replace(pattern, "")
        # Clean up double spaces and orphaned punctuation
        while "  " in text:
            text = text.replace("  ", " ")
        for p in [" .", " ,", " !", " ?"]:
            text = text.replace(p, p.strip())
    return text.strip()
