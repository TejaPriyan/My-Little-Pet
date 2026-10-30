"""Pixel-art UI: nine-slice panels, hover buttons, HUD, speech bubbles, dialogs.

All drawing happens on the 480x270 internal canvas. Mouse positions passed in
are already converted to internal coordinates.
"""
import math

import pygame

from config import (W, H, HUD_H, BAR_Y, INK, CREAM, CREAM_DK, PINK, GOLD, WHITE, BAR_BG,
                    C_HAPPY, C_HUNGER, C_ENERGY, C_XP, SHOP_ITEMS, ACHIEVEMENTS)
from settings import FPS_OPTIONS, TIME_MODES, PET_SIZES
from utils import LRUCache

RED = (255, 84, 84)
GREY = (150, 130, 150)


def _ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


class NineSlice:
    """Stretchable bordered image so panels/buttons work at any size."""

    def __init__(self, img, corner=4):
        self.img, self.c, self.cache = img, corner, {}

    def render(self, w, h):
        key = (w, h)
        out = self.cache.get(key)
        if out is not None:
            return out
        c = self.c
        iw, ih = self.img.get_size()
        xs_s, xs_d = (0, c, iw - c, iw), (0, c, w - c, w)
        ys_s, ys_d = (0, c, ih - c, ih), (0, c, h - c, h)
        out = pygame.Surface((w, h), pygame.SRCALPHA)
        for j in range(3):
            for i in range(3):
                sw, sh = xs_s[i + 1] - xs_s[i], ys_s[j + 1] - ys_s[j]
                dw, dh = xs_d[i + 1] - xs_d[i], ys_d[j + 1] - ys_d[j]
                if min(sw, sh, dw, dh) <= 0:
                    continue
                piece = self.img.subsurface(pygame.Rect(xs_s[i], ys_s[j], sw, sh))
                if (dw, dh) != (sw, sh):
                    piece = pygame.transform.scale(piece, (dw, dh))
                out.blit(piece, (xs_d[i], ys_d[j]))
        self.cache[key] = out
        return out


class Button:
    def __init__(self, key, label, icon, tip, rect):
        self.key, self.label, self.icon, self.tip = key, label, icon, tip
        self.rect = pygame.Rect(rect)
        self.hover = 0.0
        self.flash = 0.0
        self.active = False

    def update(self, dt, mouse):
        inside = mouse is not None and self.rect.collidepoint((int(mouse[0]), int(mouse[1])))
        self.hover += ((1.0 if inside else 0.0) - self.hover) * min(1.0, dt * 14)
        self.flash = max(0.0, self.flash - dt)

    @property
    def hovered(self):
        return self.hover > 0.5

    def draw(self, surf, ui):
        pressed = self.flash > 0 or self.active
        frame = 2 if pressed else (1 if self.hovered else 0)
        r = self.rect.move(0, 1 if pressed else (-1 if self.hovered else 0))
        surf.blit(ui.btn[frame].render(r.w, r.h), r)
        ic = ui.assets.icons.get(self.icon)
        tw = ui.font.width(self.label)
        if tw + 12 > r.w - 6:
            ic = None
        total = (9 + 3 if ic else 0) + tw
        x = r.x + (r.w - total) // 2
        if ic:
            surf.blit(ic, (x, r.y + (r.h - 9) // 2))
            x += 12
        ui.font.draw(surf, self.label, (x, r.y + (r.h - 7) // 2), INK)


class UI:
    def __init__(self, assets, font):
        self.assets, self.font = assets, font
        self.panel = NineSlice(assets.panel, 4)
        self.btn = [NineSlice(assets.buttons[i], 4) for i in range(3)]
        self.disp = {"hunger": 0.0, "happiness": 0.0, "energy": 0.0}
        self.disp_init = False
        self.t = 0.0
        self.toasts = []
        self.banner = None
        self._bubble_cache = LRUCache(maxsize=80)
        self.dim = pygame.Surface((W, H), pygame.SRCALPHA)
        self.dim.fill((24, 12, 44, 150))
        self.mouse = None
        self.buttons = self._make_buttons()

    # ---------------------------------------------------------------- layout
    def _make_buttons(self):
        spec = [
            ("home", "HOME", "home", "GO HOME (H)"),
            ("feed", "FEED", "apple", "FEED (F)"),
            ("play", "PLAY", "ball", "PLAY (P)"),
            ("sleep", "SLEEP", "moon", "SLEEP (S)"),
            ("pet", "PET", "heart", "PET (E)"),
            ("game", "GAME", "spark", "MINI-GAME (G)"),
            ("follow", "TAIL", "paw", "FOLLOW MODE (C)"),
            ("shop", "SHOP", "coin", "SHOP (B)"),
            ("stats", "STATS", "star", "STATS & AWARDS (T)"),
            ("desktop", "DESK", "desk", "DESKTOP PET (D)"),
            ("menu", "MENU", "gear", "SETTINGS (ESC)")
        ]
        bw, gap = 41, 2
        x0 = (W - (len(spec) * bw + (len(spec) - 1) * gap)) // 2
        return [Button(k, lab, ic, tip, (x0 + i * (bw + gap), BAR_Y + 3, bw, 20))
                for i, (k, lab, ic, tip) in enumerate(spec)]

    def button(self, key):
        return next(b for b in self.buttons if b.key == key)

    # ---------------------------------------------------------------- update
    def update(self, dt, mouse, pet=None):
        self.t += dt
        self.mouse = mouse
        for b in self.buttons:
            b.update(dt, mouse)
        if pet is not None:
            target = {"hunger": pet.hunger, "happiness": pet.happiness, "energy": pet.energy}
            for k, v in target.items():
                if not self.disp_init:
                    self.disp[k] = v
                else:
                    d = v - self.disp[k]
                    self.disp[k] += max(-60 * dt, min(60 * dt, d))
            self.disp_init = True
        for t in self.toasts:
            t[2] -= dt
        self.toasts = [t for t in self.toasts if t[2] > 0]
        if self.banner:
            self.banner["t"] += dt
            if self.banner["t"] > 3.2:
                self.banner = None

    def click(self, pos):
        for b in self.buttons:
            if b.rect.collidepoint((int(pos[0]), int(pos[1]))):
                b.flash = 0.12
                return b.key
        return None

    def toast(self, msg, color=WHITE, dur=2.0):
        self.toasts = [t for t in self.toasts if t[0] != msg][-2:]
        self.toasts.append([msg, color, dur])

    def show_banner(self, name, level):
        self.banner = {"name": name, "level": level, "t": 0.0}

    # ---------------------------------------------------------------- helpers
    def text(self, surf, s, pos, color=INK, scale=1, shadow=None, anchor="topleft"):
        return self.font.draw(surf, s, pos, color, scale, shadow, anchor)

    def draw_panel(self, surf, rect):
        r = pygame.Rect(rect)
        surf.blit(self.panel.render(r.w, r.h), r)

    def small_button(self, surf, rect, label, hover, pressed=False):
        r = pygame.Rect(rect)
        frame = 2 if pressed else (1 if hover else 0)
        rr = r.move(0, -1 if (hover and not pressed) else (1 if pressed else 0))
        surf.blit(self.btn[frame].render(rr.w, rr.h), rr)
        self.text(surf, label, (rr.centerx, rr.centery - 3), INK, anchor="midtop")

    def _bar(self, surf, x, y, value, color, low):
        segs, sw, h = 10, 6, 7
        surf.fill(INK, (x, y, segs * (sw + 1) + 1, h))
        light = tuple(min(255, c + 60) for c in color)
        if low and int(self.t * 3) % 2 == 0:
            color = RED
            light = (255, 160, 160)
        for i in range(segs):
            sx = x + 1 + i * (sw + 1)
            surf.fill(BAR_BG, (sx, y + 1, sw, h - 2))
            frac = (value - i * 10) / 10.0
            if frac > 0:
                fw = max(1, int(sw * min(1.0, frac) + 0.5))
                surf.fill(color, (sx, y + 1, fw, h - 2))
                surf.fill(light, (sx, y + 1, fw, 1))

    # ---------------------------------------------------------------- HUD
    def draw_hud(self, surf, pet):
        self.draw_panel(surf, (0, 0, W, HUD_H))
        name = pet.name.upper()
        self.text(surf, name, (8, 5), INK)
        x = 8 + self.font.width(name) + 6
        mood_col = {"happy": C_HAPPY, "sad": (120, 170, 255), "sleepy": (180, 150, 230), "ok": C_ENERGY}.get(pet.mood, INK)
        self.text(surf, "[%s]" % pet.mood.upper(), (x, 5), mood_col)
        x += self.font.width("[%s]" % pet.mood.upper()) + 6
        self.text(surf, "LV %02d" % pet.level, (x, 5), (150, 90, 200))
        x += self.font.width("LV 00") + 6
        need = pet.xp_needed
        surf.fill(INK, (x, 5, 62, 7))
        surf.fill(BAR_BG, (x + 1, 6, 60, 5))
        surf.fill(C_XP, (x + 1, 6, int(60 * min(1.0, pet.xp / need)), 5))
        surf.fill((190, 215, 255), (x + 1, 6, int(60 * min(1.0, pet.xp / need)), 1))
        self.text(surf, "%d/%d" % (pet.xp, need), (x + 66, 5), GREY)
        coins = str(pet.coins)
        cw = self.font.width(coins)
        surf.blit(self.assets.icons["coin"], (W - 8 - cw - 12, 4))
        self.text(surf, coins, (W - 8 - cw, 5), (170, 110, 20))

        rows = (("happiness", "HAPPY", "heart", C_HAPPY), ("hunger", "FOOD", "apple", C_HUNGER),
                ("energy", "ENERGY", "bolt", C_ENERGY))
        for i, (key, label, icon, col) in enumerate(rows):
            gx = 8 + i * 160
            v = self.disp[key]
            surf.blit(self.assets.icons[icon], (gx, 18))
            self.text(surf, label, (gx + 12, 19), INK)
            self._bar(surf, gx + 49, 18, v, col, getattr(pet, key) < 25)
            self.text(surf, "%d" % round(getattr(pet, key)), (gx + 124, 19), INK)

    def draw_bar(self, surf):
        self.draw_panel(surf, (0, BAR_Y, W, H - BAR_Y))
        for b in self.buttons:
            b.draw(surf, self)
        for b in self.buttons:
            if b.hovered and not b.flash:
                w = self.font.width(b.tip) + 8
                x = max(2, min(W - w - 2, b.rect.centerx - w // 2))
                self.draw_panel(surf, (x, BAR_Y - 17, w, 14))
                self.text(surf, b.tip, (x + 4, BAR_Y - 14), INK)

    def draw_overlays(self, surf, follow_on):
        if follow_on:
            s = "FOLLOW MODE: ON"
            w = self.font.width(s) + 10
            self.draw_panel(surf, (W - w - 4, HUD_H + 4, w, 14))
            self.text(surf, s, (W - w + 1, HUD_H + 7), (60, 150, 80))
        y = HUD_H + 6
        for msg, col, life in self.toasts:
            w = self.font.width(msg) + 12
            x = (W - w) // 2
            self.draw_panel(surf, (x, y, w, 15))
            self.text(surf, msg, (x + 6, y + 4), INK)
            y += 17
        if self.banner:
            self._draw_banner(surf)

    def _draw_banner(self, surf):
        b = self.banner
        t = b["t"]
        slide = _ease_out(t / 0.5) if t < 2.6 else 1 - _ease_out((t - 2.6) / 0.6)
        w, h = 176, 50
        x, y = (W - w) // 2, int(-h + (HUD_H + 14 + h) * slide)
        self.draw_panel(surf, (x, y, w, h))
        star = self.assets.icons["star"]
        bob = int(math.sin(self.t * 8) * 2)
        for sx in (x + 10, x + w - 28):
            surf.blit(pygame.transform.scale(star, (18, 18)), (sx, y + 8 + bob))
        self.text(surf, "LEVEL UP!", (x + w // 2, y + 7), (230, 90, 140), 2, WHITE, "midtop")
        self.text(surf, "%s  LEVEL %02d" % (b["name"].upper(), b["level"]),
                  (x + w // 2, y + 30), INK, 1, None, "midtop")

    # ---------------------------------------------------------------- speech bubble
    def draw_bubble(self, surf, pet):
        if pet.bubble_t <= 0 or not pet.bubble_text:
            return
        age = pet.bubble_dur - pet.bubble_t
        a = min(1.0, age / 0.15, pet.bubble_t / 0.6)
        if a <= 0:
            return
        text = pet.bubble_text
        img = self._bubble_cache.get(text)
        if img is None:
            tw = self.font.width(text)
            w, h = tw + 10, 15
            img = pygame.Surface((w, h + 4), pygame.SRCALPHA)
            img.fill(INK, (1, 0, w - 2, h))
            img.fill(INK, (0, 1, w, h - 2))
            img.fill((255, 252, 244), (1, 1, w - 2, h - 2))
            cx = w // 2 - 2
            img.fill((255, 252, 244), (cx + 1, h - 1, 3, 1))
            img.fill((255, 252, 244), (cx + 1, h, 3, 1))
            img.fill(INK, (cx, h, 1, 1))
            img.fill(INK, (cx + 4, h, 1, 1))
            img.fill((255, 252, 244), (cx + 2, h + 1, 1, 1))
            img.fill(INK, (cx + 1, h + 1, 1, 1))
            img.fill(INK, (cx + 3, h + 1, 1, 1))
            img.fill(INK, (cx + 2, h + 2, 1, 1))
            img.blit(self.font.render(text, INK), (5, 4))
            self._bubble_cache.put(text, img)
        img.set_alpha(int(255 * a))
        bob = int(math.sin(self.t * 3) * 1)
        x = int(pet.x - img.get_width() // 2)
        x = max(2, min(W - img.get_width() - 2, x))
        y = max(HUD_H + 2, int(pet.y - 24 - img.get_height() - pet.z) + bob)
        surf.blit(img, (x, y))


# =====================================================================
# Overlays: each has update(dt, mouse), draw(surf), on_key(ev), on_click(pos)
# =====================================================================
class NameScreen:
    MAX = 12

    def __init__(self, ui, assets, on_submit, pet_name="", owner_name="", on_cancel=None):
        self.ui, self.assets, self.on_submit = ui, assets, on_submit
        self.text = pet_name
        self.owner_text = owner_name
        self.focus = "pet"
        self.on_cancel = on_cancel
        self.t = 0.0
        self.mouse = None
        self.rect = pygame.Rect(100, 18, 280, 234)
        self.pet_box = pygame.Rect(170, 132, 140, 20)
        self.owner_box = pygame.Rect(170, 177, 140, 20)
        self.start = pygame.Rect(200, 211, 80, 20)
        self.modal = True

    def update(self, dt, mouse):
        self.t += dt
        self.mouse = mouse

    def _submit(self):
        self.on_submit(self.text.strip() or "Mochi", self.owner_text.strip() or "Friend")

    def on_key(self, ev):
        if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._submit()
        elif ev.key == pygame.K_ESCAPE and self.on_cancel:
            self.on_cancel()
        elif ev.key == pygame.K_TAB:
            self.focus = "owner" if self.focus == "pet" else "pet"
        else:
            attr = "text" if self.focus == "pet" else "owner_text"
            value = getattr(self, attr)
            if ev.key == pygame.K_BACKSPACE:
                setattr(self, attr, value[:-1])
                return
            ch = getattr(ev, "unicode", "")
            if ch and len(value) < self.MAX and ch.isascii() and (ch.isalnum() or ch in " -"):
                if not (ch == " " and not value):
                    setattr(self, attr, value + ch)

    def on_click(self, pos):
        if self.pet_box.collidepoint(pos): self.focus = "pet"
        if self.owner_box.collidepoint(pos): self.focus = "owner"
        if self.start.collidepoint((int(pos[0]), int(pos[1]))):
            self._submit()

    def draw(self, surf):
        ui = self.ui
        surf.blit(ui.dim, (0, 0))
        ui.draw_panel(surf, self.rect)
        cx = self.rect.centerx
        ui.text(surf, "YOUR LITTLE FAMILY" if self.on_cancel else "MY LITTLE PET", (cx, 31), (150, 90, 200), 2, WHITE, "midtop")
        clip = self.assets.pet["idle"]
        fr = clip.frames[int(self.t * 3) % len(clip.frames)]
        surf.blit(pygame.transform.scale(fr, (48, 48)), (cx - 24, 62))
        for field, label, value, box in (("pet", "YOUR PET'S NAME", self.text, self.pet_box),
                                         ("owner", "YOUR NAME (OWNER)", self.owner_text, self.owner_box)):
            ui.text(surf, label, (cx, box.y - 12), INK, 1, None, "midtop")
            surf.fill(PINK if self.focus == field else INK, box)
            surf.fill((255, 252, 244), box.inflate(-2, -2))
            shown = value.upper() + ("_" if self.focus == field and int(self.t * 2) % 2 == 0 else " ")
            ui.text(surf, shown, (box.x + 6, box.y + 7), INK)
        hover = self.mouse is not None and self.start.collidepoint((int(self.mouse[0]), int(self.mouse[1])))
        ui.small_button(surf, self.start, "SAVE" if self.on_cancel else "START", hover)
        ui.text(surf, "TAB SWITCHES - UP TO 12 LETTERS", (cx, 239), GREY, 1, None, "midtop")


class SettingsMenu:
    ROW_H = 12

    def __init__(self, ui, settings, on_change, on_reset, on_close):
        self.ui, self.s = ui, settings
        self.on_change, self.on_reset, self.on_close = on_change, on_reset, on_close
        self.sel = 0
        self.mouse = None
        self.modal = True
        self.rect = pygame.Rect(100, 16, 280, 238)
        self.rows = ["SOUND", "MUSIC", "VOLUME", "FPS", "FULLSCREEN", "TIME OF DAY",
                     "RESET PET", "DESKTOP PET SIZE", "VOICE", "QUIET", "WEATHER", "DESKTOP", "HELP", "OWNER + PET NAMES", "BUY ME A COFFEE", "CLOSE"]

    def _row_rect(self, i):
        return pygame.Rect(self.rect.x + 8, self.rect.y + 28 + i * self.ROW_H, self.rect.w - 16, self.ROW_H)

    def update(self, dt, mouse):
        self.mouse = mouse
        if mouse is not None:
            for i in range(len(self.rows)):
                if self._row_rect(i).collidepoint((int(mouse[0]), int(mouse[1]))):
                    self.sel = i

    def _value(self, i):
        s = self.s
        return [("ON" if s.sound else "OFF"), ("ON" if s.music else "OFF"), "%d%%" % s.volume,
                str(s.fps), ("ON" if s.fullscreen else "OFF"), s.time_mode.upper(), "",
                PET_SIZES[s.pet_scale], "ON" if s.voice else "OFF", "ON" if s.quiet else "OFF",
                s.weather.upper(), "ON" if s.desktop else "OFF", "", ""][i]

    def _adjust(self, i, d):
        s = self.s
        if i == 0:
            s.sound = not s.sound
        elif i == 1:
            s.music = not s.music
        elif i == 2:
            s.volume = max(0, min(100, s.volume + 10 * d))
        elif i == 3:
            s.fps = FPS_OPTIONS[(FPS_OPTIONS.index(s.fps) + d) % len(FPS_OPTIONS)]
        elif i == 4:
            s.fullscreen = not s.fullscreen
        elif i == 5:
            s.time_mode = TIME_MODES[(TIME_MODES.index(s.time_mode) + d) % len(TIME_MODES)]
        elif i == 6:
            self.on_reset()
            return
        elif i == 7:
            sizes = list(PET_SIZES)
            s.pet_scale = sizes[(sizes.index(s.pet_scale) + d) % len(sizes)]
        elif i == 8:
            s.voice = not s.voice
        elif i == 9:
            s.quiet = not s.quiet
        elif i == 10:
            modes = ("auto", "clear", "rain", "snow")
            s.weather = modes[(modes.index(s.weather) + d) % 4]
        elif i == 11:
            s.desktop = not s.desktop
        elif i == 12:
            if hasattr(self, "on_help"): self.on_help()
            return
        elif i == 13:
            if hasattr(self, "on_profile"): self.on_profile()
            return
        elif i == 14:
            import webbrowser
            webbrowser.open('https://buymeacoffee.com/tejapriyan')
            self.ui.toast('OPTIONAL SUPPORT - EVERYTHING IS FREE')
            return
        else:
            self.on_close()
            return
        self.on_change()

    def on_key(self, ev):
        k = ev.key
        n = len(self.rows)
        if k == pygame.K_ESCAPE:
            self.on_close()
        elif k == pygame.K_UP:
            self.sel = (self.sel - 1) % n
        elif k == pygame.K_DOWN:
            self.sel = (self.sel + 1) % n
        elif k == pygame.K_LEFT:
            if self.sel < 6 or 7 <= self.sel <= 11:
                self._adjust(self.sel, -1)
        elif k in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._adjust(self.sel, 1)

    def on_click(self, pos):
        p = (int(pos[0]), int(pos[1]))
        for i in range(len(self.rows)):
            r = self._row_rect(i)
            if r.collidepoint(p):
                self.sel = i
                if i == 2:                               # click on the slider sets the value
                    bar_x = r.right - 74
                    self.s.volume = max(0, min(100, int(round((p[0] - bar_x) / 70.0 * 10)) * 10))
                    self.on_change()
                else:
                    self._adjust(i, 1)
                return
        if not self.rect.collidepoint(p):
            self.on_close()

    def draw(self, surf):
        ui = self.ui
        surf.blit(ui.dim, (0, 0))
        ui.draw_panel(surf, self.rect)
        ui.text(surf, "SETTINGS", (self.rect.centerx, self.rect.y + 9), (150, 90, 200), 2, WHITE, "midtop")
        for i, label in enumerate(self.rows):
            r = self._row_rect(i)
            if i == self.sel:
                surf.fill(CREAM_DK, r)
                surf.fill(PINK, (r.x, r.y, 2, r.h))
            col = RED if label == "RESET PET" else INK
            ui.text(surf, label, (r.x + 8, r.y + 4), col)
            if i == 2:
                bx = r.right - 74
                surf.fill(INK, (bx, r.y + 3, 71, 9))
                for k in range(10):
                    c = C_HAPPY if k < self.s.volume // 10 else BAR_BG
                    surf.fill(c, (bx + 1 + k * 7, r.y + 4, 6, 7))
            elif i < 6 or 7 <= i <= 11:
                ui.text(surf, self._value(i), (r.right - 6, r.y + 4), (150, 90, 200), 1, None, "topright")
        ui.text(surf, "ARROWS + ENTER   ESC CLOSES", (self.rect.centerx, self.rect.bottom - 14),
                GREY, 1, None, "midtop")


class ConfirmDialog:
    def __init__(self, ui, lines, on_yes, on_no):
        self.ui, self.lines, self.on_yes, self.on_no = ui, lines, on_yes, on_no
        self.modal = True
        self.mouse = None
        self.rect = pygame.Rect(130, 88, 220, 90)
        self.yes = pygame.Rect(150, 150, 64, 20)
        self.no = pygame.Rect(266, 150, 64, 20)

    def update(self, dt, mouse):
        self.mouse = mouse

    def on_key(self, ev):
        if ev.key in (pygame.K_y, pygame.K_RETURN):
            self.on_yes()
        elif ev.key in (pygame.K_n, pygame.K_ESCAPE):
            self.on_no()

    def on_click(self, pos):
        p = (int(pos[0]), int(pos[1]))
        if self.yes.collidepoint(p):
            self.on_yes()
        elif self.no.collidepoint(p):
            self.on_no()

    def draw(self, surf):
        ui = self.ui
        surf.blit(ui.dim, (0, 0))
        ui.draw_panel(surf, self.rect)
        for i, line in enumerate(self.lines):
            ui.text(surf, line, (self.rect.centerx, self.rect.y + 12 + i * 12), INK, 1, None, "midtop")
        m = self.mouse
        p_mouse = (int(m[0]), int(m[1])) if m is not None else (-1, -1)
        y_hov = self.yes.collidepoint(p_mouse)
        n_hov = self.no.collidepoint(p_mouse)
        ui.small_button(surf, self.yes, "YES (Y)", y_hov)
        ui.small_button(surf, self.no, "NO (N)", n_hov)


class ShopMenu:
    def __init__(self, ui, pet, on_buy, on_close):
        self.ui, self.pet, self.on_buy, self.on_close = ui, pet, on_buy, on_close
        self.modal = True
        self.mouse = None
        self.sel = 0
        self.rect = pygame.Rect(90, 24, 300, 222)
        self.keys = list(SHOP_ITEMS)

    def _row(self, i):
        return pygame.Rect(self.rect.x + 8, self.rect.y + 28 + i * 35, self.rect.w - 16, 32)

    def update(self, dt, mouse):
        self.mouse = mouse
        if mouse is not None:
            for i in range(len(self.keys)):
                if self._row(i).collidepoint((int(mouse[0]), int(mouse[1]))):
                    self.sel = i

    def on_key(self, ev):
        if ev.key in (pygame.K_ESCAPE, pygame.K_b):
            self.on_close()
        elif ev.key == pygame.K_UP:
            self.sel = (self.sel - 1) % len(self.keys)
        elif ev.key == pygame.K_DOWN:
            self.sel = (self.sel + 1) % len(self.keys)
        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.on_buy(self.keys[self.sel])

    def on_click(self, pos):
        p = (int(pos[0]), int(pos[1]))
        for i, k in enumerate(self.keys):
            if self._row(i).collidepoint(p):
                self.sel = i
                self.on_buy(k)
                return
        if not self.rect.collidepoint(p):
            self.on_close()

    def draw(self, surf):
        ui = self.ui
        surf.blit(ui.dim, (0, 0))
        ui.draw_panel(surf, self.rect)
        ui.text(surf, "SHOP", (self.rect.x + 12, self.rect.y + 8), (150, 90, 200), 2, WHITE)
        coins = str(self.pet.coins)
        cw = ui.font.width(coins)
        surf.blit(ui.assets.icons["coin"], (self.rect.right - cw - 24, self.rect.y + 8))
        ui.text(surf, coins, (self.rect.right - cw - 10, self.rect.y + 9), (170, 110, 20))
        for i, k in enumerate(self.keys):
            item = SHOP_ITEMS[k]
            r = self._row(i)
            if i == self.sel:
                surf.fill(CREAM_DK, r)
                surf.fill(PINK, (r.x, r.y, 2, r.h))
            owned = self.pet.inventory.get(k, 0)
            ui.text(surf, item["name"], (r.x + 8, r.y + 4), INK)
            ui.text(surf, item["desc"], (r.x + 8, r.y + 17), GREY)
            if not item.get("repeatable", True) and owned > 0:
                tag, col = "OWNED", C_ENERGY
            else:
                tag = "%d" % item["price"]
                col = (170, 110, 20) if self.pet.coins >= item["price"] else RED
                surf.blit(ui.assets.icons["coin"], (r.right - ui.font.width(tag) - 22, r.y + 5))
            ui.text(surf, tag, (r.right - 8, r.y + 5), col, 1, None, "topright")
            if item.get("repeatable", True) and owned > 0:
                ui.text(surf, "HAVE %d" % owned, (r.right - 8, r.y + 17), GREY, 1, None, "topright")
        ui.text(surf, "CLICK TO BUY   ESC CLOSES", (self.rect.centerx, self.rect.bottom - 13),
                GREY, 1, None, "midtop")


class StatsAndAwardsMenu:
    def __init__(self, ui, pet, on_close):
        self.ui, self.pet, self.on_close = ui, pet, on_close
        self.modal = True
        self.mouse = None
        self.tab = "stats"   # "stats" or "awards"
        self.rect = pygame.Rect(75, 22, 330, 226)
        self.stats_tab_btn = pygame.Rect(self.rect.x + 12, self.rect.y + 26, 75, 16)
        self.awards_tab_btn = pygame.Rect(self.rect.x + 92, self.rect.y + 26, 120, 16)
        self.award_page = 0
        self.keys = list(ACHIEVEMENTS.keys())
        self.prev_btn = pygame.Rect(self.rect.x + 16, self.rect.bottom - 22, 50, 14)
        self.next_btn = pygame.Rect(self.rect.right - 66, self.rect.bottom - 22, 50, 14)

    def update(self, dt, mouse):
        self.mouse = mouse

    def on_key(self, ev):
        if ev.key in (pygame.K_ESCAPE, pygame.K_t):
            self.on_close()
        elif ev.key in (pygame.K_TAB, pygame.K_1, pygame.K_2, pygame.K_LEFT, pygame.K_RIGHT):
            self.tab = "awards" if self.tab == "stats" else "stats"
        elif self.tab == "awards":
            max_page = (len(self.keys) - 1) // 4
            if ev.key == pygame.K_UP:
                self.award_page = max(0, self.award_page - 1)
            elif ev.key == pygame.K_DOWN:
                self.award_page = min(max_page, self.award_page + 1)

    def on_click(self, pos):
        p = (int(pos[0]), int(pos[1]))
        if self.stats_tab_btn.collidepoint(p):
            self.tab = "stats"
            return
        elif self.awards_tab_btn.collidepoint(p):
            self.tab = "awards"
            return
        if self.tab == "awards":
            max_page = (len(self.keys) - 1) // 4
            if self.prev_btn.collidepoint(p):
                self.award_page = max(0, self.award_page - 1)
                return
            elif self.next_btn.collidepoint(p):
                self.award_page = min(max_page, self.award_page + 1)
                return
        if not self.rect.collidepoint(p):
            self.on_close()

    def draw(self, surf):
        ui = self.ui
        pet = self.pet
        surf.blit(ui.dim, (0, 0))
        ui.draw_panel(surf, self.rect)
        r = self.rect

        # Title
        ui.text(surf, "PET JOURNAL", (r.x + 14, r.y + 8), (150, 90, 200), 2, WHITE)
        coins = str(pet.coins)
        cw = ui.font.width(coins)
        surf.blit(ui.assets.icons["coin"], (r.right - cw - 24, r.y + 8))
        ui.text(surf, coins, (r.right - cw - 10, r.y + 9), (170, 110, 20))

        # Tabs
        m = self.mouse
        p_mouse = (int(m[0]), int(m[1])) if m else (-1, -1)
        s_hov = self.stats_tab_btn.collidepoint(p_mouse)
        a_hov = self.awards_tab_btn.collidepoint(p_mouse)

        ui.small_button(surf, self.stats_tab_btn, "STATS", s_hov, pressed=(self.tab == "stats"))
        ui.small_button(surf, self.awards_tab_btn, "AWARDS (%d/%d)" % (len(pet.achievements), len(ACHIEVEMENTS)),
                        a_hov, pressed=(self.tab == "awards"))

        if self.tab == "stats":
            self._draw_stats(surf)
        else:
            self._draw_awards(surf)

        ui.text(surf, "TAB SWITCHES   ESC CLOSES", (r.centerx, r.bottom - 13), GREY, 1, None, "midtop")

    def _draw_stats(self, surf):
        ui = self.ui
        pet = self.pet
        r = self.rect
        st = pet.stats
        content_rect = pygame.Rect(r.x + 12, r.y + 46, r.w - 24, 148)
        surf.fill(CREAM_DK, content_rect)

        # Left Column - Activity Stats
        x1 = content_rect.x + 8
        y = content_rect.y + 8
        mins = int(st.get("time_played", 0.0) // 60)
        secs = int(st.get("time_played", 0.0) % 60)
        ui.text(surf, "PLAY TIME: %dm %02ds" % (mins, secs), (x1, y), INK)
        y += 15
        ui.text(surf, "TOTAL FEEDS: %d" % st.get("total_feeds", 0), (x1, y), INK)
        y += 15
        ui.text(surf, "TOTAL PLAYS: %d" % st.get("total_plays", 0), (x1, y), INK)
        y += 15
        ui.text(surf, "TOTAL PETTINGS: %d" % st.get("total_pettings", 0), (x1, y), INK)
        y += 15
        ui.text(surf, "TOTAL SLEEPS: %d" % st.get("total_sleeps", 0), (x1, y), INK)
        y += 15
        dist = int(st.get("distance_walked", 0.0))
        ui.text(surf, "EXPLORED: %d px" % dist, (x1, y), INK)
        y += 15
        ui.text(surf, "BUG GAME BEST: %d pts" % st.get("high_score", 0), (x1, y), (170, 110, 20))
        y += 15
        ui.text(surf, "TREAT BEST: %d pts" % st.get("treat_high_score", 0), (x1, y), (170, 110, 20))

        # Right Column - Personality Profile
        x2 = content_rect.centerx + 6
        y2 = content_rect.y + 8
        ui.text(surf, "PERSONALITY:", (x2, y2), (150, 90, 200))
        y2 += 16
        for trait, val in pet.personality.items():
            ui.text(surf, trait.upper(), (x2, y2), INK)
            bx = x2 + 74
            surf.fill(INK, (bx, y2 + 1, 52, 6))
            surf.fill(BAR_BG, (bx + 1, y2 + 2, 50, 4))
            bar_w = int(50 * max(0.0, min(1.0, val)))
            surf.fill(C_XP, (bx + 1, y2 + 2, bar_w, 4))
            y2 += 15

    def _draw_awards(self, surf):
        ui = self.ui
        pet = self.pet
        r = self.rect
        content_rect = pygame.Rect(r.x + 12, r.y + 46, r.w - 24, 148)
        surf.fill(CREAM_DK, content_rect)

        page_size = 4
        start = self.award_page * page_size
        items = self.keys[start:start + page_size]

        for i, k in enumerate(items):
            ach = ACHIEVEMENTS[k]
            unlocked = k in pet.achievements
            row_r = pygame.Rect(content_rect.x + 4, content_rect.y + 4 + i * 35, content_rect.w - 8, 31)
            if unlocked:
                surf.fill((240, 252, 240), row_r)
                surf.fill(C_ENERGY, (row_r.x, row_r.y, 2, row_r.h))
            else:
                surf.fill((245, 238, 232), row_r)

            # Icon
            ic = ui.assets.icons.get(ach.get("icon", "star"))
            if ic:
                surf.blit(ic, (row_r.x + 6, row_r.y + 7))

            ui.text(surf, ach["title"], (row_r.x + 22, row_r.y + 4), INK if unlocked else GREY)
            ui.text(surf, ach["desc"], (row_r.x + 22, row_r.y + 17), GREY)

            status_str = "UNLOCKED" if unlocked else "+%d COINS" % ach["reward"]
            status_col = C_ENERGY if unlocked else (170, 110, 20)
            ui.text(surf, status_str, (row_r.right - 6, row_r.y + 9), status_col, 1, None, "topright")

        # Page nav
        max_page = (len(self.keys) - 1) // page_size
        m = self.mouse
        p_mouse = (int(m[0]), int(m[1])) if m else (-1, -1)
        if self.award_page > 0:
            ui.small_button(surf, self.prev_btn, "PREV", self.prev_btn.collidepoint(p_mouse))
        if self.award_page < max_page:
            ui.small_button(surf, self.next_btn, "NEXT", self.next_btn.collidepoint(p_mouse))
        page_str = "%d / %d" % (self.award_page + 1, max_page + 1)
        ui.text(surf, page_str, (content_rect.centerx, self.rect.bottom - 22), GREY, 1, None, "midtop")


class Fade:
    """Full-screen fade out -> callback -> fade in, for smooth scene changes."""

    def __init__(self):
        self.phase, self.t, self.dur, self.cb = None, 0.0, 0.35, None
        self.surf = pygame.Surface((W, H), pygame.SRCALPHA)

    def start(self, callback, dur=0.35):
        self.phase, self.t, self.dur, self.cb = "out", 0.0, dur, callback

    def fade_in(self, dur=0.35):
        self.phase, self.t, self.dur, self.cb = "in", 0.0, dur, None

    @property
    def busy(self):
        return self.phase is not None

    def update(self, dt):
        if not self.phase:
            return
        self.t += dt
        if self.t >= self.dur:
            if self.phase == "out":
                if self.cb:
                    self.cb()
                self.phase, self.t = "in", 0.0
            else:
                self.phase = None

    def draw(self, surf):
        if not self.phase:
            return
        f = min(1.0, self.t / self.dur)
        a = f if self.phase == "out" else 1.0 - f
        self.surf.fill((20, 10, 36, int(255 * a)))
        surf.blit(self.surf, (0, 0))
