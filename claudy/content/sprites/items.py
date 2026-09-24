"""Pixel art for the things Claudy gives away and keeps.

Each image is a text grid; symbols map to ITEM_COLORS. Unlike particles,
items are drawn on Claudy's own pixel grid (ITEM_SCALE): a gift is an object
in his world, not an effect, and on the finer particle grid it reads as an
icon borrowed from somewhere else.

GIFT_ART maps the emoji a gift is stored under in memory.json to its picture,
so collections saved before these pictures existed keep working.
"""

ITEM_SCALE = 5      # config.PIXEL_SCALE; a test keeps the two in step

ITEM_COLORS = {
    "e": "#2D2D2D",  # eye
    "c": "#FFF8EE",  # eye glint
    "b": "#4D9BE0",  # fish body
    "B": "#AFD8F6",  # fish belly
    "f": "#2E7BC4",  # fins and tail
    "o": "#FF8A1F",  # pufferfish
    "u": "#7A9BF5",  # periwinkle (gem, wings, the rainbow's inner band)
    "U": "#C7ECFF",  # pale blue
    "y": "#FFD24A",  # gold
    "Y": "#FFF0B0",  # gold light
    "p": "#F6A5B8",  # shell and petal pink
    "m": "#DD6E8E",  # deep pink (ribs, petal shade)
    "n": "#5DBB63",  # green
    "x": "#E4533D",  # red
    "w": "#9A6B45",  # teddy brown
    "W": "#BE8C5E",  # teddy light brown
    "k": "#5F3E26",  # teddy nose
    "g": "#A7A7B5",  # butterfly body
}

ITEM_ART = {
    "fish": """
        ....ff....
        ..bbbbb..f
        .bbbbbbbff
        .bebbbbbf.
        .Bbbbbbbff
        ..BBbbb..f
        ....ff....
    """,
    "puffer": """
        ....ooo....
        .o.ooooo.o.
        ..ooooooo..
        o.ceooooo.o
        o.ooooooo.o
        ..ooooooo..
        .o.ooooo.o.
        ....ooo....
    """,
    "diamond": """
        ..UUUUU..
        .UuUuUuU.
        UuuuUuuuU
        .uuuUuuu.
        ..uuUuu..
        ...uuu...
        ....u....
    """,
    "star": """
        ....y....
        ...yYy...
        yyyyYyyyy
        .yyyyyyy.
        ..yyyyy..
        ..yy.yy..
        .yy...yy.
    """,
    "flower": """
        ..pp.pp..
        .ppppppp.
        ppmmYmmpp
        ppmYYYmpp
        ppmmYmmpp
        .ppppppp.
        ..pp.pp..
        ....n....
        ...nn....
    """,
    "rainbow": """
        ...xxxxx...
        ..xooooox..
        .xooyyyoox.
        xooynnnyoox
        xoynuuunyox
        xoynu.unyox
    """,
    "butterfly": """
        uuu.....uuu
        uUUuu.uuUUu
        uUUUuguUUUu
        .uUUuguUUu.
        ..uuuguuu..
        .uuu.g.uuu.
        .uUu.g.uUu.
        ..uu.g.uu..
    """,
    "shell": """
        ...ppppp...
        ..ppppppp..
        .pmppmppmp.
        .pmppmppmp.
        ..pmpmpmp..
        ...pmpmp...
        ....ppp....
    """,
    "teddy": """
        .ww...ww.
        wWWw.wWWw
        .wwwwwww.
        .wwwwwww.
        .weWWWew.
        .wwWkWww.
        wwwwwwwww
        .wWWWWWw.
        ..ww.ww..
    """,
}

# The gift Claudy leaves on the Dock, by the emoji it is stored under
GIFT_ART = {
    "\U0001F41F": "fish",       # 🐟
    "\U0001F421": "puffer",     # 🐡
    "\U0001F48E": "diamond",    # 💎
    "⭐": "star",           # ⭐
    "\U0001F338": "flower",     # 🌸
    "\U0001F308": "rainbow",    # 🌈
    "\U0001F98B": "butterfly",  # 🦋
    "\U0001F41A": "shell",      # 🐚
}

# What Claudy sleeps with after being given a toy
TOY = "teddy"
