"""Lightweight particle + floating-text system (hearts, dust, Zs, sparkles...)."""
import math
import random

from config import INK

MAX_PARTICLES = 320


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "kind", "color", "size", "grav")

    def __init__(self, x, y, vx, vy, life, kind, color=(255, 255, 255), size=1, grav=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.kind, self.color, self.size, self.grav = kind, color, size, grav


class FloatText:
    __slots__ = ("x", "y", "text", "color", "life", "max_life")

    def __init__(self, x, y, text, color, life=1.3):
        self.x, self.y, self.text, self.color = x, y, text, color
        self.life = self.max_life = life


class Effects:
    SPRITE_KINDS = ("heart", "spark", "bang", "note")

    def __init__(self, assets, font, rng=None):
        self.assets = assets
        self.font = font
        self.rng = rng or random.Random()
        self.parts = []
        self.texts = []

    # ---------------------------------------------------------------- update
    def update(self, dt):
        alive = []
        for p in self.parts:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.grav * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.parts = alive
        for t in self.texts:
            t.life -= dt
            t.y -= 14 * dt
        self.texts = [t for t in self.texts if t.life > 0]

    # ---------------------------------------------------------------- draw
    def draw(self, surf):
        for p in self.parts:
            frac = p.life / p.max_life
            if frac < 0.3 and int(p.life * 24) % 2 == 0:
                continue                                  # pixel-style fade: blink out
            if p.kind in self.SPRITE_KINDS:
                img = self.assets.fx.get(p.kind)
                if img:
                    surf.blit(img, (int(p.x) - 3, int(p.y) - 3))
            elif p.kind == "z":
                scale = 1 if frac < 0.55 else 2
                self.font.draw(surf, "Z", (p.x, p.y), p.color, scale, INK)
            else:
                s = p.size if frac > 0.4 else max(1, p.size - 1)
                surf.fill(p.color, (int(p.x), int(p.y), s, s))
        for t in self.texts:
            self.font.draw(surf, t.text, (t.x, t.y), t.color, 1, INK, anchor="midtop")

    # ---------------------------------------------------------------- emitters
    def _add(self, p):
        if len(self.parts) < MAX_PARTICLES:
            self.parts.append(p)

    def hearts(self, x, y, n=3):
        for _ in range(n):
            self._add(Particle(x + self.rng.uniform(-8, 8), y + self.rng.uniform(-4, 2),
                               self.rng.uniform(-6, 6), self.rng.uniform(-22, -14),
                               self.rng.uniform(0.9, 1.4), "heart"))

    def sparkles(self, x, y, n=4, spread=12):
        for _ in range(n):
            self._add(Particle(x + self.rng.uniform(-spread, spread), y + self.rng.uniform(-spread, 4),
                               self.rng.uniform(-8, 8), self.rng.uniform(-14, -4),
                               self.rng.uniform(0.6, 1.0), "spark"))

    def bang(self, x, y):
        self._add(Particle(x, y, 0, -10, 0.8, "bang"))

    def note(self, x, y):
        self._add(Particle(x, y, self.rng.uniform(-6, 6), -14, 1.0, "note"))

    def zzz(self, x, y):
        self._add(Particle(x, y, 7, -9, 1.8, "z", (214, 214, 255)))

    def dust(self, x, y):
        for _ in range(2):
            self._add(Particle(x + self.rng.uniform(-3, 3), y - 1, self.rng.uniform(-8, 8),
                               self.rng.uniform(-8, -2), self.rng.uniform(0.25, 0.45), "px",
                               (236, 214, 184), 1, 20))

    def crumbs(self, x, y, food="kibble"):
        colors = {"berries": [(197,80,118), (111,103,186)], "fish": [(250,174,158), (255,220,192)],
                  "greens": [(79,147,78), (133,193,91)], "milk": [(255,250,230), (196,227,239)],
                  "soup": [(244,177,67), (95,155,86)], "feast": [(250,232,185), (236,141,106), (106,176,107)]}
        for _ in range(3):
            self._add(Particle(x, y, self.rng.uniform(-16, 16), self.rng.uniform(-26, -12),
                               self.rng.uniform(0.35, 0.6), "px",
                               self.rng.choice(colors.get(food, [(196, 124, 74), (232, 164, 100)])), 1, 90))

    def burst(self, x, y):
        """Level-up celebration."""
        for i in range(26):
            a = self.rng.uniform(0, math.tau)
            sp = self.rng.uniform(30, 80)
            col = self.rng.choice([(255, 220, 80), (255, 128, 164), (120, 200, 255), (255, 255, 255)])
            self._add(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp - 20,
                               self.rng.uniform(0.7, 1.3), "px", col, 2, 60))
        self.sparkles(x, y - 6, 8, 18)
        self.hearts(x, y - 8, 4)

    def text(self, x, y, msg, color):
        self.texts.append(FloatText(x, y, msg, color))
