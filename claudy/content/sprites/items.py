"""Pixel art for the things Claudy gives away, keeps and dreams about.

Each image is a text grid; symbols map to ITEM_COLORS. Unlike particles,
items are drawn on Claudy's own pixel grid (ITEM_SCALE): a gift is an object
in his world, not an effect, and on the finer particle grid it reads as an
icon borrowed from somewhere else.

GIFT_ART maps the emoji a gift is offered under to its picture. DREAM_ART
maps an activity to what Claudy may dream of having done.
"""

from claudy.content.sprites.particles import PARTICLE_SCALE

ITEM_SCALE = 5      # config.PIXEL_SCALE; a test keeps the two in step

# The named star is the one exception: it hangs far away in the night sky
# instead of standing on the Dock, so it is drawn on the finer particle grid.
# At Claudy's own scale a star reads as an object left hanging in mid-air
# rather than as something distant.
SKY_SCALE = PARTICLE_SCALE

ITEM_COLORS = {
    "e": "#2D2D2D",  # eye
    "c": "#FFF8EE",  # eye glint
    "b": "#4D9BE0",  # fish body
    "B": "#AFD8F6",  # fish belly
    "f": "#2E7BC4",  # fins and tail
    "o": "#FF8A1F",  # pufferfish
    "O": "#FFC27A",  # pufferfish belly
    "q": "#D9640F",  # pufferfish fins and tail
    "u": "#7A9BF5",  # periwinkle (gem, wings, the rainbow's inner band)
    "U": "#C7ECFF",  # pale blue
    "v": "#5373D6",  # gem shade
    "y": "#FFD24A",  # gold
    "Y": "#FFF0B0",  # gold light
    "Z": "#F2B233",  # deep gold (the named star's ray tips)
    "p": "#F6A5B8",  # shell and petal pink
    "m": "#DD6E8E",  # deep pink (ribs, petal shade)
    "n": "#5DBB63",  # green
    "x": "#E4533D",  # red
    "w": "#9A6B45",  # teddy brown
    "W": "#BE8C5E",  # teddy light brown
    "k": "#5F3E26",  # teddy nose
    "g": "#A7A7B5",  # butterfly body
    "s": "#E8C67C",  # sand
    "S": "#C49A55",  # sand shade
    "h": "#F4F5FB",  # dream cloud
    "H": "#DADDEE",  # dream cloud underside
    "l": "#9EA5C0",  # dream cloud edge
}

ITEM_ART = {
    "fish": """
        ...ff....
        .bbbbb..f
        bbbbbbbff
        bebbbbbf.
        bBBBbbbff
        .bbbbb..f
        ...ff....
    """,
    "puffer": """
        .o..o..o...
        ..ooooo....
        .ceooooo..q
        oeeooooooqq
        ooOOOooooqq
        .oOOOooo..q
        ..ooooo....
        .o..o..o...
    """,
    "diamond": """
        ..uuuuu..
        .uUUuUuu.
        uuuuuuuuu
        .uUuuuvv.
        ..uUuvv..
        ...uvv...
        ....v....
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
        .xxyyyyyxx.
        xyynnnnnyyx
        xynnuuunnyx
        xynu...unyx
        xynu...unyx
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
        ..ppppp..
        .ppppppp.
        pmppmppmp
        pmppmppmp
        .pmpmpmp.
        ..pmpmp..
        ...ppp...
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
    "book": """
        ..ccc.ccc..
        .ccccgcccc.
        xcggcgcggcx
        xccccgccccx
        xcggcgcggcx
        xccccgccccx
        xxxxxxxxxxx
    """,
    # The landscape Claudy paints on his easel: sun top right, hill below left
    "canvas": """
        wwwwwwwww
        wUUUUyyUw
        wUUUUyyUw
        wUUUUUUUw
        wnnnUUUUw
        wnnnnnnnw
        wwwwwwwww
    """,
    "sandcastle": """
        .....xx....
        .....w.....
        ....sss....
        s.s.sss.s.s
        sssssssssss
        sssssssssss
        ssssSSSssss
        ssssSSSssss
    """,
    # The cloud a dream floats in, with its trail of bubbles down to the
    # sleeper. Round lobes, a cool edge and a shaded underside: a thought, not
    # the speech bubble's stepped box with its dark ink.
    "dream_cloud": """
        ........llll.........
        ....ll.lhhhhl.lll....
        ...lhhlhhhhhhlhhhl...
        ..lhhhhhhhhhhhhhhhl..
        .lhhhhhhhhhhhhhhhhhl.
        .lhhhhhhhhhhhhhhhhhl.
        lhhhhhhhhhhhhhhhhhhhl
        lHhhhhhhhhhhhhhhhhhHl
        .lhhhhhhhhhhhhhhhhhl.
        .lhhhhhhhhhhhhhhhhhl.
        lhhhhhhhhhhhhhhhhhhhl
        lHhhhhhhhhhhhhhhhhhHl
        .lHhhhhhHhhhhhhhHHHl.
        ..lHhhhHlHhhhhhHlll..
        ...lHHHl.lHHHHHl.....
        ....lll...lllll......
        .........lhhl........
        ........lhhhhl.......
        ........lHhhHl.......
        .........lHHl........
        ..........ll.........
        ........ll...........
        .......lhhl..........
        .......lHHl..........
        ........ll...........
    """,
    # The named star twinkles by changing shape, not by fading: faded, its
    # gold turns khaki over a dark sky and vanishes over a light window
    "sky_star": """
        ...Z...
        ...y...
        ..yYy..
        ZyYcYyZ
        ..yYy..
        ...y...
        ...Z...
    """,
    "sky_star_dim": """
        .......
        ...Z...
        ...y...
        .ZyYyZ.
        ...y...
        ...Z...
        .......
    """,
    "sky_star_flash": """
        ...y...
        ...Y...
        ..yYy..
        yYYcYYy
        ..yYy..
        ...Y...
        ...y...
    """,
}

# Pictures not drawn on Claudy's own pixel grid (see SKY_SCALE)
ITEM_SCALES = {name: SKY_SCALE
               for name in ("sky_star", "sky_star_dim", "sky_star_flash")}

# The gift Claudy leaves on the Dock, by the emoji it is offered under
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

# The star Claudy named after the user, kept in the night sky: how it
# twinkles, as (picture, ms) steps. A few uneven steps rather than a smooth
# cycle, so it reads as a star and not as a status light, and so its window
# is redrawn only a handful of times per cycle.
NAMED_STAR = "sky_star"
STAR_TWINKLE = (("sky_star", 1600), ("sky_star_dim", 500),
                ("sky_star", 1100), ("sky_star_flash", 250),
                ("sky_star", 900), ("sky_star_dim", 350))

# The cloud a dream floats in
DREAM_CLOUD = "dream_cloud"

# What Claudy may dream of, by the activity that left it in his head. An
# activity missing here leaves no picture behind: he dreams of what stayed,
# not of everything he did.
DREAM_ART = {
    "reading": ("book",),
    "fishing": ("fish", "puffer"),
    "shell_collecting": ("shell",),
    "magic": ("flower", "rainbow", "butterfly"),
    "telescope": ("star",),
    "painting": ("canvas",),
    "sandcastle": ("sandcastle",),
}
