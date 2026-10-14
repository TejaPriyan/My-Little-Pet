"""A tiny PIL-backed stand-in for the subset of pygame that TEJA PET uses.

It exists ONLY so the game can be exercised headlessly where real pygame is
not installable (no display / no network). Call install() before importing the
game. Real pygame is always preferred when it is available.
"""
import sys
import types

from PIL import Image, ImageDraw

SRCALPHA = 0x10000
RESIZABLE = 0x10
FULLSCREEN = 0x80
QUIT, KEYDOWN, KEYUP = 256, 768, 769
MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP = 1024, 1025, 1026
VIDEORESIZE = 32769


class error(Exception):
    pass


# ------------------------------------------------------------------ Rect
class Rect:
    def __init__(self, *a):
        if len(a) == 1:
            a = tuple(a[0])
        if len(a) == 2:
            (x, y), (w, h) = a
        else:
            x, y, w, h = a
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    width = property(lambda s: s.w, lambda s, v: setattr(s, "w", int(v)))
    height = property(lambda s: s.h, lambda s, v: setattr(s, "h", int(v)))
    left = property(lambda s: s.x, lambda s, v: setattr(s, "x", int(v)))
    top = property(lambda s: s.y, lambda s, v: setattr(s, "y", int(v)))
    right = property(lambda s: s.x + s.w, lambda s, v: setattr(s, "x", int(v) - s.w))
    bottom = property(lambda s: s.y + s.h, lambda s, v: setattr(s, "y", int(v) - s.h))
    centerx = property(lambda s: s.x + s.w // 2, lambda s, v: setattr(s, "x", int(v) - s.w // 2))
    centery = property(lambda s: s.y + s.h // 2, lambda s, v: setattr(s, "y", int(v) - s.h // 2))
    size = property(lambda s: (s.w, s.h))

    def _set(self, ax, ay, p):
        px, py = int(p[0]), int(p[1])
        if ax == "l": self.x = px
        elif ax == "c": self.x = px - self.w // 2
        elif ax == "r": self.x = px - self.w
        if ay == "t": self.y = py
        elif ay == "m": self.y = py - self.h // 2
        elif ay == "b": self.y = py - self.h

    def _get(self, ax, ay):
        x = {"l": self.x, "c": self.x + self.w // 2, "r": self.x + self.w}[ax]
        y = {"t": self.y, "m": self.y + self.h // 2, "b": self.y + self.h}[ay]
        return (x, y)


for _n, (_ax, _ay) in {"topleft": ("l", "t"), "midtop": ("c", "t"), "topright": ("r", "t"),
                       "midleft": ("l", "m"), "center": ("c", "m"), "midright": ("r", "m"),
                       "bottomleft": ("l", "b"), "midbottom": ("c", "b"),
                       "bottomright": ("r", "b")}.items():
    setattr(Rect, _n, property(lambda s, a=_ax, b=_ay: s._get(a, b),
                               lambda s, v, a=_ax, b=_ay: s._set(a, b, v)))


def _rect_methods():
    def colliderect(s, o):
        o = Rect(o)
        return s.x < o.x + o.w and o.x < s.x + s.w and s.y < o.y + o.h and o.y < s.y + s.h

    def collidepoint(s, *p):
        if len(p) == 1:
            p = p[0]
        return s.x <= p[0] < s.x + s.w and s.y <= p[1] < s.y + s.h

    Rect.colliderect = colliderect
    Rect.collidepoint = collidepoint
    Rect.inflate = lambda s, dx, dy: Rect(s.x - dx // 2, s.y - dy // 2, s.w + dx, s.h + dy)
    Rect.move = lambda s, dx, dy: Rect(s.x + dx, s.y + dy, s.w, s.h)
    Rect.copy = lambda s: Rect(s.x, s.y, s.w, s.h)
    Rect.__iter__ = lambda s: iter((s.x, s.y, s.w, s.h))
    Rect.__getitem__ = lambda s, i: (s.x, s.y, s.w, s.h)[i]
    Rect.__repr__ = lambda s: "Rect(%d,%d,%d,%d)" % (s.x, s.y, s.w, s.h)
    Rect.__eq__ = lambda s, o: tuple(s) == tuple(o)
    Rect.__hash__ = lambda s: hash(tuple(s))


_rect_methods()


# ------------------------------------------------------------------ Surface
def _col(c, alpha=True):
    c = tuple(int(v) for v in c)
    if len(c) == 3:
        c += (255,)
    return c if alpha else c[:3] + (255,)


class Surface:
    def __init__(self, size, flags=0):
        size = (max(1, int(size[0])), max(1, int(size[1])))
        self.hasalpha = bool(flags & SRCALPHA)
        self.im = Image.new("RGBA", size, (0, 0, 0, 0) if self.hasalpha else (0, 0, 0, 255))
        self.alpha = None

    @classmethod
    def _wrap(cls, im, hasalpha=True):
        s = cls(im.size, SRCALPHA if hasalpha else 0)
        s.im = im.convert("RGBA")
        return s

    def get_size(self): return self.im.size
    def get_width(self): return self.im.size[0]
    def get_height(self): return self.im.size[1]

    def get_rect(self, **kw):
        r = Rect(0, 0, *self.im.size)
        for k, v in kw.items():
            setattr(r, k, v)
        return r

    def copy(self):
        s = Surface._wrap(self.im.copy(), self.hasalpha)
        s.alpha = self.alpha
        return s

    def convert(self): return self
    def convert_alpha(self): return self
    def set_alpha(self, v): self.alpha = v
    def set_colorkey(self, *_): pass

    def subsurface(self, rect):
        r = Rect(rect)
        return Surface._wrap(self.im.crop((r.x, r.y, r.x + r.w, r.y + r.h)), self.hasalpha)

    def fill(self, color, rect=None):
        c = _col(color, self.hasalpha)
        w, h = self.im.size
        if rect is None:
            box = (0, 0, w, h)
        else:
            r = Rect(rect)
            box = (max(0, r.x), max(0, r.y), min(w, r.x + r.w), min(h, r.y + r.h))
        if box[2] > box[0] and box[3] > box[1]:
            self.im.paste(c, box)

    def set_at(self, pos, color):
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self.im.size[0] and 0 <= y < self.im.size[1]:
            self.im.putpixel((x, y), _col(color, self.hasalpha))

    def get_at(self, pos):
        return self.im.getpixel((int(pos[0]), int(pos[1])))

    def blit(self, src, dest, area=None):
        if isinstance(dest, Rect):
            dest = (dest.x, dest.y)
        dx, dy = int(dest[0]), int(dest[1])
        simg = src.im
        if area is not None:
            a = Rect(area)
            simg = simg.crop((a.x, a.y, a.x + a.w, a.y + a.h))
        if src.alpha is not None and src.alpha < 255:
            simg = simg.copy()
            simg.putalpha(simg.getchannel("A").point(lambda v: v * src.alpha // 255))
        W, H = self.im.size
        sx0, sy0 = max(0, -dx), max(0, -dy)
        sx1, sy1 = min(simg.size[0], W - dx), min(simg.size[1], H - dy)
        if sx1 <= sx0 or sy1 <= sy0:
            return
        piece = simg.crop((sx0, sy0, sx1, sy1))
        self.im.alpha_composite(piece, (dx + sx0, dy + sy0))
        if not self.hasalpha:
            self.im.putalpha(255)


# ------------------------------------------------------------------ draw
def _d(surf): return ImageDraw.Draw(surf.im)

def _box(r):
    r = Rect(r)
    return (r.x, r.y, r.x + r.w - 1, r.y + r.h - 1), r.w > 0 and r.h > 0

class _Draw:
    @staticmethod
    def rect(surf, color, rect, width=0, border_radius=0):
        box, ok = _box(rect)
        if not ok: return
        c = _col(color, surf.hasalpha)
        d = _d(surf)
        if border_radius:
            d.rounded_rectangle(box, radius=border_radius, fill=c if width == 0 else None,
                                outline=c if width else None, width=width or 1)
        else:
            d.rectangle(box, fill=c if width == 0 else None, outline=c if width else None,
                        width=width or 1)

    @staticmethod
    def ellipse(surf, color, rect, width=0):
        box, ok = _box(rect)
        if not ok: return
        c = _col(color, surf.hasalpha)
        _d(surf).ellipse(box, fill=c if width == 0 else None, outline=c if width else None,
                         width=width or 1)

    @staticmethod
    def circle(surf, color, center, radius, width=0):
        cx, cy = center
        c = _col(color, surf.hasalpha)
        _d(surf).ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                         fill=c if width == 0 else None, outline=c if width else None,
                         width=width or 1)

    @staticmethod
    def polygon(surf, color, pts, width=0):
        c = _col(color, surf.hasalpha)
        pts = [(int(x), int(y)) for x, y in pts]
        d = _d(surf)
        if width == 0:
            d.polygon(pts, fill=c)
        else:
            d.line(pts + [pts[0]], fill=c, width=width)

    @staticmethod
    def line(surf, color, a, b, width=1):
        _d(surf).line([tuple(a), tuple(b)], fill=_col(color, surf.hasalpha), width=width)


# ------------------------------------------------------------------ module build
class _Harness:
    """Global knobs the headless tests drive."""
    events = []
    pressed = set()
    mouse = (0, 0)
    mods = 0
    frame_ms = 16
    screen = None
    screen_size = (960, 540)
    sounds_played = []


class _Event:
    def __init__(self, type, **kw):
        self.type = type
        self.__dict__.update(kw)


class _Pressed:
    def __getitem__(self, k): return k in _Harness.pressed


class _Clock:
    def tick(self, fps=0): return _Harness.frame_ms


class _Sound:
    def __init__(self, file=None, buffer=None):
        self.name = file
    def play(self, loops=0):
        _Harness.sounds_played.append(self.name)
    def set_volume(self, v): pass
    def stop(self): pass


def install():
    m = types.ModuleType("pygame")
    m.SRCALPHA, m.RESIZABLE, m.FULLSCREEN = SRCALPHA, RESIZABLE, FULLSCREEN
    m.QUIT, m.KEYDOWN, m.KEYUP = QUIT, KEYDOWN, KEYUP
    m.MOUSEMOTION, m.MOUSEBUTTONDOWN, m.MOUSEBUTTONUP = MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
    m.VIDEORESIZE = VIDEORESIZE
    m.KMOD_SHIFT = 3
    keys = {"UP": 1073741906, "DOWN": 1073741905, "LEFT": 1073741904, "RIGHT": 1073741903,
            "RETURN": 13, "ESCAPE": 27, "BACKSPACE": 8, "SPACE": 32, "TAB": 9,
            "F11": 1073741892, "KP_ENTER": 1073741912, "LSHIFT": 1073742049,
            "RSHIFT": 1073742053}
    for n, v in keys.items():
        setattr(m, "K_" + n, v)
    for ch in "abcdefghijklmnopqrstuvwxyz0123456789":
        setattr(m, "K_" + ch, ord(ch))
    m.Rect, m.Surface, m.error = Rect, Surface, error
    m.Event = _Event
    m.init = lambda: (6, 0)
    m.quit = lambda: None
    m.draw = _Draw

    tr = types.SimpleNamespace()
    tr.scale = lambda s, size: Surface._wrap(
        s.im.resize((max(1, int(size[0])), max(1, int(size[1]))), Image.NEAREST), s.hasalpha)
    def flip(s, fx, fy):
        im = s.im
        if fx: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if fy: im = im.transpose(Image.FLIP_TOP_BOTTOM)
        return Surface._wrap(im, s.hasalpha)
    tr.flip = flip
    m.transform = tr

    img = types.SimpleNamespace()
    img.load = lambda p: Surface._wrap(Image.open(p).convert("RGBA"), True)
    img.save = lambda s, p: s.im.save(p)
    m.image = img

    def set_mode(size, flags=0):
        if size == (0, 0):
            size = (1920, 1080)
        _Harness.screen = Surface(size)
        _Harness.screen_size = size
        return _Harness.screen
    m.display = types.SimpleNamespace(
        set_mode=set_mode, get_surface=lambda: _Harness.screen, flip=lambda: None,
        set_caption=lambda *_: None, set_icon=lambda *_: None)

    def ev_get():
        evs, _Harness.events = _Harness.events, []
        return evs
    m.event = types.SimpleNamespace(get=ev_get, post=lambda e: _Harness.events.append(e),
                                    Event=_Event)
    m.key = types.SimpleNamespace(get_pressed=lambda: _Pressed(), get_mods=lambda: _Harness.mods)
    m.mouse = types.SimpleNamespace(get_pos=lambda: _Harness.mouse)
    m.time = types.SimpleNamespace(Clock=_Clock)
    m.mixer = types.SimpleNamespace(pre_init=lambda *a, **k: None, init=lambda *a, **k: None,
                                    get_init=lambda: (22050, -16, 1), Sound=_Sound)
    sys.modules["pygame"] = m
    m._harness = _Harness
    return m
