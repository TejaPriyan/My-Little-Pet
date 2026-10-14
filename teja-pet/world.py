"""The room: props, collision, A* navigation, day/night cycle and lighting."""
import heapq
import math
import time

import pygame

from config import W, H, HUD_H, FLOOR_Y, BAR_Y, WEATHER_MODES
from utils import lerp as _lerp, mix as _mix, smooth as _smooth

CELL = 6                     # navigation grid resolution (px)
FEET_W, FEET_H = 10, 4       # pet foot hitbox used for collision
NAV_MARGIN = 2.0             # extra clearance paths keep from furniture


# ---------------------------------------------------------------- day / night
class DayNight:
    SKY = [(0, ((14, 16, 52), (36, 40, 96))), (5, ((14, 16, 52), (36, 40, 96))),
           (6.5, ((255, 170, 140), (255, 214, 150))), (8.5, ((96, 176, 240), (190, 228, 250))),
           (16.5, ((96, 176, 240), (190, 228, 250))), (18.5, ((120, 80, 150), (255, 150, 100))),
           (20.5, ((14, 16, 52), (36, 40, 96))), (24, ((14, 16, 52), (36, 40, 96)))]

    def __init__(self, mode="real"):
        self.mode = mode
        self.hour = self._real_hour()
        self.daylight = self._target()

    @staticmethod
    def _real_hour():
        t = time.localtime()
        return t.tm_hour + t.tm_min / 60.0 + t.tm_sec / 3600.0

    @staticmethod
    def light_at(h):
        if 7 <= h <= 17:
            return 1.0
        if 5 <= h < 7:
            return _smooth((h - 5) / 2)
        if 17 < h <= 19.5:
            return 1 - _smooth((h - 17) / 2.5)
        return 0.0

    def _target(self):
        return self.light_at(self.hour)

    def set_mode(self, mode):
        self.mode = mode

    def update(self, dt):
        if self.mode == "real":
            self.hour = self._real_hour()
        elif self.mode == "fast":
            self.hour = (self.hour + dt * 24.0 / 120.0) % 24     # full day in 2 minutes
        elif self.mode == "day":
            self.hour = 12.0
        elif self.mode == "night":
            self.hour = 23.0
        self.daylight += (self._target() - self.daylight) * min(1.0, dt * 2.0)

    @property
    def darkness(self):
        return 1.0 - self.daylight

    def sky_colors(self):
        h = self.hour
        for (h0, c0), (h1, c1) in zip(self.SKY, self.SKY[1:]):
            if h0 <= h <= h1:
                t = (h - h0) / (h1 - h0) if h1 > h0 else 0
                return _mix(c0[0], c1[0], t), _mix(c0[1], c1[1], t)
        return self.SKY[0][1]


# ---------------------------------------------------------------- props
class Prop:
    def __init__(self, name, frames, pos, collider=None, fps=0.0, layer="floor"):
        self.name = name
        self.frames = frames if isinstance(frames, list) else [frames]
        self.x, self.y = pos
        w, h = self.frames[0].get_size()
        self.rect = pygame.Rect(self.x, self.y, w, h)
        self.collider = pygame.Rect(collider) if collider else None
        self.fps = fps
        self.layer = layer
        self.frame_index = 0
        self.sort_y = self.rect.bottom

    def image(self, t):
        if self.fps and len(self.frames) > 1:
            return self.frames[int(t * self.fps) % len(self.frames)]
        return self.frames[self.frame_index % len(self.frames)]

    def draw(self, surf, t):
        surf.blit(self.image(t), (self.x, self.y))

    def hit(self, pt):
        if not self.rect.collidepoint(pt):
            return False
        img = self.frames[0]
        try:
            return img.get_at((int(pt[0] - self.x), int(pt[1] - self.y)))[3] > 20
        except (IndexError, ValueError):
            return True


class World:
    BOUNDS = pygame.Rect(16, 106, 448, 132)      # where the pet's feet may be

    def __init__(self, assets):
        self.assets = assets
        a = assets
        self.bed = Prop("bed", a.bed, (14, 102), collider=(14, 116, 64, 26))
        self.table = Prop("table", a.table, (326, 108), collider=(329, 130, 30, 10))
        self.plant = Prop("plant", a.plant, (436, 100), collider=(440, 124, 16, 10), fps=1.5)
        self.food = Prop("food", a.food, (400, 214), collider=(402, 218, 12, 6))
        self.water = Prop("water", a.water, (428, 214), collider=(430, 218, 12, 6))
        self.door = Prop("door", a.door, (396, 42), layer="wall")
        self.window = Prop("window", a.window, (104, 44), layer="wall")
        self.picture = Prop("picture", a.decor["picture"], (190, 48), layer="wall")
        self.clock = Prop("clock", a.decor["clock"], (232, 52), layer="wall")
        self.shelf = Prop("shelf", a.decor["shelf"], (262, 56), layer="wall")
        self.rug = Prop("rug", a.rug, (170, 164), layer="ground")
        self.cushion = Prop("cushion", a.decor["cushion"], (286, 176), layer="ground")
        self.floor_props = [self.bed, self.table, self.plant, self.food, self.water]
        self.colliders = [p.collider for p in self.floor_props if p.collider]
        self.clickable = [self.food, self.water, self.plant, self.table, self.bed, self.door,
                          self.window, self.picture, self.clock, self.shelf, self.cushion]

        # Toy (a ball that moves while the pet plays)
        self.toy_home = (292.0, 220.0)
        self.toy = [self.toy_home[0], self.toy_home[1]]
        self.toy_z = 0.0
        self.bowl_full = False
        self.bowl_timer = 0.0

        # Named places the pet can walk to
        self.anchors = {
            "bed_approach": (48, 152), "bed_spot": (36, 127),
            "food": (386, 222), "water": (452, 222),
        }
        self.landmarks = {                     # click-to-visit spots (stand point, comments)
            "door": ((413, 112), ["OUTSIDE?", "NOT TODAY!", "I WANT A WALK!"]),
            "window": ((130, 110), ["NICE VIEW!", "LOOK, THE SKY!", "BIRDS?"]),
            "plant": ((428, 132), ["SMELLS GREEN!", "HELLO PLANT!", "LEAVES!"]),
            "table": ((344, 152), ["FLOWERS!", "WHAT'S UP THERE?", "TABLE!"]),
            "picture": ((201, 112), ["PRETTY!", "NICE ART!"]),
            "clock": ((243, 112), ["TICK TOCK...", "WHAT TIME?"]),
            "shelf": ((280, 112), ["BOOKS!", "TOO HIGH!"]),
            "cushion": ((294, 198), ["SOFT!", "COZY!"]),
        }
        self._build_grid()
        self.motes = [[110 + (i * 37) % 100, 92 + (i * 53) % 70, 0.0, 0.0, i * 1.7] for i in range(9)]
        self.stars = [(6 + (i * 13) % 38, 4 + (i * 7) % 14, i * 0.9) for i in range(10)]
        self._bulb_cols = [(255, 120, 150), (255, 220, 100), (120, 220, 200), (255, 160, 90)]
        self._overlay = pygame.Surface((W, BAR_Y - HUD_H), pygame.SRCALPHA)
        self._light = pygame.Surface((W, BAR_Y - HUD_H), pygame.SRCALPHA)
        self._glow = {}

        # Weather system (window atmosphere)
        self.weather = "clear"
        self.weather_override = None
        self.weather_timer = 0.0
        self.rain_drops = [[float((i * 17) % 44), float((i * 23) % 28), 65.0 + (i * 11) % 35] for i in range(18)]
        self.snow_flakes = [[float((i * 13) % 44), float((i * 19) % 28), 12.0 + (i * 7) % 14, i * 0.7] for i in range(16)]

    # ---------------------------------------------------------------- collision
    def is_free(self, x, y, m=0.0):
        """True if the pet's feet box at (x, y) is inside the room and clear of
        furniture. `m` adds clearance around furniture (used for navigation)."""
        b = self.BOUNDS
        if not (b.x <= x <= b.right and b.y <= y <= b.bottom):
            return False
        left, right = x - FEET_W / 2.0 - m, x + FEET_W / 2.0 + m
        top, bottom = y - FEET_H - m, y + m
        for c in self.colliders:
            if right > c.x and left < c.right and bottom > c.y and top < c.bottom:
                return False
        return True

    def try_move(self, x, y, dx, dy):
        """Axis-separated movement with sliding. Returns the new (x, y)."""
        if not self.is_free(x, y):                     # stuck? let the pet walk out
            return x + dx, y + dy
        if self.is_free(x + dx, y):
            x += dx
        if self.is_free(x, y + dy):
            y += dy
        return x, y

    def segment_free(self, a, b, m=None):
        """Line of sight with clearance, sampled finely enough to catch corners."""
        m = NAV_MARGIN if m is None else m
        dist = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(dist / 1.5))
        return all(self.is_free(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, m)
                   for i in range(1, n + 1))

    # ---------------------------------------------------------------- navigation
    def _build_grid(self):
        b = self.BOUNDS
        self.gw, self.gh = b.w // CELL + 1, b.h // CELL + 1
        self.blocked = [[not self.is_free(b.x + i * CELL, b.y + j * CELL, NAV_MARGIN)
                         for i in range(self.gw)] for j in range(self.gh)]

    def _cell(self, x, y):
        i = int(round((x - self.BOUNDS.x) / CELL))
        j = int(round((y - self.BOUNDS.y) / CELL))
        return max(0, min(self.gw - 1, i)), max(0, min(self.gh - 1, j))

    def _pt(self, c):
        return (self.BOUNDS.x + c[0] * CELL, self.BOUNDS.y + c[1] * CELL)

    def _open(self, c):
        return 0 <= c[0] < self.gw and 0 <= c[1] < self.gh and not self.blocked[c[1]][c[0]]

    def _nearest_open(self, c):
        if self._open(c):
            return c
        for r in range(1, 14):
            best = None
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    if max(abs(di), abs(dj)) != r:
                        continue
                    n = (c[0] + di, c[1] + dj)
                    if self._open(n):
                        d = di * di + dj * dj
                        if best is None or d < best[0]:
                            best = (d, n)
            if best:
                return best[1]
        return None

    def nearest_free(self, x, y):
        c = self._nearest_open(self._cell(x, y))
        return self._pt(c) if c else None

    def find_path(self, start, goal):
        """A* on the grid, then line-of-sight smoothing. Returns [(x, y), ...] or None."""
        s = self._nearest_open(self._cell(*start))
        g = self._nearest_open(self._cell(*goal))
        if s is None or g is None:
            return None
        end = goal if self.is_free(*goal) else self._pt(g)
        if s == g:
            return [end]

        def h(c):
            dx, dy = abs(c[0] - g[0]), abs(c[1] - g[1])
            return (dx + dy) + (1.414 - 2) * min(dx, dy)

        openq = [(h(s), 0, s)]
        cost, parent, counter = {s: 0.0}, {s: None}, 0
        while openq:
            _, _, cur = heapq.heappop(openq)
            if cur == g:
                break
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (cur[0] + di, cur[1] + dj)
                if not self._open(n):
                    continue
                if di and dj and not (self._open((cur[0] + di, cur[1])) and
                                      self._open((cur[0], cur[1] + dj))):
                    continue                       # no cutting corners
                nc = cost[cur] + (1.414 if di and dj else 1.0)
                if nc < cost.get(n, 1e9):
                    cost[n] = nc
                    parent[n] = cur
                    counter += 1
                    heapq.heappush(openq, (nc + h(n), counter, n))
        if g not in parent:
            return None
        cells = []
        c = g
        while c is not None:
            cells.append(c)
            c = parent[c]
        cells.reverse()
        pts = [tuple(start)] + [self._pt(c) for c in cells[1:-1]] + [end]
        out, i = [], 0
        while i < len(pts) - 1:                    # string-pulling smoothing
            j = len(pts) - 1
            while j > i + 1 and not self.segment_free(pts[i], pts[j]):
                j -= 1
            out.append(pts[j])
            i = j
        return out

    def random_free_point(self, rng, near=None, radius=90):
        for _ in range(40):
            if near:
                x = near[0] + rng.uniform(-radius, radius)
                y = near[1] + rng.uniform(-radius * 0.6, radius * 0.6)
            else:
                x = rng.uniform(self.BOUNDS.x + 8, self.BOUNDS.right - 8)
                y = rng.uniform(self.BOUNDS.y + 4, self.BOUNDS.bottom - 4)
            if self.is_free(x, y):
                return (x, y)
        return self.nearest_free(*(near or (240, 190)))

    # ---------------------------------------------------------------- toy / bowl
    def toy_stand(self):
        return self.nearest_free(self.toy[0] - 18, self.toy[1] + 4)

    def toy_hit_rect(self):
        return pygame.Rect(int(self.toy[0]) - 6, int(self.toy[1]) - 6 - int(self.toy_z), 12, 12)

    def object_at(self, pt):
        if self.toy_hit_rect().collidepoint(pt):
            return "toy"
        for p in self.clickable:
            if p.hit(pt):
                return p.name
        return None

    # ---------------------------------------------------------------- update
    def update(self, dt):
        if self.bowl_full and self.bowl_timer > 0:
            self.bowl_timer -= dt
            if self.bowl_timer <= 0:
                self.bowl_full = False
        self.food.frame_index = 0 if self.bowl_full else 1
        for m in self.motes:
            m[4] += dt
            m[0] += math.sin(m[4] * 0.8) * 4 * dt
            m[1] -= 3 * dt
            if m[1] < 84:
                m[1] = 150
                m[0] = 110 + (m[0] * 7) % 100

        # Dynamic weather cycle (changes gently every ~120s)
        self.weather_timer += dt
        cycle = int(self.weather_timer / 120.0) % 4
        self.weather = self.weather_override or ["clear", "rain", "clear", "snow"][cycle]

        if self.weather == "rain":
            for r in self.rain_drops:
                r[1] += r[2] * dt
                r[0] += 16 * dt
                if r[1] >= 28:
                    r[1] = 0.0
                    r[0] = (r[0] + 7) % 44
        elif self.weather == "snow":
            for s in self.snow_flakes:
                s[3] += dt
                s[1] += s[2] * dt
                s[0] += math.sin(s[3] * 1.5) * 8 * dt
                if s[1] >= 28:
                    s[1] = 0.0
                    s[0] = (s[0] + 11) % 44

    def set_weather(self, mode):
        self.weather_override = mode if mode in WEATHER_MODES else None
        if mode in WEATHER_MODES:
            self.weather = mode

    # ---------------------------------------------------------------- drawing
    def draw_background(self, surf, t, dn):
        surf.blit(self.assets.room, (0, HUD_H))
        self._draw_window(surf, t, dn)
        for p in (self.picture, self.clock, self.shelf, self.door):
            p.draw(surf, t)
        self._draw_lights(surf, t)
        for p in (self.rug, self.cushion):
            p.draw(surf, t)
        self._draw_light_shaft(surf, t, dn)

    def _draw_window(self, surf, t, dn):
        gw, gh = 44, 28
        sky = pygame.Surface((gw, gh))
        top, bot = dn.sky_colors()
        if self.weather == "rain":
            top = _mix(top, (80, 95, 120), 0.5)
            bot = _mix(bot, (120, 135, 160), 0.5)
        elif self.weather == "snow":
            top = _mix(top, (160, 175, 195), 0.4)
            bot = _mix(bot, (200, 210, 225), 0.4)
        for y in range(gh):
            sky.fill(_mix(top, bot, y / (gh - 1)), (0, y, gw, 1))
        h = dn.hour
        dark = dn.darkness
        if dark > 0.35 and self.weather == "clear":           # stars
            for sx, sy, ph in self.stars:
                if int(t * 1.5 + ph) % 3:
                    v = int(170 + 80 * dark)
                    sky.fill((v, v, 255), (sx, sy, 1, 1))
        if 6 <= h <= 18:                                      # sun arc
            p = (h - 6) / 12.0
            cx, cy = 4 + int(p * 36), 24 - int(math.sin(p * math.pi) * 16)
            sun_col = (210, 190, 110) if self.weather != "clear" else (255, 214, 90)
            pygame.draw.circle(sky, sun_col, (cx, cy), 4)
            pygame.draw.circle(sky, (255, 244, 170), (cx, cy), 2)
        else:                                                 # moon arc
            p = ((h - 18) % 24) / 12.0
            cx, cy = 4 + int(p * 36), 24 - int(math.sin(p * math.pi) * 16)
            pygame.draw.circle(sky, (238, 238, 214), (cx, cy), 3)
            sky.set_at((cx - 1, cy), (200, 200, 180))
        if dn.daylight > 0.2:                                 # drifting clouds
            col = _mix((70, 76, 120), (255, 255, 255), dn.daylight)
            for off, yy in ((0, 8), (34, 17)):
                cx = int((t * 2 + off) % 64) - 14
                pygame.draw.ellipse(sky, col, (cx, yy, 12, 4))
                pygame.draw.ellipse(sky, col, (cx + 3, yy - 2, 7, 4))

        # Weather precipitation inside window
        if self.weather == "rain":
            for rx, ry, _spd in self.rain_drops:
                sky.fill((160, 205, 255), (int(rx), int(ry), 1, 3))
            if int(t * 8) % 2 == 0:
                sky.fill((220, 240, 255), ((int(t * 37) % 36) + 4, 26, 3, 1))
        elif self.weather == "snow":
            for sx, sy, _spd, _ph in self.snow_flakes:
                sky.fill((255, 255, 255), (int(sx), int(sy), 1, 1))
            sky.fill((235, 245, 255), (3, 26, 38, 2))

        surf.blit(sky, (self.window.x + 4, self.window.y + 4))
        self.window.draw(surf, t)

    def _bulbs(self, t):
        y0 = HUD_H + 5
        for i, x in enumerate(range(6, W, 12)):
            y = y0 + int(5 * math.sin(math.pi * (((x - 6) % 48) / 48.0)))
            lit = (i + int(t * 1.6)) % 3 != 0
            yield x, y + 3, self._bulb_cols[i % 4], lit

    def _draw_lights(self, surf, t):
        for x in range(0, W):
            y = HUD_H + 5 + int(5 * math.sin(math.pi * ((x % 48) / 48.0)))
            surf.set_at((x, y), (60, 90, 70))
        for x, y, col, lit in self._bulbs(t):
            c = col if lit else tuple(int(v * 0.55) for v in col)
            surf.fill((52, 40, 82), (x - 1, y - 1, 4, 4))
            surf.fill(c, (x, y, 2, 2))

    def _draw_light_shaft(self, surf, t, dn):
        dl = dn.daylight
        if dl < 0.05 and dn.darkness < 0.5:
            return
        shift = int((dn.hour - 12) * 5)
        wx, bot_y = self.window.x, 150
        light = self._light
        light.fill((0, 0, 0, 0))
        pts = [(wx + 4, 84 - HUD_H), (wx + 48, 84 - HUD_H),
               (wx + 48 + shift + 50, bot_y), (wx + 4 + shift + 50, bot_y)]
        if dl > 0.3:
            pygame.draw.polygon(light, (255, 244, 190, int(34 * dl)), pts)
        else:
            pygame.draw.polygon(light, (170, 190, 255, int(14 * dn.darkness)), pts)
        surf.blit(light, (0, HUD_H))
        if dl > 0.3:
            for x, y, _vx, _vy, ph in self.motes:
                if int(ph * 2) % 2:
                    surf.set_at((int(x), int(y)), (255, 250, 220))

    def draw_objects(self, surf, t, pet, assets):
        """Y-sorted drawing of furniture, toy and pet so depth looks right."""
        items = [(p.sort_y, 0, p) for p in self.floor_props]
        items.append((self.toy[1] + 5, 1, None))
        if pet is not None:
            items.append((pet.sort_y, 2, pet))
        for _, kind, obj in sorted(items, key=lambda i: (i[0], i[1])):
            if kind == 0:
                obj.draw(surf, t)
            elif kind == 1:
                self._draw_toy(surf, assets)
            else:
                pet.draw(surf, assets)

    def _draw_toy(self, surf, assets):
        x, y = int(self.toy[0]), int(self.toy[1])
        surf.blit(assets.shadow, (x - 8, y + 1), (0, 0, 16, 6))
        surf.blit(assets.toy, (x - 5, y - 8 - int(self.toy_z)))

    def _glow_sprite(self, col, r=7):
        key = (col, r)
        g = self._glow.get(key)
        if g is None:
            g = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
            for rad, a in ((r, 14), (r - 2, 22), (r - 4, 34)):
                if rad > 0:
                    pygame.draw.circle(g, col + (a,), (r, r), rad)
            self._glow[key] = g
        return g

    def draw_overlay(self, surf, t, dn):
        """Subtle day/night tint (never fully dark) plus warm light glows."""
        dark = dn.darkness
        tw = 1.0 - abs(dn.daylight * 2 - 1)
        alpha = int(min(110, dark * 88 + tw * 26))
        if alpha > 2:
            col = _mix((20, 24, 72), (255, 150, 90), tw * 0.9)
            self._overlay.fill(col + (alpha,))
            surf.blit(self._overlay, (0, HUD_H))
        if dark > 0.25:
            for x, y, col, lit in self._bulbs(t):
                if lit:
                    g = self._glow_sprite(col)
                    surf.blit(g, (x - 6, y - 6))
