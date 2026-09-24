"""Pixel art for particles (hearts, notes, sparkles...).

Each image is a small text grid; symbols map to PARTICLE_COLORS. Particles
are drawn at PARTICLE_SCALE screen pixels per art pixel — a little finer
than Claudy's own pixels.
"""

PARTICLE_SCALE = 3

PARTICLE_COLORS = {
    "r": "#FF6B8A",  # heart red-pink
    "R": "#FFC2CF",  # heart shine
    "y": "#FFD24A",  # gold
    "Y": "#FFF3B0",  # gold shine
    "o": "#FF8A1F",  # orange
    "O": "#E0602A",  # deep orange
    "p": "#C084FC",  # purple
    "P": "#E6CCFF",  # light purple
    "k": "#4B3A5A",  # dark (butterfly body)
    "b": "#8BA4C4",  # sleepy blue
    "u": "#60A5FA",  # blue
    "U": "#D6EBFF",  # light blue
    "c": "#FFF8EE",  # cream paper
    "g": "#A7A7B5",  # gray
    "G": "#D9D9E0",  # light gray
    "w": "#F4F4F8",  # white
    "x": "#F0564A",  # red
    "i": "#FF9EC0",  # pink petals
}

# Colors the rainbow sparkle cycles through
RAINBOW = ["#FF5A5A", "#FF9F40", "#FFE14D", "#5BD46B", "#4DA3FF",
           "#7A6CFF", "#C07CFF"]

# Juggling balls are "ball" images in these colors
JUGGLE_BALL_COLORS = ("#FF5A5A", "#4DA3FF", "#FFD23F")

PARTICLE_ART = {
    "heart": """
        .rr.rr.
        rRrrrrr
        rrrrrrr
        .rrrrr.
        ..rrr..
        ...r...
    """,
    "sparkle": """
        ..y..
        ..y..
        yyYyy
        ..y..
        ..y..
    """,
    "sparkle_small": """
        .y.
        yYy
        .y.
    """,
    "star": """
        ...y...
        ..yyy..
        yyyYyyy
        .yyyyy.
        ..yyy..
        .yy.yy.
        .y...y.
    """,
    "note": """
        ..pp.
        ..p.p
        ..p..
        ..p..
        ppp..
        ppp..
    """,
    "note_beamed": """
        ..ppppp
        ..p...p
        ..p...p
        ..p...p
        ppp.ppp
        ppp.ppp
    """,
    "z_big": """
        bbbbb
        ...b.
        ..b..
        .b...
        bbbbb
    """,
    "z_small": """
        bbbb
        ..b.
        .b..
        bbbb
    """,
    "sweat": """
        .u..
        .uu.
        uUuu
        uuuu
        .uu.
    """,
    "question": """
        .yyy.
        y...y
        ....y
        ..yy.
        ..y..
        .....
        ..y..
    """,
    "exclaim": """
        xx
        xx
        xx
        xx
        ..
        xx
    """,
    "flower_pink": """
        ..i..
        .iii.
        iiyii
        .iii.
        ..i..
    """,
    "flower_yellow": """
        ..y..
        .yyy.
        yyoyy
        .yyy.
        ..y..
    """,
    "flower_red": """
        ..x..
        .xxx.
        xxyxx
        .xxx.
        ..x..
    """,
    "butterfly_open": """
        pp...pp
        pPpkpPp
        .ppkpp.
        .pp.pp.
    """,
    "butterfly_closed": """
        ..p.p..
        ..pkp..
        ..pkp..
        ...k...
    """,
    "poof": """
        ..ww...
        .wwwww.
        wwGwwww
        .wwwwG.
    """,
    "dust": """
        .GG..
        GGGGG
        .GGG.
    """,
    "code_tag": """
        ..u...u.u..
        .u....u..u.
        u....u....u
        .u..u....u.
        ..u.u...u..
    """,
    "code_braces": """
        .uu.uu.
        .u...u.
        u.....u
        .u...u.
        .uu.uu.
    """,
    "code_bits": """
        uuu..u.
        u.u.uu.
        u.u..u.
        u.u..u.
        uuu.uuu
    """,
    "page": """
        cccc
        cggc
        cccc
        cggc
        cccc
    """,
    "flame": """
        ..o..
        ..oo.
        .ooo.
        .oyoo
        ooyyo
        oyYyo
        .ooo.
    """,
    "ember": """
        oO
        Oo
    """,
    "spark": """
        y
    """,
    "ball": """
        .yyy.
        yYyyy
        yyyyy
        yyyyy
        .yyy.
    """,
}
