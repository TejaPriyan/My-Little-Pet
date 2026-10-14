"""Windows colour-key desktop companion. Transparent pixels pass clicks through.

Only this application's own HWND is changed. No global hooks or input capture.
Win32 reference: https://learn.microsoft.com/windows/win32/winmsg/window-features
"""
import ctypes
from ctypes import wintypes
import math
import os
import random

import pygame
from config import DESKTOP_KEY, GOLD, INK, WAKE_ENERGY


class DesktopWindow:
    def __init__(self, scale):
        if os.name != "nt":
            raise OSError("Desktop mode is available on Windows.")
        self.scale = scale
        self.api = ctypes.WinDLL("user32", use_last_error=True)
        self.api.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        self.api.GetWindowLongW.restype = wintypes.LONG
        self.api.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
        self.api.SetWindowLongW.restype = wintypes.LONG
        self.api.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.DWORD, wintypes.BYTE, wintypes.DWORD]
        self.api.SetLayeredWindowAttributes.restype = wintypes.BOOL
        self.api.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        self.api.SetWindowPos.restype = wintypes.BOOL
        self.api.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        self.api.GetCursorPos.restype = wintypes.BOOL
        self.api.SetCapture.argtypes = [wintypes.HWND]
        self.api.SetCapture.restype = wintypes.HWND
        self.api.ReleaseCapture.argtypes = []
        self.api.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
        area = wintypes.RECT()
        if not self.api.SystemParametersInfoW(0x30, 0, ctypes.byref(area), 0):
            raise ctypes.WinError(ctypes.get_last_error())
        self.origin = area.left, area.top
        self.size = area.right - area.left, area.bottom - area.top
        self.surface = pygame.display.set_mode(self.size, pygame.NOFRAME)
        pygame.display.set_caption("TEJA PET - Desktop")
        self.hwnd = pygame.display.get_wm_info()["window"]
        style = self.api.GetWindowLongW(self.hwnd, -20)
        ctypes.set_last_error(0)
        self.api.SetWindowLongW(self.hwnd, -20, style | 0x80000)  # WS_EX_LAYERED
        if ctypes.get_last_error():
            raise ctypes.WinError(ctypes.get_last_error())
        key = DESKTOP_KEY[0] | DESKTOP_KEY[1] << 8 | DESKTOP_KEY[2] << 16
        if not self.api.SetLayeredWindowAttributes(self.hwnd, key, 255, 1):
            raise ctypes.WinError(ctypes.get_last_error())
        if not self.api.SetWindowPos(self.hwnd, -1, *self.origin, *self.size, 0x10 | 0x40):
            raise ctypes.WinError(ctypes.get_last_error())
        self.canvas = pygame.Surface((self.size[0] // scale, self.size[1] // scale))
        self.surface.fill(DESKTOP_KEY)
        pygame.display.flip()

    def mouse(self):
        point = wintypes.POINT()
        if self.api.GetCursorPos(ctypes.byref(point)):
            return ((point.x - self.origin[0]) / self.scale, (point.y - self.origin[1]) / self.scale)
        return pygame.mouse.get_pos()[0] / self.scale, pygame.mouse.get_pos()[1] / self.scale

    def present(self):
        self.surface.fill(DESKTOP_KEY)
        self.surface.blit(pygame.transform.scale(self.canvas, (self.canvas.get_width() * self.scale,
                                                              self.canvas.get_height() * self.scale)), (0, 0))
        pygame.display.flip()

    def capture(self, on):
        if on: self.api.SetCapture(self.hwnd)
        else: self.api.ReleaseCapture()

    def close(self):
        # Remove topmost/layering before SDL restores the ordinary room window.
        style = self.api.GetWindowLongW(self.hwnd, -20)
        self.api.SetWindowLongW(self.hwnd, -20, style & ~0x80000)
        self.api.SetWindowPos(self.hwnd, -2, 0, 0, 0, 0, 0x01 | 0x02 | 0x10)


class DesktopPet:
    def __init__(self, game, window):
        self.game, self.window = game, window
        self.pet = game.pet
        self.room_pos = (self.pet.x, self.pet.y)
        self.w, self.h = window.canvas.get_size()
        self.pet.x, self.pet.y = self.w * .6, self.h - 28
        self.pet.z = 0
        self.pet.on_bed = self.pet.hidden = False
        self.pet.anim.play("idle")
        self.home = pygame.Rect(12, self.h - 58, 52, 48)
        self.food = pygame.Rect(80, self.h - 26, 16, 16)
        self.water = pygame.Rect(105, self.h - 26, 16, 16)
        self.ball = pygame.Rect(135, self.h - 26, 14, 14)
        self.room_button = pygame.Rect(12, self.h - 77, 92, 15)
        self.menu = None
        self.rows = ["PET", "FEED", "PLAY", "HOME / SLEEP", "FOLLOW", "QUIET", "ROOM", "QUIT"]
        self.target = None
        self.after = None
        self.state = "idle"
        self.timer = 4.0
        self.drag_start = None
        self.dragged = False
        self.last_pet = -10.0
        self.clock = 0.0
        self.last_beg = -30.0
        self.sleep_time = 0.0
        self.follow = False
        self.explore_distance = 0.0
        self.pet.say("HI " + self.pet.owner_name.upper() + "!", 4)

    def clamp(self, point):
        return max(14, min(self.w - 14, point[0])), max(32, min(self.h - 8, point[1]))

    def wake(self):
        self.pet.hidden = self.pet.carried = False
        self.state = "idle"
        self.timer = 3

    def walk(self, point, after=None):
        self.wake()
        self.target = self.clamp(point)
        self.after = after
        self.state = "walk"

    def reward(self, kind):
        levels = self.pet.gain(kind)
        if levels:
            self.game._on_event("levelup", level=self.pet.level)
        self.game.check_achievements()
        self.game.save_now()

    def command(self, action):
        p, g = self.pet, self.game
        if action in ("home", "sleep"):
            self.follow = False
            self.walk((self.home.centerx, self.home.bottom - 5), "sleep")
        elif action == "feed":
            if p.hunger >= 98:
                p.say("I'M FULL!")
            else:
                self.walk((self.food.centerx, self.food.y), "eat")
        elif action == "drink":
            self.walk((self.water.centerx, self.water.y), "drink")
        elif action == "play":
            if p.energy < 12:
                p.say("TIME FOR A NAP!")
            else:
                self.walk((self.ball.centerx, self.ball.y), "play")
        elif action == "pet":
            if self.clock - self.last_pet < 1.5:
                return
            self.last_pet = self.clock
            p.happiness = min(100, p.happiness + 4)
            p.stats["total_pettings"] += 1
            p.say("I LIKE YOU!")
            g.voice("purr" if p.species == "cat" else p.voice)
            self.reward("pet")
        elif action == "follow":
            self.follow = not self.follow
            self.wake()
            p.say("LET'S GO!" if self.follow else "I'LL STAY HERE")
        elif action == "quiet":
            g.settings.quiet = not g.settings.quiet
            g.audio.apply_settings()
            g.settings.save()
            p.say("QUIET TIME" if g.settings.quiet else "SOUND IS BACK")
        elif action == "room":
            g.leave_desktop()
        elif action == "quit":
            g.running = False

    def event(self, ev):
        pos = self.window.mouse()
        if hasattr(ev, "pos"):
            scale = getattr(self.window, "scale", 1)
            pos = (ev.pos[0] / scale, ev.pos[1] / scale)
        if ev.type == pygame.QUIT:
            self.game.running = False
        elif ev.type == getattr(pygame, "WINDOWFOCUSLOST", -1):
            self.drag_start = None
            self.pet.carried = False
            if hasattr(self.window, "capture"): self.window.capture(False)
        elif ev.type == pygame.KEYDOWN:
            mapping = {pygame.K_ESCAPE: "room", pygame.K_d: "room", pygame.K_h: "home",
                       pygame.K_s: "sleep", pygame.K_f: "feed", pygame.K_p: "play",
                       pygame.K_e: "pet", pygame.K_c: "follow", pygame.K_q: "quiet"}
            if ev.key in mapping:
                self.command(mapping[ev.key])
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 3:
                self.menu = pygame.Rect(min(max(0, int(pos[0])), self.w - 124),
                                        min(max(0, int(pos[1])), self.h - 151), 124, 151)
            elif ev.button == 1:
                if self.menu:
                    if self.menu.collidepoint(pos):
                        i = int((pos[1] - self.menu.y - 5) // 18)
                        if 0 <= i < len(self.rows):
                            self.command(("pet", "feed", "play", "home", "follow", "quiet", "room", "quit")[i])
                    elif self.pet.rect().inflate(6, 6).collidepoint(pos) and not self.pet.hidden:
                        self.drag_start = pos
                        self.dragged = False
                        self.wake()
                        self.target = None
                        if hasattr(self.window, "capture"): self.window.capture(True)
                    self.menu = None
                elif self.room_button.collidepoint(pos):
                    self.command("room")
                elif self.pet.rect().inflate(6, 6).collidepoint(pos) and not self.pet.hidden:
                    self.drag_start = pos
                    self.dragged = False
                    self.wake()
                    self.target = None
                    if hasattr(self.window, "capture"): self.window.capture(True)
                elif self.home.collidepoint(pos):
                    if self.pet.hidden:
                        self.wake()
                        self.pet.say("GOOD MORNING!")
                    else:
                        self.command("home")
                else:
                    for rect, key in ((self.food, "feed"), (self.water, "drink"), (self.ball, "play")):
                        if rect.collidepoint(pos):
                            self.command(key)
                            break
        elif ev.type == pygame.MOUSEMOTION and self.drag_start:
            if math.dist(pos, self.drag_start) > 2:
                self.dragged = True
                self.pet.carried = True
                self.pet.x, self.pet.y = self.clamp((pos[0], pos[1] + 12))
                self.pet.anim.play("dangle")
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.drag_start:
            if hasattr(self.window, "capture"): self.window.capture(False)
            if math.dist(pos, self.drag_start) > 2:
                self.dragged = True
                self.pet.x, self.pet.y = self.clamp((pos[0], pos[1] + 12))
            self.drag_start = None
            self.pet.carried = False
            if self.dragged:
                if self.home.collidepoint(pos):
                    self.command("home")
                else:
                    self.pet.say("WHEEE!")
                    self.timer = 3
            else:
                self.command("pet")

    def update(self, dt):
        p, g = self.pet, self.game
        self.clock += dt
        pos = self.window.mouse()
        # Keep the companion still while the user chooses from its menu.
        if self.menu:
            p.update(dt)
            return
        activity = "idle"
        if self.drag_start:
            if math.dist(pos, self.drag_start) > 2:
                self.dragged = True
            if self.dragged:
                p.x, p.y = self.clamp((pos[0], pos[1] + 12))
                p.carried = True
                p.anim.play("dangle")
        else:
            keys = pygame.key.get_pressed()
            dx = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            dy = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
            if (dx or dy) and not self.menu:
                self.wake()
                self.target = self.clamp((p.x + dx * 60, p.y + dy * 60))
                self.after = None
                self.state = "walk"
            elif self.follow and not self.menu and math.dist((p.x, p.y), pos) > 22:
                self.walk(pos)
            if self.state == "walk" and self.target:
                dx, dy = self.target[0] - p.x, self.target[1] - p.y
                distance = math.hypot(dx, dy)
                speed = 78 if p.zoomies > 0 or pygame.key.get_mods() & pygame.KMOD_SHIFT else 36
                step = min(distance, speed * dt)
                if distance > 1:
                    p.x += dx / distance * step
                    p.y += dy / distance * step
                    p.face_vector(dx, dy)
                    p.anim.play("walk_" + p.facing)
                    activity = "run" if speed == 78 else "walk"
                    p.stats["distance_walked"] += step
                    self.explore_distance += step
                    if self.explore_distance >= 600:
                        self.explore_distance -= 600
                        self.reward("explore")
                else:
                    self.state = self.after or "idle"
                    self.target = None
                    self.timer = 3.0
                    self.sleep_time = 0
            elif self.state == "sleep":
                activity = "sleep"
                p.hidden = True
                p.anim.play("sleep")
                self.sleep_time += dt
                if self.sleep_time >= 5 and p.energy >= WAKE_ENERGY:
                    p.stats["total_sleeps"] += 1
                    self.reward("sleep")
                    self.wake()
                    p.say("ALL RESTED!")
            elif self.state in ("eat", "drink", "play"):
                p.anim.play("play" if self.state == "play" else "eat")
                self.timer -= dt
                if self.timer <= 0:
                    if self.state == "eat":
                        bonus = 15 if p.inventory.get("treat", 0) else 0
                        if bonus:
                            p.inventory["treat"] -= 1
                        p.hunger = min(100, p.hunger + 20 + bonus)
                        p.happiness = min(100, p.happiness + 5)
                        p.stats["total_feeds"] += 1
                        g.daily_event("feed")
                        self.reward("feed")
                        g.audio.play("eat")
                    elif self.state == "play":
                        p.happiness = min(100, p.happiness + 20 + (5 if p.inventory.get("squeaky") else 0))
                        p.energy = max(0, p.energy - 10)
                        p.stats["total_plays"] += 1
                        g.daily_event("play")
                        self.reward("play")
                        g.voice()
                    else:
                        p.stats["total_drinks"] += 1
                        p.happiness = min(100, p.happiness + 2)
                    self.wake()
            else:
                p.anim.play("sit" if p.energy < 40 else "idle")
                self.timer -= dt
                if not self.menu and self.timer <= 0:
                    if p.energy < 22:
                        self.command("home")
                    elif p.hunger < 28 and self.clock - self.last_beg > 30:
                        self.last_beg = self.clock
                        p.say("FEED ME?")
                        self.walk((self.food.centerx, self.food.y))
                    elif not self.follow:
                        self.walk((random.uniform(20, self.w - 20), random.uniform(max(40, self.h * .6), self.h - 12)))
                        self.timer = random.uniform(4, 9)
        p.update(dt)
        p.tick_needs(dt, activity, g.daynight.darkness > .6)

    def draw(self):
        c, g, p = self.window.canvas, self.game, self.pet
        c.fill(DESKTOP_KEY)
        c.blit(pygame.transform.scale(g.assets.house, self.home.size), self.home)
        c.blit(g.assets.food[0 if p.hunger > 40 else -1], self.food)
        c.blit(g.assets.water[0], self.water)
        c.blit(g.assets.toy, self.ball)
        g.ui.small_button(c, self.room_button, "ROOM (ESC)", self.room_button.collidepoint(self.window.mouse()))
        p.draw(c, g.assets)
        if p.hidden:
            g.ui.text(c, "ZZZ", (self.home.centerx - 8, self.home.y - 8), GOLD)
        if p.bubble_t > 0 and not p.hidden and not g.settings.quiet:
            text = p.bubble_text
            width = g.font.width(text) + 10
            rect = pygame.Rect(max(1, min(self.w - width - 1, int(p.x) - width // 2)), max(2, int(p.y) - 47), width, 15)
            g.ui.draw_panel(c, rect)
            g.ui.text(c, text, (rect.x + 5, rect.y + 4), INK)
        if self.menu:
            g.ui.draw_panel(c, self.menu)
            for i, label in enumerate(self.rows):
                if label == "FOLLOW": label += " ON" if self.follow else " OFF"
                if label == "QUIET": label += " ON" if g.settings.quiet else " OFF"
                r = pygame.Rect(self.menu.x + 4, self.menu.y + 5 + i * 18, self.menu.w - 8, 17)
                g.ui.small_button(c, r, label, r.collidepoint(self.window.mouse()))
        self.window.present()

    def restore(self):
        self.pet.x, self.pet.y = self.room_pos
        self.pet.hidden = self.pet.carried = self.pet.on_bed = False
        self.pet.z = 0
        self.window.close()
