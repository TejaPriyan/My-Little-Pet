"""Original pixel pet art: seven species, three coats and expressive poses.

Every pose is described as data (a small dict), rendered by a species "rig"
and finished with a clean 1-px silhouette outline. Because poses are data we
also know where the head is in every frame, which is how accessories (bow,
crown...) stay glued to the pet's head while it walks, hops and sleeps.

Frames are 24x24. Row 22 is the ground line (the game blits at y - 22).
"""
import pygame

from config import FRAME, INK

OUT = INK
EYE = (34, 26, 58)
WHITE = (255, 255, 255)
TEAR = (120, 200, 255)

# ----------------------------------------------------------------- coats
# Coat 0 is the "base" palette the PNGs are painted with; other coats are made
# by swapping these exact colours, so hand-edited PNGs can still be recoloured.
# Keep every colour unique inside a coat and different from OUT/EYE/WHITE.
COATS = {
    "cat": [
        ("LILAC", dict(body=(190, 172, 244), shade=(150, 132, 214), belly=(248, 242, 254),
                       accent=(128, 108, 200), inner=(255, 162, 198), cheek=(255, 146, 182),
                       nose=(255, 118, 158))),
        ("GINGER", dict(body=(250, 178, 98), shade=(222, 136, 68), belly=(255, 241, 218),
                        accent=(206, 108, 50), inner=(255, 172, 172), cheek=(255, 142, 142),
                        nose=(240, 112, 122))),
        ("MIDNIGHT", dict(body=(92, 96, 130), shade=(66, 68, 100), belly=(234, 234, 248),
                          accent=(72, 74, 108), inner=(232, 152, 192), cheek=(216, 122, 162),
                          nose=(242, 142, 182))),
    ],
    "dog": [
        ("GOLDEN", dict(body=(242, 198, 130), shade=(212, 158, 98), belly=(255, 245, 224),
                        accent=(170, 106, 66), inner=(216, 142, 112), cheek=(255, 152, 152),
                        nose=(58, 40, 46))),
        ("CHOCO", dict(body=(158, 106, 78), shade=(124, 80, 60), belly=(238, 208, 178),
                       accent=(98, 64, 50), inner=(192, 122, 112), cheek=(242, 132, 132),
                       nose=(44, 30, 36))),
        ("SNOWY", dict(body=(246, 244, 238), shade=(214, 208, 204), belly=(255, 253, 249),
                       accent=(72, 68, 82), inner=(232, 172, 172), cheek=(255, 162, 172),
                       nose=(40, 36, 48))),
    ],
    "bunny": [
        ("COTTON", dict(body=(250, 244, 248), shade=(220, 206, 222), belly=(255, 252, 253),
                        accent=(236, 220, 232), inner=(255, 172, 202), cheek=(255, 152, 186),
                        nose=(255, 122, 162))),
        ("COCOA", dict(body=(192, 148, 114), shade=(158, 114, 86), belly=(247, 228, 208),
                       accent=(172, 128, 96), inner=(250, 178, 188), cheek=(255, 152, 162),
                       nose=(240, 122, 142))),
        ("SKY", dict(body=(178, 212, 250), shade=(138, 174, 228), belly=(241, 248, 255),
                     accent=(152, 192, 242), inner=(255, 182, 212), cheek=(255, 162, 198),
                     nose=(255, 132, 172))),
    ],
    "fox": [
        ("RED", dict(body=(246, 136, 66), shade=(212, 100, 46), belly=(255, 247, 237),
                     accent=(72, 52, 62), inner=(255, 198, 162), cheek=(255, 152, 142),
                     nose=(46, 32, 40))),
        ("ARCTIC", dict(body=(234, 240, 250), shade=(196, 204, 228), belly=(255, 254, 251),
                        accent=(150, 160, 192), inner=(250, 202, 222), cheek=(255, 172, 192),
                        nose=(54, 46, 66))),
        ("SHADOW", dict(body=(122, 112, 152), shade=(92, 82, 122), belly=(228, 224, 242),
                        accent=(50, 44, 68), inner=(202, 162, 202), cheek=(232, 142, 182),
                        nose=(36, 30, 46))),
    ],
    "dino": [
        ("FERN", dict(body=(128, 204, 139), shade=(85, 160, 106), belly=(236, 243, 188),
                      accent=(63, 129, 104), inner=(255, 185, 137), cheek=(248, 159, 142), nose=(59, 100, 77))),
        ("LAGOON", dict(body=(111, 204, 209), shade=(65, 160, 174), belly=(222, 248, 215),
                        accent=(71, 113, 168), inner=(255, 204, 135), cheek=(249, 159, 163), nose=(48, 101, 123))),
        ("BERRY", dict(body=(204, 148, 206), shade=(165, 103, 176), belly=(255, 229, 199),
                       accent=(120, 80, 148), inner=(250, 180, 131), cheek=(255, 145, 164), nose=(106, 64, 126))),
    ],
    "tiger": [
        ("AMBER", dict(body=(251, 174, 75), shade=(222, 130, 49), belly=(255, 246, 216),
                       accent=(83, 52, 51), inner=(252, 192, 167), cheek=(255, 141, 140), nose=(129, 73, 81))),
        ("FROST", dict(body=(238, 244, 250), shade=(190, 208, 224), belly=(255, 253, 244),
                       accent=(91, 112, 138), inner=(244, 185, 208), cheek=(246, 159, 188), nose=(135, 89, 116))),
        ("ROSE", dict(body=(244, 174, 183), shade=(212, 130, 155), belly=(255, 241, 219),
                      accent=(123, 72, 107), inner=(253, 213, 186), cheek=(255, 143, 159), nose=(137, 77, 100))),
    ],
    "parrot": [
        ("TROPICAL", dict(body=(113, 207, 157), shade=(66, 165, 137), belly=(254, 225, 126),
                          accent=(70, 138, 216), inner=(251, 171, 79), cheek=(255, 166, 149), nose=(248, 190, 69))),
        ("SCARLET", dict(body=(241, 124, 114), shade=(202, 78, 99), belly=(255, 220, 112),
                         accent=(87, 147, 216), inner=(253, 169, 88), cheek=(255, 186, 167), nose=(244, 193, 83))),
        ("BLUEBELL", dict(body=(127, 182, 235), shade=(82, 133, 198), belly=(238, 241, 185),
                          accent=(130, 109, 194), inner=(253, 183, 103), cheek=(255, 174, 194), nose=(246, 199, 85))),
    ],
}

# name -> (fps, has_blink_variants)
PET_CLIPS = {
    "idle": (3.0, True), "walk_down": (8.0, False), "walk_up": (8.0, False),
    "walk_left": (8.0, False), "walk_right": (8.0, False), "sit": (2.5, True),
    "sleep": (1.4, False), "eat": (5.0, False), "happy": (8.0, False),
    "sad": (2.0, False), "play": (7.0, False), "dangle": (5.0, False),
    "stretch": (3.0, False), "dance": (7.0, False), "wave": (6.0, False),
}


# ================================================================= helpers
def _s():
    return pygame.Surface((FRAME, FRAME), pygame.SRCALPHA)


def _mirror(pts):
    return [(FRAME - 1 - x, y) for x, y in pts]


def _shrink(pts, k):
    cx = sum(p[0] for p in pts) / float(len(pts))
    cy = sum(p[1] for p in pts) / float(len(pts))
    return [(round(cx + (x - cx) * k), round(cy + (y - cy) * k)) for x, y in pts]


def _tip(pts, k=0.38):
    """Small triangle at the apex (pts[1]) of an ear - for dark ear tips."""
    a = pts[1]
    return [a, (round(a[0] + (pts[0][0] - a[0]) * k), round(a[1] + (pts[0][1] - a[1]) * k)),
            (round(a[0] + (pts[2][0] - a[0]) * k), round(a[1] + (pts[2][1] - a[1]) * k))]


def _ell(s, col, r):
    if r[2] > 0 and r[3] > 0:
        pygame.draw.ellipse(s, col, r)


def _blob(s, p, r, lip=False):
    """Shaded body-coloured ellipse. lip=True draws a dark line under it so a
    head sitting on a body still reads as two shapes."""
    x, y, w, h = r
    if lip:
        _ell(s, OUT, (x + 1, y + 1, w - 2, h))
    _ell(s, p["shade"], (x, y, w, h))
    _ell(s, p["body"], (x + 1, y, w - 2, h - 2))


def _chain(s, col, pts):
    """A soft 3-px thick curve through pts (tails)."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        _ell(s, col, ((x0 + x1) // 2 - 1, (y0 + y1) // 2 - 1, 3, 3))
    for x, y in pts:
        _ell(s, col, (x - 1, y - 1, 3, 3))


def _outline(s, col=OUT):
    w, h = s.get_size()
    solid = [[s.get_at((x, y))[3] > 0 for x in range(w)] for y in range(h)]
    for y in range(h):
        row = solid[y]
        for x in range(w):
            if row[x]:
                continue
            if ((x > 0 and row[x - 1]) or (x < w - 1 and row[x + 1]) or
                    (y > 0 and solid[y - 1][x]) or (y < h - 1 and solid[y + 1][x])):
                s.set_at((x, y), col)
    return s


def _eyes(s, y, kind, xs):
    for x in xs:
        if kind == "open":
            s.fill(EYE, (x, y, 2, 3))
            s.set_at((x, y), WHITE)
        elif kind == "wide":
            s.fill(EYE, (x, y - 1, 2, 4))
            s.set_at((x, y - 1), WHITE)
            s.set_at((x + 1, y + 1), WHITE)
        elif kind in ("blink", "closed"):
            s.fill(EYE, (x - 1, y + 2, 4, 1))
        elif kind == "happy":
            for px, py in ((x - 1, y + 2), (x, y + 1), (x + 1, y + 1), (x + 2, y + 2)):
                s.set_at((px, py), EYE)
        elif kind == "sad":
            s.fill(EYE, (x, y + 1, 2, 2))
            s.set_at((x, y + 1), WHITE)


def _mouth(s, y, kind, p, cx=11):
    if kind == "smile":
        for px, py in ((cx - 1, y), (cx + 2, y), (cx, y + 1), (cx + 1, y + 1)):
            s.set_at((px, py), EYE)
    elif kind == "open":
        s.fill(EYE, (cx - 1, y, 4, 2))
        s.fill(p["inner"], (cx, y + 1, 2, 1))
    elif kind == "frown":
        for px, py in ((cx - 1, y + 1), (cx + 2, y + 1), (cx, y), (cx + 1, y)):
            s.set_at((px, py), EYE)


# ================================================================= species rigs
class Rig:
    """Default rig = cat-shaped. Species override the bits that differ."""
    head_y = 3
    head_h = 13
    eye_dy = 5
    paw = "belly"

    # ---- front view pieces
    def ears(self, s, p, hy, droop, back):
        pass

    def ears_over(self, s, p, hy, droop, back):
        pass

    def tail(self, s, p, dy, t):
        pass

    def tail_sit(self, s, p, t):
        pass

    def tail_back(self, s, p, dy, t):
        pass

    def marks(self, s, p, hy):
        pass

    def marks_back(self, s, p, hy):
        pass

    def body_details(self, s, p, dy, tail, back):
        pass

    def hands(self, s, p, hy, left, right):
        """Small lifted paws are only drawn in gestures; ordinary poses stay intact."""
        for x, lift in ((2, left), (18, right)):
            if lift:
                y = hy + 12 - lift
                _ell(s, OUT, (x, y, 4, 5))
                _ell(s, p["body"], (x, y, 4, 4))
                _ell(s, p[self.paw], (x + 1, y, 2, 2))

    def face(self, s, p, hy, mouth):
        s.fill(p["nose"], (11, hy + 8, 2, 1))
        _mouth(s, hy + 9, mouth, p)

    def post_front(self, s, p, hy):
        pass

    # ---- side view pieces (facing right)
    def ears_side(self, s, p, hy, droop):
        pass

    def ears_side_over(self, s, p, hy, droop):
        pass

    def tail_side(self, s, p, dy, t):
        pass

    def snout_side(self, s, p, hy, mouth):
        s.set_at((22, hy + 6), p["nose"])
        if mouth == "open":
            s.fill(EYE, (20, hy + 8, 2, 2))
            s.set_at((21, hy + 9), p["inner"])
        else:
            s.set_at((21, hy + 8), EYE)

    side_eye_x = 17

    # ---- sleeping pieces
    def ears_sleep(self, s, p, hy):
        pass

    def ears_sleep_over(self, s, p, hy):
        pass

    def tail_sleep(self, s, p, t):
        pass


class Cat(Rig):
    def _ear(self, hy, droop):
        return [(2, hy + 5), (2, hy), (9, hy + 2)] if droop else [(4, hy + 5), (5, hy - 2), (10, hy + 1)]

    def ears(self, s, p, hy, droop, back):
        left = self._ear(hy, droop)
        for pts in (left, _mirror(left)):
            pygame.draw.polygon(s, p["body"], pts)
            if not back:
                pygame.draw.polygon(s, p["inner"], _shrink(pts, 0.45))

    def tail(self, s, p, dy, t):
        _chain(s, p["body"], [(16, 18 + dy), (18, 17 + dy), (19, 15 + dy), (20 + t, 13 + dy), (19 + t, 11 + dy)])
        _ell(s, p["accent"], (18 + t, 10 + dy, 3, 2))

    def tail_sit(self, s, p, t):
        _chain(s, p["body"], [(13, 20), (16, 20), (19, 19), (20, 17 + t)])
        _ell(s, p["accent"], (19, 15 + t, 3, 2))

    def tail_back(self, s, p, dy, t):
        _chain(s, p["body"], [(12, 19 + dy), (12, 17 + dy), (13 + t, 15 + dy), (13 + t, 12 + dy)])
        _ell(s, p["accent"], (12 + t, 11 + dy, 3, 2))

    def marks(self, s, p, hy):
        for x, h in ((9, 2), (11, 1), (12, 1), (14, 2)):
            s.fill(p["accent"], (x, hy + 1, 1, h))

    def marks_back(self, s, p, hy):
        for x in (8, 11, 12, 15):
            s.fill(p["accent"], (x, hy + 2, 1, 3))

    def post_front(self, s, p, hy):
        for x0, x1 in ((0, 1), (23, 22)):
            s.set_at((x0, hy + 8), OUT)
            s.set_at((x1, hy + 8), OUT)
            s.set_at((x0, hy + 10), OUT)
            s.set_at((x1, hy + 9), OUT)

    def ears_side(self, s, p, hy, droop):
        far = [(15, hy + 2), (20, hy), (20, hy + 4)] if droop else [(15, hy + 2), (18, hy - 2), (20, hy + 3)]
        pygame.draw.polygon(s, p["shade"], far)
        near = [(10, hy + 3), (10, hy - 1), (15, hy + 1)] if droop else [(10, hy + 3), (12, hy - 2), (16, hy + 1)]
        pygame.draw.polygon(s, p["body"], near)
        pygame.draw.polygon(s, p["inner"], _shrink(near, 0.45))

    def tail_side(self, s, p, dy, t):
        _chain(s, p["body"], [(4, 16 + dy), (2, 14 + dy), (1, 11 + dy), (2 + t, 8 + dy)])
        _ell(s, p["accent"], (1 + t, 6 + dy, 3, 2))

    def ears_sleep(self, s, p, hy):
        for pts in ([(2, hy + 3), (3, hy - 3), (7, hy + 1)], [(8, hy + 1), (11, hy - 3), (12, hy + 3)]):
            pygame.draw.polygon(s, p["body"], pts)
            pygame.draw.polygon(s, p["inner"], _shrink(pts, 0.45))

    def tail_sleep(self, s, p, t):
        _chain(s, p["body"], [(9, 20), (13, 21), (17, 21), (21, 20 - t)])
        _ell(s, p["accent"], (20, 18 - t, 3, 2))


class Dog(Rig):
    side_eye_x = 16

    def ears_over(self, s, p, hy, droop, back):
        o = 2 if droop else 0
        _ell(s, p["accent"], (1, hy + 2 + o, 6, 10))
        _ell(s, p["accent"], (17, hy + 2 + o, 6, 10))

    def tail(self, s, p, dy, t):
        _ell(s, p["body"], (16 + t, 9 + dy, 4, 8))
        _ell(s, p["belly"], (17 + t, 8 + dy, 2, 3))

    def tail_sit(self, s, p, t):
        _ell(s, p["body"], (17 + t, 14, 4, 7))

    def tail_back(self, s, p, dy, t):
        _ell(s, p["body"], (10 + t, 11 + dy, 4, 8))
        _ell(s, p["belly"], (11 + t, 10 + dy, 2, 3))

    def marks(self, s, p, hy):
        _ell(s, p["belly"], (7, hy + 7, 10, 6))
        _ell(s, p["accent"], (14, hy + 3, 5, 5))

    def face(self, s, p, hy, mouth):
        s.fill(p["nose"], (10, hy + 8, 4, 1))
        s.fill(p["nose"], (11, hy + 9, 2, 1))
        if mouth == "open":
            s.fill(EYE, (10, hy + 10, 4, 1))
            s.fill(p["inner"], (11, hy + 11, 2, 2))
        elif mouth == "frown":
            s.set_at((10, hy + 11), EYE)
            s.set_at((13, hy + 11), EYE)
            s.fill(EYE, (11, hy + 10, 2, 1))
        else:
            s.set_at((10, hy + 10), EYE)
            s.set_at((13, hy + 10), EYE)

    def ears_side_over(self, s, p, hy, droop):
        _ell(s, p["accent"], (10, hy + 1 + (2 if droop else 0), 5, 9))

    def snout_side(self, s, p, hy, mouth):
        _ell(s, p["belly"], (17, hy + 5, 7, 5))
        s.fill(p["nose"], (21, hy + 5, 2, 2))
        if mouth == "open":
            s.fill(EYE, (19, hy + 9, 3, 1))
            s.fill(p["inner"], (20, hy + 10, 2, 1))
        else:
            s.fill(EYE, (19, hy + 9, 2, 1))

    def tail_side(self, s, p, dy, t):
        _ell(s, p["body"], (1, 8 + dy + t, 4, 7))
        _ell(s, p["belly"], (1, 7 + dy + t, 2, 3))

    def ears_sleep_over(self, s, p, hy):
        _ell(s, p["accent"], (0, hy + 2, 4, 7))
        _ell(s, p["accent"], (10, hy + 2, 4, 7))

    def tail_sleep(self, s, p, t):
        _ell(s, p["body"], (19, 12 - t, 4, 6))


class Bunny(Rig):
    head_y = 6
    head_h = 12
    eye_dy = 4

    def ears(self, s, p, hy, droop, back):
        if droop:
            for r in ((1, hy + 1, 8, 4), (15, hy + 1, 8, 4)):
                _ell(s, p["body"], r)
                if not back:
                    _ell(s, p["inner"], (r[0] + 2, r[1] + 1, 4, 2))
            return
        for x in (5, 14):
            _ell(s, p["body"], (x, hy - 5, 5, 10))
            if not back:
                _ell(s, p["inner"], (x + 1, hy - 3, 3, 6))

    def tail(self, s, p, dy, t):
        _ell(s, p["belly"], (16, 15 + dy, 6, 5))

    def tail_sit(self, s, p, t):
        _ell(s, p["belly"], (17, 17, 5, 5))

    def tail_back(self, s, p, dy, t):
        _ell(s, p["belly"], (9, 15 + dy, 6, 5))

    def face(self, s, p, hy, mouth):
        s.fill(p["nose"], (11, hy + 7, 2, 1))
        if mouth == "open":
            s.fill(EYE, (10, hy + 8, 4, 2))
            s.fill(WHITE, (11, hy + 8, 2, 1))
        elif mouth == "frown":
            _mouth(s, hy + 8, "frown", p)
        else:
            for px, py in ((10, hy + 8), (11, hy + 9), (12, hy + 9), (13, hy + 8)):
                s.set_at((px, py), EYE)
            s.fill(WHITE, (11, hy + 10, 2, 1))

    def ears_side(self, s, p, hy, droop):
        if droop:
            _ell(s, p["shade"], (4, hy, 9, 4))
            _ell(s, p["body"], (3, hy + 2, 9, 4))
            return
        _ell(s, p["shade"], (13, hy - 5, 4, 9))
        _ell(s, p["body"], (10, hy - 6, 4, 10))
        _ell(s, p["inner"], (11, hy - 4, 2, 6))

    def snout_side(self, s, p, hy, mouth):
        s.set_at((21, hy + 5), p["nose"])
        s.set_at((20, hy + 7), EYE)
        if mouth == "open":
            s.set_at((20, hy + 8), WHITE)

    def tail_side(self, s, p, dy, t):
        _ell(s, p["belly"], (1, 13 + dy, 5, 5))

    def ears_sleep(self, s, p, hy):
        _ell(s, p["shade"], (8, hy + 2, 10, 4))
        _ell(s, p["body"], (7, hy, 10, 4))
        _ell(s, p["inner"], (9, hy + 1, 6, 2))

    def tail_sleep(self, s, p, t):
        _ell(s, p["belly"], (19, 13 + t, 5, 5))


class Fox(Rig):
    paw = "accent"

    def _ear(self, hy, droop):
        return [(1, hy + 5), (1, hy), (9, hy + 2)] if droop else [(3, hy + 6), (4, hy - 2), (11, hy + 1)]

    def ears(self, s, p, hy, droop, back):
        left = self._ear(hy, droop)
        for pts in (left, _mirror(left)):
            pygame.draw.polygon(s, p["body"], pts)
            if not back:
                pygame.draw.polygon(s, p["inner"], _shrink(pts, 0.45))
            pygame.draw.polygon(s, p["accent"], _tip(pts))

    def tail(self, s, p, dy, t):
        _ell(s, p["shade"], (14 + t, 8 + dy, 9, 13))
        _ell(s, p["body"], (14 + t, 8 + dy, 8, 12))
        _ell(s, p["belly"], (15 + t, 7 + dy, 7, 5))

    def tail_sit(self, s, p, t):
        _ell(s, p["body"], (9, 17, 14, 5))
        _ell(s, p["belly"], (8 + t, 17, 6, 5))

    def tail_back(self, s, p, dy, t):
        _ell(s, p["shade"], (7 + t, 7 + dy, 10, 14))
        _ell(s, p["body"], (7 + t, 7 + dy, 9, 13))
        _ell(s, p["belly"], (8 + t, 6 + dy, 8, 5))

    def marks(self, s, p, hy):
        pygame.draw.polygon(s, p["belly"], [
            (3, hy + 8), (7, hy + 6), (11, hy + 8), (12, hy + 8), (16, hy + 6), (20, hy + 8),
            (16, hy + 12), (12, hy + 13), (11, hy + 13), (7, hy + 12)])

    def ears_side(self, s, p, hy, droop):
        far = [(15, hy + 2), (18, hy - 3), (21, hy + 3)]
        near = [(10, hy + 3), (12, hy - 3), (16, hy + 1)]
        if droop:
            far = [(15, hy + 2), (21, hy), (20, hy + 4)]
            near = [(10, hy + 3), (9, hy - 1), (15, hy + 1)]
        pygame.draw.polygon(s, p["shade"], far)
        pygame.draw.polygon(s, p["accent"], _tip(far))
        pygame.draw.polygon(s, p["body"], near)
        pygame.draw.polygon(s, p["inner"], _shrink(near, 0.45))
        pygame.draw.polygon(s, p["accent"], _tip(near))

    def snout_side(self, s, p, hy, mouth):
        _ell(s, p["belly"], (14, hy + 6, 7, 5))
        pygame.draw.polygon(s, p["body"], [(18, hy + 4), (23, hy + 7), (18, hy + 9)])
        pygame.draw.polygon(s, p["belly"], [(17, hy + 8), (23, hy + 8), (18, hy + 11)])
        s.fill(p["nose"], (22, hy + 6, 2, 2))
        if mouth == "open":
            s.fill(EYE, (19, hy + 9, 3, 1))

    def tail_side(self, s, p, dy, t):
        _ell(s, p["shade"], (0, 6 + dy + t, 9, 10))
        _ell(s, p["body"], (0, 6 + dy + t, 8, 9))
        _ell(s, p["belly"], (0, 5 + dy + t, 4, 5))

    def ears_sleep(self, s, p, hy):
        for pts in ([(1, hy + 4), (2, hy - 3), (7, hy + 1)], [(8, hy + 1), (12, hy - 3), (13, hy + 4)]):
            pygame.draw.polygon(s, p["body"], pts)
            pygame.draw.polygon(s, p["inner"], _shrink(pts, 0.45))
            pygame.draw.polygon(s, p["accent"], _tip(pts))

    def tail_sleep(self, s, p, t):
        _ell(s, p["shade"], (6, 15, 17, 7))
        _ell(s, p["body"], (6, 15, 16, 6))
        _ell(s, p["belly"], (4 + t, 16, 6, 5))


class Dino(Rig):
    """Round baby dinosaur with a broad muzzle, scalloped crest and heavy tail."""
    head_y = 4
    paw = "shade"

    def ears(self, s, p, hy, droop, back):
        for x, height in ((7, 2), (11, 3), (15, 2)):
            pygame.draw.polygon(s, p["accent"], [(x - 2, hy + 2), (x, hy - height), (x + 2, hy + 2)])

    def marks(self, s, p, hy):
        _ell(s, p["belly"], (5, hy + 6, 14, 6))
        for x in (6, 16):
            s.fill(p["shade"], (x, hy + 3, 2, 1))

    def face(self, s, p, hy, mouth):
        for x in (9, 14):
            s.set_at((x, hy + 8), p["nose"])
        _mouth(s, hy + 9, mouth, p)
        if mouth == "open":
            s.set_at((10, hy + 9), WHITE)
            s.set_at((13, hy + 9), WHITE)

    def marks_back(self, s, p, hy):
        for y in range(hy + 2, hy + 11, 3):
            _ell(s, p["accent"], (10, y, 4, 3))

    def tail(self, s, p, dy, t):
        pygame.draw.polygon(s, p["shade"], [(14, 17 + dy), (21, 17 + dy), (22, 12 + dy + t), (23, 18 + dy), (19, 21 + dy), (14, 21 + dy)])
        pygame.draw.polygon(s, p["body"], [(15, 17 + dy), (20, 18 + dy), (22, 14 + dy + t), (21, 19 + dy), (16, 20 + dy)])

    def tail_sit(self, s, p, t):
        self.tail(s, p, 0, t)

    def tail_back(self, s, p, dy, t):
        pygame.draw.polygon(s, p["body"], [(9, 15 + dy), (14, 15 + dy), (16 + t, 21), (12, 22), (9, 20)])
        s.fill(p["accent"], (11, 16 + dy, 2, 4))

    def ears_side(self, s, p, hy, droop):
        for x, y in ((10, hy), (13, hy - 1), (16, hy - 1)):
            pygame.draw.polygon(s, p["accent"], [(x - 1, y + 3), (x, y - 2), (x + 2, y + 2)])

    def snout_side(self, s, p, hy, mouth):
        _ell(s, p["belly"], (16, hy + 6, 8, 5))
        s.set_at((21, hy + 6), p["nose"])
        s.fill(EYE, (20, hy + 9, 3, 1))
        if mouth == "open":
            s.set_at((21, hy + 10), WHITE)

    def tail_side(self, s, p, dy, t):
        pygame.draw.polygon(s, p["shade"], [(8, 14 + dy), (3, 15 + dy), (1, 10 + dy + t), (0, 17 + dy), (4, 21 + dy), (10, 20 + dy)])
        pygame.draw.polygon(s, p["body"], [(8, 15 + dy), (4, 17 + dy), (1, 12 + dy + t), (2, 18 + dy), (7, 20 + dy)])

    def ears_sleep(self, s, p, hy):
        for x in (3, 7, 11):
            pygame.draw.polygon(s, p["accent"], [(x - 1, hy + 2), (x, hy - 2), (x + 2, hy + 2)])

    def tail_sleep(self, s, p, t):
        pygame.draw.polygon(s, p["body"], [(10, 19), (18, 19), (22, 15 - t), (22, 21), (13, 22)])


class Tiger(Cat):
    """Rounded ears and broad stripes distinguish a tiger from the pointy cat."""
    def ears(self, s, p, hy, droop, back):
        for x in (2, 16):
            _ell(s, p["accent"], (x, hy - 1, 6, 6))
            _ell(s, p["body"], (x + 1, hy, 4, 4))
            if not back:
                _ell(s, p["inner"], (x + 2, hy + 1, 2, 2))

    def marks(self, s, p, hy):
        _ell(s, p["belly"], (6, hy + 7, 12, 6))
        for x, width, height in ((8, 2, 3), (11, 2, 2), (14, 2, 3)):
            s.fill(p["accent"], (x, hy + 1, width, height))
        for y in (hy + 5, hy + 8):
            s.fill(p["accent"], (3, y, 3, 1))
            s.fill(p["accent"], (18, y, 3, 1))

    def marks_back(self, s, p, hy):
        for x in (5, 10, 16):
            s.fill(p["accent"], (x, hy + 2, 2, 4))
        for x in (4, 17):
            s.fill(p["accent"], (x, hy + 8, 3, 2))

    def body_details(self, s, p, dy, tail, back):
        for x in (6, 16):
            s.fill(p["accent"], (x, 17 + dy, 2, 1))

    def tail(self, s, p, dy, t):
        super().tail(s, p, dy, t)
        for x, y in ((19 + t, 13 + dy), (18, 16 + dy)):
            s.fill(p["accent"], (x, y, 2, 1))

    def ears_side(self, s, p, hy, droop):
        for x, y in ((17, hy - 1), (10, hy)):
            _ell(s, p["accent"], (x, y, 5, 5))
            _ell(s, p["inner"], (x + 1, y + 1, 3, 3))

    def ears_side_over(self, s, p, hy, droop):
        for x in (10, 13):
            s.fill(p["accent"], (x, hy + 3, 2, 3))

    def snout_side(self, s, p, hy, mouth):
        _ell(s, p["belly"], (17, hy + 6, 6, 5))
        super().snout_side(s, p, hy, mouth)

    def ears_sleep(self, s, p, hy):
        for x in (1, 9):
            _ell(s, p["accent"], (x, hy - 2, 5, 5))
            _ell(s, p["inner"], (x + 1, hy - 1, 3, 3))

    def ears_sleep_over(self, s, p, hy):
        for x in (4, 8):
            s.fill(p["accent"], (x, hy + 1, 1, 3))


class Parrot(Rig):
    """Feathered crest, curved beak, folded wings and a three-feather tail."""
    head_y = 4
    paw = "nose"

    def ears(self, s, p, hy, droop, back):
        for x, y in ((9, hy - 2), (12, hy - 3), (15, hy - 1)):
            _ell(s, p["accent"], (x - 1, y, 3, 5))

    def marks(self, s, p, hy):
        for x in (5, 13):
            _ell(s, p["belly"], (x, hy + 4, 6, 7))

    def marks_back(self, s, p, hy):
        for x in (7, 11, 15):
            s.fill(p["shade"], (x, hy + 6, 1, 4))

    def face(self, s, p, hy, mouth):
        pygame.draw.polygon(s, p["nose"], [(10, hy + 7), (13, hy + 7), (14, hy + 9), (11, hy + 11), (10, hy + 9)])
        s.fill(p["inner"], (10, hy + 9, 3, 1))
        if mouth == "open":
            s.fill(EYE, (11, hy + 10, 2, 1))

    def body_details(self, s, p, dy, tail, back):
        for x in (4, 15):
            _ell(s, p["accent"], (x, 13 + dy, 5, 7))
            s.fill(p["shade"], (x + 1, 17 + dy, 1, 2))

    def hands(self, s, p, hy, left, right):
        for x, lift in ((0, left), (19, right)):
            if lift:
                y = hy + 12 - lift
                _ell(s, p["accent"], (x, y, 5, 6))
                for px in range(x + 1, x + 4, 2):
                    s.fill(p["body"], (px, y + 1, 1, 3))

    def tail(self, s, p, dy, t):
        for x, y in ((16, 14), (19, 13), (21, 12)):
            pygame.draw.line(s, p["accent"], (15, 17 + dy), (x, y + dy + t), 2)

    def tail_sit(self, s, p, t):
        self.tail(s, p, 0, t)

    def tail_back(self, s, p, dy, t):
        for x in (9, 12, 15):
            pygame.draw.line(s, p["accent"], (12, 16 + dy), (x + t, 22), 2)

    def ears_side(self, s, p, hy, droop):
        for x, y in ((12, hy - 2), (15, hy - 3), (18, hy - 2)):
            _ell(s, p["accent"], (x, y, 3, 5))

    def ears_side_over(self, s, p, hy, droop):
        _ell(s, p["belly"], (15, hy + 3, 7, 7))
        _ell(s, p["accent"], (5, 14, 8, 6))

    def snout_side(self, s, p, hy, mouth):
        pygame.draw.polygon(s, p["nose"], [(20, hy + 5), (23, hy + 6), (23, hy + 9), (21, hy + 10), (22, hy + 7)])
        if mouth == "open":
            s.set_at((22, hy + 9), EYE)

    def tail_side(self, s, p, dy, t):
        for y in (16, 18, 20):
            pygame.draw.line(s, p["accent"], (8, 16 + dy), (0, y + dy + t), 2)

    def ears_sleep(self, s, p, hy):
        for x in (4, 7, 10):
            _ell(s, p["accent"], (x, hy - 2, 3, 4))

    def tail_sleep(self, s, p, t):
        _ell(s, p["accent"], (13, 15, 9, 5))
        for x in (16, 19):
            s.fill(p["body"], (x, 16, 1, 3))


RIGS = {"cat": Cat(), "dog": Dog(), "bunny": Bunny(), "fox": Fox(),
        "dino": Dino(), "tiger": Tiger(), "parrot": Parrot()}


# ================================================================= views
def _front(rig, p, dy=0, squash=0, lf=0, rf=0, tail=0, eyes="open", mouth="smile",
           sit=False, droop=False, back=False, tear=False, arm_l=0, arm_r=0, **_):
    s = _s()
    hy = rig.head_y + dy + squash
    if not back and not sit:
        rig.tail(s, p, dy, tail)
    rig.ears(s, p, hy, droop, back)
    if sit:
        _blob(s, p, (5, 13 + dy, 14, 9 - dy))
    else:
        _blob(s, p, (6, 13 + dy, 12, 9 - dy))
    pk = p[rig.paw]
    for x, lift in ((7, lf), (13, rf)):
        _ell(s, OUT, (x, 20 - lift, 4, 3))
        _ell(s, pk, (x, 19 - lift, 4, 3))
    if not back:
        _ell(s, p["belly"], (8, 15 + dy, 8, 5))
    rig.body_details(s, p, dy, tail, back)
    if sit:
        rig.tail_sit(s, p, tail)
    _blob(s, p, (3, hy, 18, rig.head_h - squash), lip=True)
    rig.ears_over(s, p, hy, droop, back)
    if back:
        rig.marks_back(s, p, hy)
        rig.tail_back(s, p, dy, tail)
        _outline(s)
        return s
    rig.marks(s, p, hy)
    ey = hy + rig.eye_dy
    _eyes(s, ey, eyes, (7, 15))
    s.fill(p["cheek"], (5, ey + 3, 2, 1))
    s.fill(p["cheek"], (17, ey + 3, 2, 1))
    rig.face(s, p, hy, mouth)
    rig.hands(s, p, hy, arm_l, arm_r)
    _outline(s)
    rig.post_front(s, p, hy)
    if tear:
        s.fill(TEAR, (7, ey + 3, 1, 2))
    return s


def _side(rig, p, dy=0, fl=0, bl=0, tail=0, eyes="open", mouth="smile", dip=0, squash=0, **_):
    s = _s()
    hy = rig.head_y + dy + dip + squash
    rig.tail_side(s, p, dy, tail)
    for x, lift, key in ((7, bl, "shade"), (14, fl, "shade")):
        top, bot = 17 + dy, 21 - lift
        s.fill(p[key], (x, top, 3, max(1, bot - top + 1)))
    _blob(s, p, (3, 12 + dy, 14, 9 - dy))
    for x, lift in ((4, bl), (11, fl)):
        top, bot = 17 + dy, 21 - lift
        s.fill(p["body"], (x, top, 3, max(1, bot - top + 1)))
        s.fill(p[rig.paw], (x, bot, 3, 1))
    _ell(s, p["belly"], (6, 16 + dy, 8, 4))
    rig.ears_side(s, p, hy, False)
    _blob(s, p, (9, hy, 14, rig.head_h - 1 - squash), lip=True)
    rig.ears_side_over(s, p, hy, False)
    ex, ey = rig.side_eye_x, hy + rig.eye_dy - 1
    if eyes in ("open", "wide"):
        s.fill(EYE, (ex, ey, 2, 3))
        s.set_at((ex, ey), WHITE)
    elif eyes in ("blink", "closed"):
        s.fill(EYE, (ex - 1, ey + 2, 3, 1))
    elif eyes == "happy":
        for px, py in ((ex - 1, ey + 2), (ex, ey + 1), (ex + 1, ey + 1), (ex + 2, ey + 2)):
            s.set_at((px, py), EYE)
    s.fill(p["cheek"], (ex - 2, ey + 3, 2, 1))
    rig.snout_side(s, p, hy, mouth)
    _outline(s)
    return s


def _sleep(rig, p, br=0, tail=0, **_):
    s = _s()
    _blob(s, p, (5, 11 + br, 18, 11 - br))
    hy = 8 + br
    rig.ears_sleep(s, p, hy)
    _blob(s, p, (1, hy, 13, 12), lip=True)
    rig.ears_sleep_over(s, p, hy)
    s.fill(EYE, (3, hy + 6, 3, 1))
    s.fill(EYE, (8, hy + 6, 3, 1))
    s.fill(p["cheek"], (2, hy + 8, 2, 1))
    s.fill(p["cheek"], (10, hy + 8, 2, 1))
    s.fill(p["nose"], (6, hy + 8, 2, 1))
    rig.tail_sleep(s, p, tail)
    _outline(s)
    return s


VIEWS = {"front": _front, "side": _side, "sleep": _sleep}


# ================================================================= poses
def poses(clip):
    """Pose list for a clip. Each pose is a plain dict understood by the views."""
    if clip == "idle":
        base = [dict(view="front", squash=q, tail=t) for q, t in zip((0, 0, 1, 1), (0, 1, 0, -1))]
        return base + [dict(d, eyes="blink") for d in base]
    if clip == "stretch":
        return [dict(view="side", dip=d, squash=q, fl=-1, eyes="closed", tail=t)
                for d, q, t in ((0, 0, 0), (1, 1, -1), (3, 2, -2), (3, 2, -1), (1, 1, 0), (0, 0, 1))]
    if clip in ("walk_down", "walk_up"):
        return [dict(view="front", dy=dy, lf=lf, rf=rf, tail=dy, back=(clip == "walk_up"))
                for lf, rf, dy in ((0, 0, 0), (2, 0, -1), (0, 0, 0), (0, 2, -1))]
    if clip in ("walk_left", "walk_right"):
        return [dict(view="side", dy=dy, fl=lf, bl=rf, tail=-dy, flip=(clip == "walk_left"))
                for lf, rf, dy in ((0, 0, 0), (2, 0, -1), (0, 0, 0), (0, 2, -1))]
    if clip == "sit":
        base = [dict(view="front", sit=True, tail=t) for t in (0, 1)]
        return base + [dict(d, eyes="blink") for d in base]
    if clip == "sleep":
        return [dict(view="sleep", br=b, tail=t) for b, t in ((0, 0), (1, 1), (1, 0), (0, 1))]
    if clip == "eat":
        return [dict(view="side", dip=d, mouth=m, eyes=e)
                for d, m, e in ((1, "smile", "open"), (3, "open", "blink"), (3, "smile", "open"),
                                (2, "open", "blink"))]
    if clip == "happy":
        return [dict(view="front", squash=1 if i == 0 else 0, eyes="happy", mouth="open",
                     tail=(-1, 1, -1, 1)[i], shift=(0, -j)) for i, j in enumerate((0, 2, 3, 1))]
    if clip == "dance":
        return [dict(view="front", squash=q, eyes="happy", mouth="open", tail=tail,
                     arm_l=al, arm_r=ar, lf=lf, rf=rf, shift=(0, -jump))
                for q, tail, al, ar, lf, rf, jump in (
                    (1, -1, 2, 5, 0, 1, 0), (0, -1, 3, 6, 0, 2, 1),
                    (0, 0, 5, 5, 0, 0, 2), (1, 1, 5, 2, 1, 0, 0),
                    (0, 1, 6, 3, 2, 0, 1), (0, 0, 5, 5, 0, 0, 2),
                    (1, -1, 3, 3, 1, 0, 0), (0, 1, 5, 5, 0, 1, 1))]
    if clip == "wave":
        return [dict(view="front", eyes=eyes, arm_r=lift, tail=tail, mouth="smile")
                for lift, tail, eyes in ((3, -1, "open"), (6, 0, "happy"),
                                         (4, 1, "happy"), (6, 0, "open"))]
    if clip == "sad":
        return [dict(view="front", squash=1, eyes="sad", mouth="frown", droop=True, tear=(i == 1))
                for i in range(2)]
    if clip == "play":
        return [dict(view="front", squash=q, eyes="wide", mouth="open", tail=(-1, 1, -1, 1)[i],
                     shift=(lean, -jump))
                for i, (q, lean, jump) in enumerate(((2, -1, 0), (0, 1, 2), (0, 2, 3), (1, -1, 0)))]
    if clip == "dangle":
        return [dict(view="front", eyes="wide", mouth="open", lf=-1, rf=-1, tail=t, shift=(sx, 0))
                for sx, t in ((0, 0), (1, 1), (0, 0), (-1, -1))]
    raise KeyError(clip)


def render(species, pose, coat=0):
    rig = RIGS[species]
    pal = COATS[species][coat][1]
    img = VIEWS[pose["view"]](rig, pal, **pose)
    sx, sy = pose.get("shift", (0, 0))
    if sx or sy:
        out = _s()
        out.blit(img, (sx, sy))
        img = out
    if pose.get("flip"):
        img = pygame.transform.flip(img, True, False)
    return img


def anchor(species, pose):
    """Top-centre of the head inside the frame (where hats sit)."""
    rig = RIGS[species]
    v = pose["view"]
    sx, sy = pose.get("shift", (0, 0))
    if v == "front":
        x, y = 12, rig.head_y + pose.get("dy", 0) + pose.get("squash", 0)
    elif v == "side":
        x, y = 16, rig.head_y + pose.get("dy", 0) + pose.get("dip", 0) + pose.get("squash", 0)
    else:
        x, y = 7, 8 + pose.get("br", 0)
    x, y = x + sx, y + sy
    if pose.get("flip"):
        x = FRAME - 1 - x
    return (x, y)


def make_clip(species, clip):
    return [render(species, p) for p in poses(clip)]


def clip_anchors(species, clip):
    return [anchor(species, p) for p in poses(clip)]


def recolor(frames, species, coat):
    """Palette-swap coat 0 frames into another coat."""
    if coat == 0:
        return frames
    src = COATS[species][0][1]
    dst = COATS[species][coat][1]
    cmap = {tuple(src[k]): tuple(dst[k]) for k in src}
    out = []
    for f in frames:
        g = f.copy()
        w, h = g.get_size()
        for y in range(h):
            for x in range(w):
                c = g.get_at((x, y))
                if c[3] == 0:
                    continue
                n = cmap.get((c[0], c[1], c[2]))
                if n:
                    g.set_at((x, y), (n[0], n[1], n[2], c[3]))
        out.append(g)
    return out
