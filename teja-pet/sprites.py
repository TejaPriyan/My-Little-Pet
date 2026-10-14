"""Procedural pixel-art painters.

Everything the game draws can be produced here, so TEJA PET runs with zero
external art. `tools/generate_assets.py` exports these as real PNG files which
can then be edited or replaced - assets.py always prefers files on disk.
"""
import random

import pygame

from config import FRAME, W, H, HUD_H, FLOOR_Y, INK

OUT = INK
PINK = (255, 150, 190)
WHITE = (255, 255, 255)


def _s(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _shift(surf, dx, dy):
    out = _s(*surf.get_size())
    out.blit(surf, (dx, dy))
    return out


def strip(frames):
    """Lay frames out horizontally into one sprite-sheet surface."""
    fw, fh = frames[0].get_size()
    sheet = _s(fw * len(frames), fh)
    for i, f in enumerate(frames):
        sheet.blit(f, (i * fw, 0))
    return sheet


# =====================================================================
# ROOM
# =====================================================================
def _rrect(s, rect, fill, border=OUT):
    """Pixel rounded rectangle (corner pixels removed)."""
    x, y, w, h = rect
    s.fill(border, (x + 1, y, w - 2, h))
    s.fill(border, (x, y + 1, w, h - 2))
    s.fill(fill, (x + 1, y + 1, w - 2, h - 2))


def make_room():
    rh = 244 - HUD_H
    s = pygame.Surface((W, rh))
    wall_h = FLOOR_Y - HUD_H
    rng = random.Random(7)
    # wallpaper: soft peach with vertical stripes and tiny dots
    s.fill((242, 218, 208), (0, 0, W, wall_h))
    for x in range(0, W, 16):
        s.fill((234, 206, 198), (x, 0, 8, wall_h))
    for x in range(4, W, 16):
        for y in range(6, wall_h - 8, 14):
            s.set_at((x, y), (250, 232, 224))
            s.set_at((x + 8, y + 7), (222, 192, 186))
    s.fill((205, 160, 150), (0, 0, W, 3))                       # crown moulding
    s.fill((226, 186, 172), (0, 3, W, 1))
    s.fill((196, 134, 108), (0, wall_h - 5, W, 5))              # baseboard
    s.fill((222, 160, 128), (0, wall_h - 5, W, 1))
    s.fill((120, 78, 62), (0, wall_h, W, 1))
    # wooden floor planks
    plank_h = 12
    tones = [(214, 160, 110), (206, 152, 104), (220, 168, 118)]
    for row in range((rh - wall_h) // plank_h + 1):
        y = wall_h + 1 + row * plank_h
        off = (row * 37) % 64
        for px in range(-64, W, 64):
            x = px + off
            col = tones[rng.randrange(3)]
            s.fill(col, (x, y, 64, plank_h))
            for _ in range(5):
                gx, gy = x + rng.randrange(64), y + rng.randrange(plank_h - 2)
                s.fill((col[0] - 14, col[1] - 14, col[2] - 12), (gx, gy, rng.randrange(3, 8), 1))
            s.fill((158, 108, 78), (x, y, 1, plank_h))
        s.fill((166, 114, 82), (0, y + plank_h - 1, W, 1))
    # soft shadow where wall meets floor
    sh = _s(W, 7)
    for i in range(7):
        sh.fill((60, 30, 30, 70 - i * 10), (0, i, W, 1))
    s.blit(sh, (0, wall_h + 1))
    return s


def make_bed():
    s = _s(64, 40)
    wood, wood_dk, wood_lt = (184, 120, 86), (140, 88, 66), (214, 152, 110)
    for x in (4, 54):
        _rrect(s, (x, 33, 6, 7), wood_dk)
    _rrect(s, (7, 7, 54, 22), (246, 232, 204))                   # mattress
    _rrect(s, (10, 9, 17, 11), WHITE)                            # pillow
    s.fill((226, 220, 240), (12, 17, 13, 1))
    _rrect(s, (30, 9, 31, 20), (112, 190, 204))                  # blanket
    for x in (38, 46, 54):
        s.fill((140, 210, 220), (x, 11, 2, 16))
    s.fill((150, 220, 228), (31, 10, 3, 18))
    _rrect(s, (2, 24, 60, 11), wood)                             # front board
    s.fill(wood_lt, (4, 25, 56, 1))
    s.fill(wood_dk, (4, 33, 56, 1))
    _rrect(s, (0, 2, 9, 33), wood_dk)                            # headboard
    s.fill(wood, (2, 4, 4, 29))
    return s


def _bowl(color, content):
    s = _s(16, 10)
    pygame.draw.ellipse(s, OUT, (0, 3, 16, 7))
    pygame.draw.ellipse(s, color, (1, 4, 14, 5))
    pygame.draw.ellipse(s, OUT, (0, 0, 16, 7))
    pygame.draw.ellipse(s, (96, 64, 72) if content != "water" else (120, 200, 240), (1, 1, 14, 5))
    if content == "kibble":
        for x, y in ((3, 2), (6, 1), (9, 2), (12, 2), (5, 3), (8, 3), (11, 3), (7, 2)):
            s.fill((196, 124, 74), (x, y, 2, 2))
            s.set_at((x, y), (232, 164, 100))
    elif content == "water":
        s.fill((200, 240, 255), (4, 2, 3, 1))
        s.fill((200, 240, 255), (9, 3, 2, 1))
    return s


def make_food():
    return [_bowl((255, 120, 150), "kibble"), _bowl((255, 120, 150), "empty")]


def make_water():
    return [_bowl((110, 170, 240), "water")]


def make_toy():
    s = _s(10, 10)
    pygame.draw.circle(s, OUT, (5, 5), 5)
    pygame.draw.circle(s, (255, 96, 110), (5, 5), 4)
    s.fill(WHITE, (1, 4, 8, 2))
    s.fill((255, 96, 110), (4, 4, 2, 2))
    s.fill(WHITE, (3, 2, 2, 1))
    return s


def make_table():
    s = _s(36, 32)
    wood, wood_dk = (200, 138, 98), (146, 92, 68)
    for x in (4, 28):
        _rrect(s, (x, 19, 4, 13), wood_dk)
    _rrect(s, (1, 10, 34, 8), wood)
    s.fill((226, 170, 126), (3, 11, 30, 1))
    s.fill(wood_dk, (3, 16, 30, 1))
    _rrect(s, (14, 3, 8, 8), (110, 170, 240))                   # vase
    s.fill((170, 210, 255), (15, 4, 2, 5))
    for x, y, c in ((15, 0, PINK), (19, -1, (255, 220, 90)), (21, 1, PINK)):
        if y >= 0:
            s.fill(c, (x, y, 3, 3))
    s.fill((96, 170, 96), (18, 1, 1, 3))
    return s


def make_plant():
    frames = []
    for sw in (-1, 0, 1, 0):
        s = _s(24, 34)
        leaf, leaf_dk = (96, 190, 110), (52, 120, 82)
        tips = ((2 + sw, 10), (12 + sw * 2, 2), (22 + sw, 9), (6 + sw, 16), (18 + sw, 16))
        for tx, ty in tips:
            mx, my = (12 + tx) // 2, (25 + ty) // 2
            pts = [(12, 25), (mx - 3, my), (tx, ty), (mx + 3, my)]
            pygame.draw.polygon(s, leaf, pts)
            pygame.draw.polygon(s, leaf_dk, pts, 1)
        _rrect(s, (5, 23, 14, 11), (218, 120, 84))              # terracotta pot
        s.fill((240, 150, 110), (6, 24, 12, 1))
        s.fill((90, 60, 50), (6, 24, 12, 2))
        s.fill((190, 98, 70), (6, 31, 12, 2))
        frames.append(s)
    return frames


def make_window():
    s = _s(52, 40)
    s.fill(OUT, (0, 0, 52, 36))
    s.fill((250, 244, 236), (2, 2, 48, 32))
    s.fill((0, 0, 0, 0), (4, 4, 44, 28))                         # glass hole
    s.fill((250, 244, 236), (25, 4, 2, 28))
    s.fill((250, 244, 236), (4, 17, 44, 2))
    _rrect(s, (-1, 34, 54, 6), (214, 160, 120))
    for x, w in ((0, 8), (44, 8)):                                # curtains
        s.fill(OUT, (x, 2, w, 31))
        s.fill((255, 170, 190), (x + 1, 3, w - 2, 29))
        for fx in range(x + 2, x + w - 1, 3):
            s.fill((234, 140, 166), (fx, 3, 1, 29))
    return s


def make_door():
    s = _s(34, 58)
    _rrect(s, (0, 0, 34, 58), (150, 96, 72))
    s.fill((196, 134, 98), (2, 2, 30, 54))
    for rect in ((5, 6, 24, 18), (5, 28, 24, 24)):
        s.fill((166, 108, 78), rect)
        s.fill((214, 156, 116), (rect[0], rect[1], rect[2], 1))
    pygame.draw.circle(s, OUT, (17, 15), 6)
    pygame.draw.circle(s, (150, 214, 245), (17, 15), 5)
    s.fill(WHITE, (14, 12, 2, 2))
    pygame.draw.circle(s, (255, 205, 70), (27, 36), 2)
    _rrect(s, (11, 44, 12, 9), (150, 96, 72))                     # pet flap
    return s


def make_rug():
    s = _s(150, 56)
    pygame.draw.ellipse(s, OUT, (0, 0, 150, 56))
    pygame.draw.ellipse(s, (232, 118, 140), (2, 2, 146, 52))
    pygame.draw.ellipse(s, (255, 236, 214), (10, 6, 130, 44))
    pygame.draw.ellipse(s, (110, 190, 190), (16, 9, 118, 38))
    pygame.draw.ellipse(s, (255, 214, 120), (30, 15, 90, 26))
    pygame.draw.ellipse(s, (232, 118, 140), (44, 20, 62, 16))
    for x in range(22, 130, 12):
        s.fill((255, 236, 214), (x, 27, 3, 3))
    return s


def make_decorations():
    d = _s(90, 26)
    _rrect(d, (0, 0, 22, 26), (184, 120, 86))                     # picture frame
    d.fill((170, 220, 250), (2, 2, 18, 22))
    d.fill((120, 190, 120), (2, 15, 18, 9))
    pygame.draw.circle(d, (255, 220, 90), (14, 8), 3)
    d.fill((96, 160, 100), (2, 19, 18, 5))
    sh = _s(36, 22)                                                # wall shelf
    _rrect(sh, (0, 16, 36, 5), (184, 120, 86))
    for x, w, c in ((3, 4, (240, 120, 130)), (8, 4, (120, 170, 240)), (13, 5, (250, 210, 100))):
        _rrect(sh, (x, 6, w, 10), c)
    _rrect(sh, (24, 9, 8, 7), (255, 255, 255))
    sh.fill(PINK, (26, 7, 4, 3))
    d.blit(sh, (22, 0))
    cu = _s(16, 10)                                                # cushion
    _rrect(cu, (0, 0, 16, 10), (255, 150, 180))
    cu.fill((255, 190, 212), (2, 2, 12, 2))
    d.blit(cu, (58, 0))
    cl = _s(16, 16)                                                # wall clock
    pygame.draw.circle(cl, OUT, (8, 8), 8)
    pygame.draw.circle(cl, (255, 250, 240), (8, 8), 6)
    cl.fill(OUT, (8, 4, 1, 5))
    cl.fill(OUT, (8, 8, 3, 1))
    d.blit(cl, (74, 0))
    return d


DECOR_SLICES = {"picture": (0, 0, 22, 26), "shelf": (22, 0, 36, 22),
                "cushion": (58, 0, 16, 10), "clock": (74, 0, 16, 16)}


# =====================================================================
# UI
# =====================================================================
def make_panel():
    s = _s(16, 16)
    s.fill(OUT, (1, 0, 14, 16))
    s.fill(OUT, (0, 1, 16, 14))
    s.fill((255, 244, 230), (1, 1, 14, 14))
    s.fill((255, 255, 255), (2, 1, 12, 1))
    s.fill((232, 208, 190), (2, 14, 12, 1))
    return s


def make_buttons():
    frames = []
    for fill, lo, hi in (((255, 208, 226), (232, 160, 190), (255, 232, 242)),
                         ((255, 230, 240), (240, 184, 210), (255, 250, 252)),
                         ((238, 172, 202), (208, 130, 166), (244, 196, 220))):
        s = _s(16, 16)
        s.fill(OUT, (1, 0, 14, 16))
        s.fill(OUT, (0, 1, 16, 14))
        s.fill(fill, (1, 1, 14, 14))
        s.fill(hi, (2, 1, 12, 1))
        s.fill(lo, (2, 13, 12, 2))
        frames.append(s)
    return strip(frames)


def _icon(draw):
    s = _s(9, 9)
    draw(s)
    return s


def _ic_heart(s):
    rows = (".kkk.kkk.", "kwrrkrrrk", "krrrrrrrk", "krrrrrrrk", ".krrrrrk.",
            "..krrrk..", "...krk...", "....k....")
    _blit_rows(s, rows, {"k": OUT, "w": (255, 210, 224), "r": (255, 92, 130)})


def _ic_apple(s):
    rows = ("....gg...", "...kg....", ".kkkkkkk.", "krrrkrrrk", "krwrrrrrk",
            "krrrrrrrk", ".krrrrrk.", "..kk.kk..")
    _blit_rows(s, rows, {"k": OUT, "g": (90, 190, 100), "r": (255, 96, 80), "w": (255, 190, 170)})


def _ic_bolt(s):
    pygame.draw.polygon(s, (255, 214, 60), [(5, 0), (1, 5), (4, 5), (3, 8), (8, 3), (5, 3)])
    pygame.draw.polygon(s, OUT, [(5, 0), (1, 5), (4, 5), (3, 8), (8, 3), (5, 3)], 1)


def _ic_coin(s):
    pygame.draw.circle(s, OUT, (4, 4), 4)
    pygame.draw.circle(s, (255, 205, 70), (4, 4), 3)
    s.fill((255, 240, 160), (3, 2, 1, 4))


def _ic_home(s):
    pygame.draw.polygon(s, OUT, [(4, 0), (8, 4), (0, 4)])
    pygame.draw.polygon(s, (255, 110, 110), [(4, 1), (7, 4), (1, 4)])
    s.fill(OUT, (1, 4, 7, 5))
    s.fill((255, 236, 214), (2, 5, 5, 3))
    s.fill(OUT, (4, 6, 1, 2))


def _ic_ball(s):
    pygame.draw.circle(s, OUT, (4, 4), 4)
    pygame.draw.circle(s, (255, 96, 110), (4, 4), 3)
    s.fill(WHITE, (1, 3, 7, 2))


def _ic_moon(s):
    pygame.draw.circle(s, OUT, (4, 4), 4)
    pygame.draw.circle(s, (255, 226, 120), (4, 4), 3)
    pygame.draw.circle(s, (0, 0, 0, 0), (6, 3), 3)


def _ic_paw(s):
    pygame.draw.ellipse(s, OUT, (2, 4, 6, 5))
    for x, y in ((0, 2), (2, 0), (5, 0), (7, 2)):
        s.fill(OUT, (x, y, 2, 3))


def _ic_gear(s):
    pygame.draw.circle(s, OUT, (4, 4), 4)
    pygame.draw.circle(s, (190, 190, 210), (4, 4), 3)
    pygame.draw.circle(s, OUT, (4, 4), 1)
    for x, y in ((3, 0), (3, 7), (0, 3), (7, 3)):
        s.fill(OUT, (x, y, 2, 2))


def _ic_star(s):
    rows = ("....y....", "....y....", "...yyy...", "yyyyyyyyy", ".yyyyyyy.",
            "..yyyyy..", "..yy.yy..", ".yy...yy.")
    _blit_rows(s, rows, {"y": (255, 220, 80)})


def _blit_rows(s, rows, pal):
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                s.set_at((x, y), pal[ch])


def _ic_spark(s):
    rows = ("....w....", "....y....", "...yyy...", ".yyywyyy.", "wyywwwyyw", ".yyywyyy.",
            "...yyy...", "....y....", "....w....")
    _blit_rows(s, rows, {"y": (255, 214, 70), "w": (255, 250, 210)})


def _ic_desk(s):
    rows = ("kkkkkkkkk", "kbbbbbbbk", "kbwbbbbbk", "kbbbbgbbk", "kbbbgggbk", "kkkkkkkkk",
            "...kkk...", "..kkkkk..")
    _blit_rows(s, rows, {"k": OUT, "b": (120, 190, 250), "w": (220, 240, 255), "g": (110, 200, 120)})


def _ic_pad(s):
    rows = (".........", ".kkkkkkk.", "kpppppppk", "kpkpppwpk", "kkkkpwpwk", "kpkpppwpk",
            "kppkkkppk", ".kk...kk.")
    _blit_rows(s, rows, {"k": OUT, "p": (190, 150, 240), "w": (255, 120, 150)})


def _ic_bow(s):
    rows = (".........", "kk.....kk", "kpk...kpk", "kppkkkppk", "kpppypppk", "kppkkkppk",
            "kpk...kpk", "kk.....kk")
    _blit_rows(s, rows, {"k": OUT, "p": (255, 110, 150), "y": (255, 214, 70)})


ICONS = {"heart": _ic_heart, "apple": _ic_apple, "bolt": _ic_bolt, "coin": _ic_coin,
         "home": _ic_home, "ball": _ic_ball, "moon": _ic_moon, "paw": _ic_paw,
         "gear": _ic_gear, "star": _ic_star, "spark": _ic_spark, "desk": _ic_desk,
         "pad": _ic_pad, "bow": _ic_bow}


def make_icons():
    names = list(ICONS)
    return names, strip([_icon(ICONS[n]) for n in names])


# =====================================================================
# SMALL EFFECT SPRITES
# =====================================================================
def make_fx():
    """Strip of 7x7 effect sprites: heart, sparkle, exclaim, note."""
    heart = _s(7, 7)
    _blit_rows(heart, (".rr.rr.", "rwrrrrr", "rrrrrrr", ".rrrrr.", "..rrr..", "...r..."),
               {"r": (255, 92, 130), "w": (255, 214, 226)})
    spark = _s(7, 7)
    _blit_rows(spark, ("...y...", "...y...", "..yyy..", "yyyyyyy", "..yyy..", "...y...", "...y..."),
               {"y": (255, 236, 120)})
    bang = _s(7, 7)
    _blit_rows(bang, ("..ooo..", "..ooo..", "..ooo..", "...o...", "...o...", ".......", "..ooo.."),
               {"o": (255, 120, 80)})
    note = _s(7, 7)
    _blit_rows(note, ("...bbb.", "...b.b.", "...b...", "...b...", ".bbb...", "bbbb...", ".bb...."),
               {"b": (140, 120, 240)})
    return strip([heart, spark, bang, note])


FX_NAMES = ("heart", "spark", "bang", "note")


def make_shadow():
    s = _s(16, 6)
    pygame.draw.ellipse(s, (40, 20, 40, 70), (0, 0, 16, 6))
    pygame.draw.ellipse(s, (40, 20, 40, 50), (2, 1, 12, 4))
    return s


def _outline(s, col=OUT):
    w, h = s.get_size()
    solid = [[s.get_at((x, y))[3] > 0 for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if solid[y][x]:
                continue
            if ((x > 0 and solid[y][x - 1]) or (x < w - 1 and solid[y][x + 1]) or
                    (y > 0 and solid[y - 1][x]) or (y < h - 1 and solid[y + 1][x])):
                s.set_at((x, y), col)
    return s


# =====================================================================
# DESKTOP HOME  (a little pet house the pet walks into to sleep)
# =====================================================================
def make_house():
    s = _s(64, 58)
    roof, roof_dk, roof_lt = (236, 104, 120), (196, 74, 98), (255, 146, 156)
    wall, wall_dk = (255, 238, 216), (232, 204, 178)
    s.fill((178, 120, 104), (44, 4, 9, 16))                         # chimney
    s.fill((206, 146, 126), (45, 4, 3, 16))
    s.fill((150, 96, 86), (43, 2, 11, 4))
    s.fill(wall, (8, 26, 48, 29))                                   # walls
    for y in range(30, 55, 5):
        s.fill(wall_dk, (9, y, 46, 1))
    pygame.draw.polygon(s, roof, [(1, 29), (32, 3), (62, 29)])      # roof
    for i, y in enumerate(range(10, 29, 5)):
        half = 3 + (y - 3) * 30 // 26
        s.fill(roof_dk, (32 - half, y, half * 2, 2))
    pygame.draw.polygon(s, roof_lt, [(6, 27), (32, 6), (34, 7), (9, 28)])
    s.fill(roof_dk, (2, 28, 60, 3))
    pygame.draw.circle(s, (70, 46, 64), (32, 41), 9)                # doorway
    s.fill((70, 46, 64), (23, 41, 19, 14))
    pygame.draw.circle(s, (104, 70, 92), (32, 42), 7)
    s.fill((104, 70, 92), (25, 42, 15, 13))
    s.fill((255, 150, 180), (21, 54, 23, 3))                        # door mat
    for x in (12, 45):                                              # windows
        s.fill((92, 140, 200), (x, 35, 8, 8))
        s.fill((170, 214, 255), (x + 1, 36, 3, 3))
        s.fill(wall, (x + 3, 35, 2, 8))
        s.fill(wall, (x, 38, 8, 2))
    pygame.draw.circle(s, (255, 214, 70), (32, 19), 4)              # round sign
    s.fill((255, 110, 150), (30, 18, 2, 2))
    s.fill((255, 110, 150), (33, 18, 2, 2))
    s.fill((255, 110, 150), (31, 20, 3, 2))
    _outline(s)
    return s


HOUSE_DOOR = (32, 55)        # bottom-centre of the doorway inside house.png
HOUSE_WINDOWS = ((12, 35, 8, 8), (45, 35, 8, 8))


# =====================================================================
# ACCESSORIES  (drawn on the pet's head anchor; bottom row overlaps head)
# =====================================================================
ACCESSORY_ART = {
    "hat": (("kk.....kk", "kpk...kpk", "kppkykppk", "kpk...kpk", "kk.....kk"),
            {"k": OUT, "p": (240, 70, 120), "y": (255, 214, 70)}),
    "flower": (("..kkk..", ".kpwpk.", "kpwywpk", "kwyyywk", "kpwywpk", ".kpwpk.", "..kkk.."),
               {"k": OUT, "p": (255, 130, 170), "w": (255, 220, 232), "y": (255, 214, 70)}),
    "party": (("...w...", "..kyk..", "..kbk..", ".kbwbk.", ".kwbwk.", "kbwbwbk", "kwbwbwk",
               "kkkkkkk"),
              {"k": OUT, "b": (110, 170, 255), "w": (255, 250, 240), "y": (255, 214, 70)}),
    "crown": (("k...k...k", "yk.kyk.ky", "yykyyykyy", "yyyyryyyy", "ywyyyyywy", "kkkkkkkkk"),
              {"k": OUT, "y": (255, 206, 60), "r": (240, 60, 90), "w": (255, 250, 200)}),
}


def make_accessories():
    out = {}
    for name, (rows, pal) in ACCESSORY_ART.items():
        s = _s(len(rows[0]), len(rows))
        _blit_rows(s, rows, pal)
        out[name] = s
    return out


# =====================================================================
# TREAT DROP mini-game items (12x12 each)
# =====================================================================
TREAT_NAMES = ("fish", "bone", "carrot", "berry", "cookie", "star", "thorn")


def make_treats():
    frames = []
    for name in TREAT_NAMES:
        s = _s(12, 12)
        if name == "fish":
            pygame.draw.ellipse(s, (120, 180, 240), (1, 3, 8, 6))
            pygame.draw.polygon(s, (90, 150, 220), [(8, 6), (11, 3), (11, 9)])
            s.fill((200, 230, 255), (2, 5, 4, 1))
            s.set_at((3, 5), OUT)
        elif name == "bone":
            s.fill((250, 244, 232), (3, 5, 6, 2))
            for x, y in ((1, 3), (1, 6), (8, 3), (8, 6)):
                pygame.draw.ellipse(s, (250, 244, 232), (x, y, 3, 3))
        elif name == "carrot":
            pygame.draw.polygon(s, (255, 150, 60), [(3, 4), (8, 4), (6, 11)])
            s.fill((90, 190, 100), (4, 1, 1, 3))
            s.fill((90, 190, 100), (6, 0, 1, 4))
            s.fill((90, 190, 100), (8, 1, 1, 3))
            s.fill((230, 120, 40), (5, 6, 2, 1))
        elif name == "berry":
            for x, y in ((2, 4), (6, 4), (4, 7)):
                pygame.draw.ellipse(s, (220, 60, 110), (x, y, 4, 4))
            s.fill((255, 170, 200), (3, 5, 1, 1))
            s.fill((90, 190, 100), (4, 1, 4, 2))
        elif name == "cookie":
            pygame.draw.ellipse(s, (214, 156, 96), (1, 1, 10, 10))
            for x, y in ((3, 3), (7, 4), (4, 7), (7, 8)):
                s.fill((110, 70, 50), (x, y, 2, 1))
        elif name == "star":
            pygame.draw.polygon(s, (255, 214, 60), [(6, 0), (8, 4), (11, 4), (9, 7), (10, 11),
                                                    (6, 9), (2, 11), (3, 7), (1, 4), (4, 4)])
            s.fill((255, 250, 200), (5, 4, 2, 2))
        else:                                                       # thorn: avoid!
            pygame.draw.circle(s, (110, 90, 130), (6, 6), 4)
            for x, y in ((6, 0), (6, 11), (0, 6), (11, 6), (2, 2), (9, 2), (2, 9), (9, 9)):
                s.set_at((x, y), (110, 90, 130))
            s.fill((255, 90, 90), (4, 5, 1, 1))
            s.fill((255, 90, 90), (7, 5, 1, 1))
        _outline(s)
        frames.append(s)
    return frames
