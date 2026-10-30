"""The pet is the player: fetching and jumping, with free spectator practice."""
import math
import pygame
from minigame import BugCatchGame
from pet import Animator
from config import INK, GOLD


class PetGame(BugCatchGame):
    TOTAL_TIME = 45.0
    TITLE = "FETCH RELAY"
    SCORE_KEY = "fetch_high_score"
    KIND = "fetch"

    def __init__(self, ui, pet, audio, fx, on_finish, watch=False):
        super().__init__(ui, pet, audio, fx, on_finish, practice=watch)
        self.watch = watch
        self.actor = Animator(pet.anim.clips)
        self.actor.play("idle")
        self.x, self.y = 90., 176.
        self.phase = "ready"
        self.target = (300., 170.)
        self.jump = 0.
        self.obstacle = 440.
        self.obstacle_scored = False
        self.elapsed = 0.
        self.cheer = 0.
        self.spectators = []
        self.info = "CLICK THE GRASS TO THROW. YOUR PET BRINGS IT BACK."
        if self.KIND == "hurdles": self.info = "CLICK / SPACE TO JUMP OVER SOFT GARDEN HURDLES."

    def throw(self, point):
        if self.phase != "ready": return False
        x, y = point
        if not 185 <= x <= 420 or not 104 <= y <= 198: return False
        self.target = (float(x), float(y))
        self.phase = "out"
        self.info = "FETCH! WAIT FOR YOUR LITTLE FRIEND TO RETURN."
        return True

    def leap(self):
        if self.jump <= 0:
            self.jump = .85
            return True
        return False

    def on_click(self, pos):
        if self.state != "playing": return super().on_click(pos)
        if self.watch: return
        if self.KIND == "fetch": self.throw(pos)
        else: self.leap()

    def on_key(self, ev):
        if ev.key == pygame.K_SPACE and self.state == "playing" and not self.watch:
            if self.KIND == "hurdles": self.leap()
            else: self.throw((300, 170))
        else: super().on_key(ev)

    def update(self, dt, mouse):
        self.mouse = mouse
        if self.state != "playing": return
        dt = min(.1, max(0, dt))
        self.time_left = max(0, self.time_left - dt)
        self.elapsed += dt
        self.cheer = max(0, self.cheer - dt)
        if self.KIND == "fetch":
            if self.watch and self.phase == "ready": self.throw((self.rng.uniform(220, 410), self.rng.uniform(115, 190)))
            if self.phase != "ready":
                tx, ty = self.target if self.phase == "out" else (90, 176)
                dx, dy = tx - self.x, ty - self.y
                distance = math.hypot(dx, dy)
                step = min(distance, dt * 110)
                if distance > 1:
                    self.x += dx / distance * step; self.y += dy / distance * step
                    self.actor.play("walk_right" if dx >= 0 else "walk_left")
                elif self.phase == "out": self.phase = "back"
                else:
                    self.phase = "ready"; self.score += 4; self.cheer = 1
                    self.info = "GOOD FETCH! THROW AGAIN OR PRESS SPACE."
                    self.audio.play("catch", .5)
            else: self.actor.play("happy" if self.cheer else "idle")
        else:
            if self.watch and 140 < self.obstacle < 170 and self.jump <= 0: self.leap()
            self.jump = max(0, self.jump - dt)
            self.obstacle -= (95 + min(35, self.elapsed)) * dt
            height = math.sin(math.pi * (1 - self.jump / .85)) * 53 if self.jump else 0
            if self.obstacle <= self.x + 10 and not self.obstacle_scored:
                self.obstacle_scored = True
                if height >= 24:
                    self.score += 4; self.cheer = 1
                    self.info = "LOVELY LEAP! KEEP GOING."
                    self.audio.play("catch", .5)
                else:
                    self.info = "SOFT LANDING! TRY JUMPING A LITTLE EARLIER."
            if self.obstacle < 35:
                self.obstacle = 440.; self.obstacle_scored = False
            self.actor.play("happy" if self.jump else "walk_right")
        self.actor.update(dt)
        if self.time_left <= 0:
            self.completed = True; self.state = "results"; self._apply_rewards()

    def draw(self, surf):
        if self.state != "playing": return super().draw(surf)
        u = self.ui
        u.draw_panel(surf, (20, 34, 440, 200))
        surf.fill((220, 237, 213), (30, 70, 420, 138))
        for x in range(40, 450, 32):
            pygame.draw.line(surf, (171, 203, 159), (x, 201), (x + 3, 196), 1)
        u.text(surf, self.TITLE, (40, 45), INK, 2)
        u.text(surf, "%d POINTS  %ds" % (self.score, math.ceil(self.time_left)), (440, 49), INK, anchor="topright")
        u.text(surf, self.pet.name.upper() + "'S LITTLE ADVENTURE", (240, 78), INK, anchor="midtop")
        for i, friend in enumerate(self.spectators):
            surf.blit(friend.anim.clips["wave"].frames[int(self.elapsed * 3) % len(friend.anim.clips["wave"].frames)], (315 + i * 34, 96))
        if self.KIND == "fetch":
            pygame.draw.ellipse(surf, (159, 190, 139), (65, 169, 46, 20), 2)
            if self.phase == "out":
                pygame.draw.circle(surf, (222, 123, 128), tuple(map(int, self.target)), 6)
            elif self.phase == "back": pygame.draw.circle(surf, GOLD, (int(self.x) - 8, int(self.y) - 9), 5)
        else:
            pygame.draw.rect(surf, (177, 131, 162), (int(self.obstacle), 155, 12, 22), border_radius=3)
        height = math.sin(math.pi * (1 - self.jump / .85)) * 53 if self.jump else 0
        surf.blit(pygame.transform.scale(self.actor.frame(), (48, 48)), (int(self.x) - 24, int(self.y - height) - 40))
        u.text(surf, self.info, (240, 213), INK, anchor="midtop")
        u.text(surf, "WATCHING - FREE, NO REWARDS" if self.watch else "FREE PRACTICE" if not self.paid_round else "FULL ROUND: UP TO 8 COINS", (240, 239), INK, anchor="midtop")


class GardenHurdles(PetGame):
    TITLE = "GARDEN HURDLES"
    SCORE_KEY = "hurdles_high_score"
    KIND = "hurdles"
