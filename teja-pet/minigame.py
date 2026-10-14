"""Mini-game: Catch the Bug!

A fast, fun mini-game where the player catches fluttering bugs and golden
fireflies to earn coins, pet XP, and happiness.
"""
import math
import random
import pygame

from config import (W, H, HUD_H, BAR_Y, INK, CREAM, CREAM_DK, PINK, GOLD, WHITE,
                    C_ENERGY, C_HAPPY, C_XP)
GREY = (150, 130, 150)


class Bug:
    def __init__(self, rng, is_golden=False):
        self.is_golden = is_golden
        self.size = 6 if is_golden else 5
        self.x = rng.choice([-10.0, float(W + 10)])
        self.y = rng.uniform(HUD_H + 20, BAR_Y - 30)
        self.dir = 1.0 if self.x < 0 else -1.0
        self.speed = rng.uniform(40.0, 75.0) * (1.2 if is_golden else 1.0)
        self.vx = self.dir * self.speed
        self.base_y = self.y
        self.freq = rng.uniform(4.0, 7.0)
        self.amp = rng.uniform(12.0, 24.0)
        self.t = rng.uniform(0.0, 10.0)
        self.wing_t = 0.0
        self.alive = True
        if is_golden:
            self.body_col = GOLD
            self.wing_col = (255, 248, 190)
        else:
            self.body_col = rng.choice([
                (70, 180, 120),   # Green
                (110, 150, 255),  # Sky blue
                (240, 110, 170),  # Pink
                (200, 130, 240),  # Purple
                (255, 150, 70),   # Orange
            ])
            self.wing_col = (240, 245, 255)

    def update(self, dt):
        self.t += dt
        self.wing_t += dt * 24.0
        self.x += self.vx * dt
        self.y = self.base_y + math.sin(self.t * self.freq) * self.amp
        # Wrap or recycle when off-screen
        if self.dir > 0 and self.x > W + 20:
            self.alive = False
        elif self.dir < 0 and self.x < -20:
            self.alive = False

    def hit(self, pt):
        dx = pt[0] - self.x
        dy = pt[1] - self.y
        return (dx * dx + dy * dy) <= (self.size + 6) ** 2

    def draw(self, surf):
        x, y = int(self.x), int(self.y)
        wing_flap = int(math.sin(self.wing_t) * 3)
        # Wings
        surf.fill(self.wing_col, (x - 4, y - 3 + wing_flap, 3, 3))
        surf.fill(self.wing_col, (x + 2, y - 3 - wing_flap, 3, 3))
        # Body
        surf.fill(INK, (x - 2, y - 2, 5, 5))
        surf.fill(self.body_col, (x - 1, y - 1, 3, 3))
        if self.is_golden:
            surf.fill(WHITE, (x, y, 1, 1))


class BugCatchGame:
    TOTAL_TIME = 30.0
    TITLE = "CATCH THE BUG!"
    SCORE_KEY = "high_score"

    def __init__(self, ui, pet, audio, fx, on_finish):
        self.ui, self.pet, self.audio, self.fx = ui, pet, audio, fx
        self.on_finish = on_finish
        self.modal = True
        self.mouse = None
        self.time_left = self.TOTAL_TIME
        self.score = 0
        self.combo = 1
        self.combo_timer = 0.0
        self.gold_caught = 0
        self.bugs = []
        self.state = "playing"        # "playing" or "results"
        self.rng = random.Random()
        self.spawn_timer = 0.0
        self.rewarded = False
        self.levels_gained = 0
        self.panel_rect = pygame.Rect(110, 48, 260, 168)
        self.collect_btn = pygame.Rect(self.panel_rect.centerx - 55, self.panel_rect.bottom - 26, 110, 18)

        # Seed with initial bugs
        for _ in range(4):
            self.bugs.append(Bug(self.rng, is_golden=(self.rng.random() < 0.2)))

    def update(self, dt, mouse):
        self.mouse = mouse
        if self.state == "playing":
            self.time_left = max(0.0, self.time_left - dt)
            if self.combo_timer > 0:
                self.combo_timer -= dt
                if self.combo_timer <= 0:
                    self.combo = 1

            self.spawn_timer += dt
            if self.spawn_timer >= 0.8 and len(self.bugs) < 6:
                self.spawn_timer = 0.0
                is_gold = self.rng.random() < 0.18
                self.bugs.append(Bug(self.rng, is_golden=is_gold))

            for b in self.bugs:
                b.update(dt)
            self.bugs = [b for b in self.bugs if b.alive]

            if self.time_left <= 0:
                self.state = "results"
                self._apply_rewards()

    def on_click(self, pos):
        if self.state == "playing":
            p = (int(pos[0]), int(pos[1]))
            # Check bugs from top to bottom
            for b in reversed(self.bugs):
                if b.alive and b.hit(p):
                    b.alive = False
                    self.combo_timer = 1.6
                    pts = (3 if b.is_golden else 1) * self.combo
                    self.score += pts
                    if b.is_golden:
                        self.gold_caught += 1
                        self.fx.sparkles(b.x, b.y, 8, spread=16)
                        self.fx.text(b.x, b.y - 12, "+%d GOLD!" % pts, GOLD)
                        self.audio.play("award", 0.8)
                    else:
                        self.fx.sparkles(b.x, b.y, 4, spread=8)
                        self.fx.text(b.x, b.y - 10, "+%d" % pts, C_HAPPY)
                        self.audio.play("catch", 0.7)
                    self.combo = min(4, self.combo + 1)
                    break
        elif self.state == "results":
            if self.collect_btn.collidepoint((int(pos[0]), int(pos[1]))):
                self.on_finish()

    def on_key(self, ev):
        if self.state == "playing":
            if ev.key == pygame.K_ESCAPE:
                self.state = "results"
                self._apply_rewards()
        elif self.state == "results":
            if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.on_finish()

    def _apply_rewards(self):
        if self.rewarded:
            return
        self.rewarded = True
        # Calculate rewards based on score
        coins_earned = max(2, self.score // 2) + self.gold_caught * 2
        xp_earned = max(5, self.score * 2)
        happy_boost = 25

        self.pet.coins += coins_earned
        self.levels_gained = self.pet.gain_level_rewards(xp_earned)
        self.pet.happiness = min(100.0, self.pet.happiness + happy_boost)
        self.pet.stats["games_played"] = self.pet.stats.get("games_played", 0) + 1
        self.pet.stats[self.SCORE_KEY] = max(self.pet.stats.get(self.SCORE_KEY, 0), self.score)

        self.coins_earned = coins_earned
        self.xp_earned = xp_earned
        self.audio.play("happy", 0.8)

    def draw(self, surf):
        ui = self.ui
        if self.state == "playing":
            # Draw semi-transparent header bar
            bar_rect = pygame.Rect(40, HUD_H + 4, W - 80, 18)
            ui.draw_panel(surf, bar_rect)
            ui.text(surf, "SCORE: %d" % self.score, (bar_rect.x + 8, bar_rect.y + 5), INK)
            time_str = "TIME: %02ds" % int(math.ceil(self.time_left))
            time_col = PINK if self.time_left <= 5.0 else INK
            ui.text(surf, time_str, (bar_rect.centerx - 24, bar_rect.y + 5), time_col)
            if self.combo > 1:
                ui.text(surf, "COMBO x%d!" % self.combo, (bar_rect.right - 64, bar_rect.y + 5), (230, 90, 140))

            # Draw bugs
            for b in self.bugs:
                b.draw(surf)

        elif self.state == "results":
            surf.blit(ui.dim, (0, 0))
            ui.draw_panel(surf, self.panel_rect)
            r = self.panel_rect
            ui.text(surf, self.TITLE, (r.centerx, r.y + 10), (150, 90, 200), 2, WHITE, "midtop")
            ui.text(surf, "FINAL SCORE: %d" % self.score, (r.centerx, r.y + 36), INK, 1, None, "midtop")
            hi = self.pet.stats.get(self.SCORE_KEY, self.score)
            ui.text(surf, "BEST SCORE: %d" % hi, (r.centerx, r.y + 50), GREY, 1, None, "midtop")

            # Reward summary
            surf.fill(CREAM_DK, (r.x + 16, r.y + 68, r.w - 32, 48))
            ui.text(surf, "REWARDS:", (r.x + 24, r.y + 72), INK)
            cw = ui.font.width("+%d COINS" % self.coins_earned)
            surf.blit(ui.assets.icons["coin"], (r.x + 24, r.y + 86))
            ui.text(surf, "+%d COINS" % self.coins_earned, (r.x + 38, r.y + 87), (170, 110, 20))

            surf.blit(ui.assets.icons["star"], (r.centerx + 8, r.y + 86))
            ui.text(surf, "+%d XP" % self.xp_earned, (r.centerx + 22, r.y + 87), C_XP)

            surf.blit(ui.assets.icons["heart"], (r.x + 24, r.y + 100))
            ui.text(surf, "+25 HAPPINESS", (r.x + 38, r.y + 101), C_HAPPY)

            # Collect button
            hover = self.mouse is not None and self.collect_btn.collidepoint((int(self.mouse[0]), int(self.mouse[1])))
            ui.small_button(surf, self.collect_btn, "COLLECT", hover)


class TreatDropGame(BugCatchGame):
    TITLE = "TREAT DROP!"
    SCORE_KEY = "treat_high_score"

    def __init__(self, *args):
        super().__init__(*args)
        self.drops = []
        self.basket_x = W / 2
        self.spawn_timer = 0.0

    def update(self, dt, mouse):
        self.mouse = mouse
        if self.state != "playing": return
        self.time_left = max(0, self.time_left - dt)
        keys = pygame.key.get_pressed()
        dx = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        if dx: self.basket_x += dx * 220 * dt
        elif mouse is not None: self.basket_x = mouse[0]
        self.basket_x = max(20, min(W - 20, self.basket_x))
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = .40
            kind = self.rng.choice(["fish", "bone", "carrot", "berry", "cookie", "star", "thorn"])
            self.drops.append([self.rng.uniform(25, W - 25), 62.0, self.rng.uniform(65, 105), kind])
        alive = []
        for drop in self.drops:
            drop[1] += drop[2] * dt
            x, y, speed, kind = drop
            if y >= 219 and abs(x - self.basket_x) <= 23:
                if kind == "thorn":
                    self.score = max(0, self.score - 3)
                    self.audio.play("pop")
                else:
                    self.score += 3 if kind == "star" else 1
                    self.audio.play("catch", .5)
            elif y < BAR_Y: alive.append(drop)
        self.drops = alive
        if self.time_left <= 0:
            self.state = "results"
            self._apply_rewards()

    def on_click(self, pos):
        if self.state == "results": super().on_click(pos)
        else: self.basket_x = pos[0]

    def draw(self, surf):
        if self.state == "results":
            super().draw(surf)
            return
        u = self.ui
        u.draw_panel(surf, (20, HUD_H + 3, W - 40, 24))
        u.text(surf, "TREATS %d   TIME %02d   AVOID THORNS!" % (self.score, math.ceil(self.time_left)), (30, HUD_H + 9), INK)
        for x, y, speed, kind in self.drops: surf.blit(u.assets.treats[kind], (int(x) - 6, int(y) - 6))
        x = int(self.basket_x)
        surf.fill(INK, (x - 21, 225, 42, 11))
        surf.fill((220, 155, 95), (x - 19, 227, 38, 7))
        surf.fill(GOLD, (x - 22, 223, 44, 3))
