"""Movable desktop furniture and pets; the house is the room's front door."""
import math
import random
import pygame
from config import DESKTOP_KEY, GOLD, INK, WAKE_ENERGY
from economy import meal
from household import react
from life import record_adventure
from playful import DesktopFun
from settings import PET_SIZES
from desktop_render import DesktopRenderer, pet_rect


from desktop_furniture import DesktopFurniture


class DesktopPet(DesktopFurniture):
    ACTIONS = (("size", "PET SIZE"), ("visibility", "SHOW / HIDE"), ("furniture", "FURNITURE / DECOR"), ("pet", "CUDDLE"), ("feed", "FEED"), ("play", "PLAY"), ("dance", "DANCE"),
               ("follow", "FOLLOW"), ("mouse", "MOUSE VISIT"), ("peek", "HIDE AND SEEK"), ("chase", "CATCH ME"), ("surprises", "SURPRISES"), ("home", "ENTER HOME"), ("sleep", "NAP"),
               ("hide", "HIDE / SHOW HOME"), ("compact", "SMALL / LARGE HOME"),
               ("solo", "SOLO / FAMILY"), ("quiet", "QUIET TIME"), ("games", "PET GAMES"),
               ("family", "ADD PET / FAMILY"), ("toys", "TOY BOX"), ("rescue", "BRING PETS BACK"), ("pause", "PAUSE / RESUME"), ("quit", "QUIT"))

    def __init__(self, game, window):
        self.game, self.window, self.pet = game, window, game.pet
        self.room_pos = (self.pet.x, self.pet.y)
        self.w, self.h = window.canvas.get_size()
        self.pet.x, self.pet.y = self.w * .6, self.h - 28
        self.pet.z = 0
        self.pet.on_bed = self.pet.hidden = self.pet.carried = False
        self.pet.anim.play("idle")
        self.home = pygame.Rect(12, self.h - 58, 52, 48)
        self.food = pygame.Rect(80, self.h - 26, 16, 16)
        self.water = pygame.Rect(105, self.h - 26, 16, 16)
        self.ball = pygame.Rect(135, self.h - 26, 14, 14)
        layout = self.pet.desktop_layout
        self.hidden = layout.get("hidden", False)
        self.compact = layout.get("compact", False)
        if self.compact: self.home.size = (28, 26)
        for key in ("home", "food", "water", "ball"):
            rect = getattr(self, key)
            if key in layout:
                rect.topleft = (int(layout[key][0] * self.w), int(layout[key][1] * self.h))
            self.clamp_rect(rect)
        self.init_furniture(layout)
        self.menu = None
        self.menu_page = 0
        self.target = self.after = None
        self.state, self.timer = "idle", 4.0
        self.drag_start = self.drag_item = None
        self.dragged = False
        self.drag_offset = (0, 0)
        self.clock, self.last_pet, self.last_beg, self.sleep_time = 0.0, -10.0, -30.0, 0.0
        self.follow = False
        self.area_check = 0
        self.explore_distance = 0
        self.fun = DesktopFun(self)
        self.found_click = False
        self.renderer = getattr(window, "renderer", None) or DesktopRenderer()
        game.household.targets.clear()
        game.household.activities.clear()
        for i, friend in enumerate(game.household.friends):
            friend.x, friend.y = self.clamp((self.pet.x + (i + 1) * 32, self.pet.y))
        self.pet.say("DRAG HOME. RIGHT-CLICK ME!", 5)

    def clamp(self, point):
        ratio = self.game.settings.pet_scale / getattr(self.window, "scale", 3)
        margin = 12 * ratio + 2
        return max(margin, min(self.w - margin, point[0])), max(22 * ratio + 6, min(self.h - 4 * ratio, point[1]))

    def pet_rect(self, pet):
        scale = getattr(self.window, "scale", 3)
        rect = pet_rect(pet, scale, self.game.settings.pet_scale)
        return pygame.Rect(math.floor(rect.x / scale), math.floor(rect.y / scale),
                           math.ceil(rect.w / scale), math.ceil(rect.h / scale))

    def clamp_rect(self, rect):
        rect.x = max(0, min(self.w - rect.w, rect.x))
        rect.y = max(16, min(self.h - rect.h, rect.y))

    def controls(self):
        return pygame.Rect(self.home.right - 26, self.home.y - 14, 12, 12), pygame.Rect(self.home.right - 12, self.home.y - 14, 12, 12)

    def controls_visible(self, pos=None):
        if 'home' not in self.visible_props(): return False
        # Include the gap above the roof so the buttons remain reachable.
        area = self.home.unionall(list(self.controls())).inflate(6, 4)
        return area.collidepoint(self.window.mouse() if pos is None else pos)

    def save_layout(self):
        self.pet.desktop_layout = {"hidden": self.hidden, "compact": self.compact,
            "items_hidden": self.items_hidden, "pets_hidden": self.pets_hidden,
            "put_away": sorted(self.put_away),
            "furniture": {k: [r.x / self.w, r.y / self.h] for k, r in self.furniture.items()}}
        for key in ("home", "food", "water", "ball"):
            r = getattr(self, key)
            x, y = self.fun.home if key == 'ball' and self.fun.home else r.topleft
            self.pet.desktop_layout[key] = [x / self.w, y / self.h]
        self.game.save_now()

    def wake(self):
        self.pet.hidden = self.pet.carried = False
        self.pet.z = 0
        self.state, self.timer = "idle", 3

    def walk(self, point, after=None):
        self.wake()
        self.target, self.after = self.clamp(point), after
        self.state = "walk"

    def reward(self, kind):
        if self.pet.gain(kind): self.game._on_event("levelup", level=self.pet.level)
        self.game.check_achievements()
        self.game.save_now()

    def command(self, action):
        p, g = self.pet, self.game
        if action == "size":
            self.open_menu(getattr(self, "menu_origin", self.window.mouse()), "size")
            return
        if action.startswith("size:"):
            try:
                size = int(action.split(":", 1)[1])
            except ValueError:
                return
            if size not in PET_SIZES:
                return
            self.fun.stop()
            self.cancel_drag()
            g.settings.pet_scale = size
            g.settings.save()
            self.target = self.after = None
            for member in [p] + g.household.friends:
                member.x, member.y = self.clamp((member.x, member.y))
            g.household.targets.clear()
            self.menu = None
            p.say(PET_SIZES[size].title() + " paws, same little friend.", 4)
            return
        self.fun.stop()
        self.after = None
        if action in ('mouse', 'peek', 'chase', 'play'):
            g.paused = False
            self.fun.start('toy' if action == 'play' else action)
            return
        if action == 'surprises':
            g.settings.surprises = not g.settings.surprises
            g.settings.save()
            p.say('SURPRISES ON!' if g.settings.surprises else 'JUST A QUIET LITTLE BUDDY!')
            return
        if self.visibility_command(action): return
        if self.furniture_command(action): return
        if action not in ("pause", "quit"): g.paused = False
        if action in ("home", "room"):
            self.pets_hidden = False
            self.hidden = False
            self.put_away.discard("home")
            self.follow = False
            self.walk((self.home.centerx, self.home.bottom - 3), "enter")
            p.say("LET'S GO INSIDE!")
            self.save_layout()
        elif action == "sleep":
            self.follow = False
            if 'bed' in self.furniture:
                bed = self.furniture['bed']
                self.walk((bed.x + 22, bed.y + 25), 'sleep')
            elif 'home' not in self.visible_props():
                self.wake(); self.state = "sleep"
            else: self.walk((self.home.right + 18, self.home.bottom - 3), "sleep")
        elif action in ("feed", "drink", "play"):
            if action == "feed" and p.hunger >= 98: p.say("I'M FULL!"); return
            if action == "play" and p.energy < 12: p.say("TIME FOR A NAP!"); return
            self.follow = False
            target = {"feed": self.food, "drink": self.water, "play": self.ball}[action]
            state = {"feed": "eat", "drink": "drink", "play": "play"}[action]
            if {"feed": "food", "drink": "water", "play": "ball"}[action] not in self.visible_props():
                self.wake(); self.state = state; self.timer = 3
            else: self.walk((target.centerx, target.y), state)
        elif action == "pet":
            if self.clock - self.last_pet < .6: return
            self.last_pet = self.clock
            p.happiness = min(100, p.happiness + 4)
            p.stats["total_pettings"] += 1
            record_adventure(p, "cuddle")
            react(p)
            self.wake(); self.state = "wave"; self.timer = 2
            g.voice("purr" if p.species == "cat" else p.voice)
            self.reward("pet")
        elif action == "dance":
            self.follow = False
            self.wake(); self.state = "dance"; self.timer = 5
            p.say("SHAKE YOUR LITTLE PAWS!")
            g.household.socialize("dance")
            g.voice()
        elif action == "follow":
            self.follow = not self.follow
            self.wake(); self.target = None
            p.say("LET'S GO!" if self.follow else "I'LL STAY HERE")
        elif action == "hide":
            self.hidden = 'home' in self.visible_props()
            if not self.hidden: self.put_away.discard('home')
            if p.hidden: self.wake()
            p.say("PET MENU BRINGS HOME BACK!" if self.hidden else "HOME SWEET HOME!")
            self.save_layout()
        elif action == "compact":
            self.compact = not self.compact
            bottom = self.home.midbottom
            self.home.size = (28, 26) if self.compact else (52, 48)
            self.home.midbottom = bottom
            self.clamp_rect(self.home); self.save_layout()
        elif action == "solo":
            p.solo = not p.solo
            p.say("JUST YOU AND ME!" if p.solo else "EVERYONE COME PLAY!")
            g.save_now()
        elif action == "quiet":
            g.settings.quiet = not g.settings.quiet
            self.follow = False
            self.target = None
            self.wake()
            if g.settings.quiet and not self.hidden:
                self.walk((self.home.right + 20, self.home.bottom), "sit")
            g.audio.apply_settings(); g.settings.save()
        elif action == "family":
            g.leave_desktop(); g.do_action("family")
        elif action == "toys":
            g.leave_desktop(); g.do_action("toys")
        elif action == "games":
            g.leave_desktop(); g.do_action("game")
        elif action == "pause":
            g.paused = not g.paused
            p.say("PAUSED. RIGHT-CLICK TO RESUME." if g.paused else "LET'S PLAY!")
        elif action in ("rescue", "showhome"):
            g.paused = False
            self.hidden = False
            self.put_away.discard("home")
            self.cancel_drag(); self.follow = False; self.target = None; self.wake()
            if action == "rescue":
                self.pets_hidden = False
                p.solo = False
                for i, member in enumerate([p] + g.household.friends):
                    member.x, member.y = self.clamp((self.w / 2 + i * 30, self.h - 30))
                    member.hidden = member.carried = member.on_bed = False; member.z = 0
                g.household.targets.clear(); g.household.activities.clear()
            self.window.show()
            self.save_layout(); p.say("HERE WE ARE!")
        elif action == "quit": g.running = False

    def cancel_drag(self):
        if isinstance(self.drag_item, str): self.save_layout()
        elif self.drag_item is not None: self.drag_item.carried = False
        self.drag_start = self.drag_item = None
        if hasattr(self.window, "capture"): self.window.capture(False)

    def move_drag(self, pos):
        if not self.drag_start: return
        if math.dist(pos, self.drag_start) <= 2 and not self.dragged: return
        self.dragged = True
        if isinstance(self.drag_item, str):
            r = self.prop_rect(self.drag_item)
            r.topleft = (int(pos[0] - self.drag_offset[0]), int(pos[1] - self.drag_offset[1]))
            self.clamp_rect(r)
        else:
            p = self.drag_item
            ratio = self.game.settings.pet_scale / getattr(self.window, "scale", 3)
            p.carried = True; p.x, p.y = self.clamp((pos[0], pos[1] + 12 * ratio))
            p.anim.play("dangle")

    def event(self, ev):
        pos = self.window.mouse()
        if hasattr(ev, "pos"):
            scale = getattr(self.window, "scale", 1)
            pos = ev.pos[0] / scale, ev.pos[1] / scale
        if ev.type == pygame.QUIT: self.game.running = False
        elif ev.type == getattr(pygame, "WINDOWFOCUSLOST", -1): self.cancel_drag()
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE: self.menu = None; self.cancel_drag()
            elif ev.key == pygame.K_F9: self.command("rescue")
            elif ev.key == pygame.K_F10: self.game.leave_desktop()
            else:
                mapping = {pygame.K_h: "home", pygame.K_d: "home", pygame.K_s: "sleep", pygame.K_f: "feed", pygame.K_p: "play", pygame.K_e: "pet", pygame.K_c: "follow", pygame.K_q: "quiet", pygame.K_SPACE: "dance"}
                if ev.key in mapping: self.command(mapping[ev.key])
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 3:
                self.cancel_drag()
                self.context_item = self.item_at(pos)
                self.open_menu(pos)
            elif ev.button == 1:
                if self.recovery_visible() and self.recovery_rect().collidepoint(pos):
                    self.cancel_drag()
                    self.context_item = None
                    self.open_menu((self.recovery_rect().x, self.recovery_rect().y - 160), 'visibility')
                    return
                if self.menu:
                    if self.menu.collidepoint(pos):
                        if pos[1] >= self.menu.bottom - 24:
                            self.menu_page = (self.menu_page + 1) % ((len(self.menu_entries()) + 7) // 8)
                            return
                        i = int((pos[1] - self.menu.y - 5) // 16)
                        index = self.menu_page * 8 + i
                        entries = self.menu_entries()
                        self.menu = None
                        if 0 <= i < 8 and index < len(entries): self.command(entries[index][0])
                    else: self.menu = None
                    return
                if self.controls_visible(pos):
                    for r, key in zip(self.controls(), ("compact", "hide")):
                        if r.collidepoint(pos): self.command(key); return
                for p in reversed(self.visible_pets()):
                    if not p.hidden and self.pet_rect(p).inflate(6, 6).collidepoint(pos):
                        self.found_click = self.fun.found() if p is self.pet else False
                        self.fun.stop()
                        self.drag_item = p
                        if p is self.pet: self.wake(); self.target = None
                        break
                else:
                    key = self.item_at(pos)
                    if key:
                        self.fun.stop()
                        r = self.prop_rect(key)
                        self.drag_item = key
                        self.drag_offset = (pos[0] - r.x, pos[1] - r.y)
                if self.drag_item is not None:
                    self.drag_start = pos; self.dragged = False
                    if hasattr(self.window, "capture"): self.window.capture(True)
        elif ev.type == pygame.MOUSEMOTION: self.move_drag(pos)
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.drag_start:
            self.move_drag(pos)
            item, dragged = self.drag_item, self.dragged
            self.cancel_drag()
            if isinstance(item, str):
                if not dragged:
                    if item.startswith('@'):
                        if item == '@bed': self.command('sleep')
                        else: self.pet.say('A COZY LITTLE CORNER!')
                    else: self.command({"home": "home", "food": "feed", "water": "drink", "ball": "play"}[item])
            elif not dragged:
                if item is self.pet:
                    self.command("pet")
                    if self.found_click: self.pet.say('OOPS! YOU FOUND ME! HEHE!', 4)
                else: self.game.household.interact(self.game.household.friends.index(item))
            elif item is self.pet and not self.hidden and self.home.collidepoint(pos): self.command("home")
            else: item.say("WHEEE!")

    def update(self, dt):
        p, g = self.pet, self.game
        self.area_check += dt
        if self.area_check >= 2:
            self.area_check = 0
            if hasattr(self.window, "area_changed") and self.window.area_changed():
                self.save_layout()
                g.leave_desktop(); g.enter_desktop()
                return
        self.clock += dt
        # Hidden pets rest in place; no invisible care/reward farming or needs loss.
        if self.pets_hidden: self.fun.stop(); return
        # Only the short, deliberate home-entry transition may hide a pet.
        if self.state != "enter": p.hidden = False
        if self.fun.mode != 'peek': p.x, p.y = self.clamp((p.x, p.y))
        if self.menu: p.update(dt); return
        keys = pygame.key.get_pressed()
        if any(keys[k] for k in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN)):
            self.fun.stop()
        elif self.fun.update(dt):
            p.update(dt); p.tick_needs(dt, 'walk', False)
            g.household.update(dt, self)
            return
        if g.settings.quiet and self.state in ("idle", "sit", "sleep") and not self.follow:
            p.anim.play("sleep" if p.energy < 60 else "sit")
            p.update(dt); p.tick_needs(dt, "sleep", False)
            g.household.update(dt, self)
            return
        activity = "idle"
        if self.drag_start:
            self.move_drag(self.window.mouse())
        else:
            keys = pygame.key.get_pressed()
            dx, dy = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT]), int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
            if dx or dy: self.walk((p.x + dx * 60, p.y + dy * 60))
            elif self.follow:
                pos = self.clamp(self.window.mouse())
                if math.dist((p.x, p.y), pos) > 25: self.walk((pos[0] - 12, pos[1]))
                else: self.target = None; self.state = "idle"
            if self.state == "walk" and self.target:
                dx, dy = self.target[0] - p.x, self.target[1] - p.y
                distance = math.hypot(dx, dy)
                speed = 78 if p.zoomies > 0 else 36
                step = min(distance, speed * dt)
                if distance > 1:
                    p.x += dx / distance * step; p.y += dy / distance * step
                    p.face_vector(dx, dy); p.anim.play("walk_" + p.facing)
                    activity = "walk"; p.stats["distance_walked"] += step
                    self.explore_distance += step
                    if self.explore_distance >= 600: self.explore_distance -= 600; self.reward("explore")
                else:
                    self.state = self.after or "idle"; self.after = None; self.target = None; self.timer = 3; self.sleep_time = 0
            elif self.state == "enter":
                p.hidden = True
                self.timer -= dt
                if self.timer <= 2.6:
                    g.leave_desktop()
                    return
            elif self.state == "sleep":
                activity = "sleep"
                p.hidden = False; p.anim.play("sleep")
                self.sleep_time += dt
                if self.sleep_time >= 5 and p.energy >= WAKE_ENERGY:
                    p.stats["total_sleeps"] += 1; self.reward("sleep"); self.wake(); p.say("ALL RESTED!")
            elif self.state in ("eat", "drink", "play", "dance", "wave"):
                p.anim.play("eat" if self.state == "drink" else self.state)
                self.timer -= dt
                if self.timer <= 0:
                    if self.state == "eat":
                        meal(p); p.stats["total_feeds"] += 1; g.daily_event("feed"); self.reward("feed"); g.audio.play("eat")
                    elif self.state == "play":
                        p.happiness = min(100, p.happiness + 20); p.energy = max(0, p.energy - 10)
                        p.stats["total_plays"] += 1; g.daily_event("play"); self.reward("play"); g.voice()
                    elif self.state == "drink": p.stats["total_drinks"] += 1; p.happiness = min(100, p.happiness + 2)
                    self.wake()
            else:
                p.anim.play("idle"); self.timer -= dt
                if self.timer <= 0 and not self.follow:
                    if p.energy < 22: self.command("sleep")
                    else: self.walk((random.uniform(20, self.w - 20), random.uniform(40, self.h - 12)))
        p.update(dt); p.tick_needs(dt, activity, g.daynight.darkness > .6)
        g.household.update(dt, self)

    def draw(self):
        c, g = self.window.canvas, self.game
        c.fill(DESKTOP_KEY)
        ui_canvas = getattr(self.window, "ui_canvas", c)
        if ui_canvas is not c:
            ui_canvas.fill(DESKTOP_KEY)
        if 'home' in self.visible_props():
            c.blit(pygame.transform.scale(g.assets.room_style(self.pet.room_theme)["house"], self.home.size), self.home)
            if self.controls_visible():
                for r, label in zip(self.controls(), ("+" if self.compact else "-", "X")):
                    g.ui.small_button(c, r, label, r.collidepoint(self.window.mouse()))
            if self.pet.hidden: g.ui.text(c, "ZZZ" if self.state == "sleep" else "HOME!", (self.home.x, self.home.y - 24), GOLD)
        for key, img in (('food', g.assets.meals[self.pet.selected_food][0]), ('water', g.assets.water[0]), ('ball', g.assets.toys[self.pet.selected_toy])):
            if key in self.visible_props(): c.blit(img, self.prop_rect(key))
        for key, rect in sorted(self.furniture.items(), key=lambda item: item[1].bottom):
            if not self.items_hidden: c.blit(self.furniture_image(key), rect)
        self.fun.draw(c)
        if ui_canvas is c:  # Headless/platform-neutral preview adapter.
            self.renderer.draw(c, self.visible_pets(), g.assets, 1, 1)
        else:
            self.window.pets, self.window.assets = self.visible_pets(), g.assets
            self.window.pet_scale = g.settings.pet_scale
        c = ui_canvas
        if self.recovery_visible():
            r = self.recovery_rect()
            g.ui.small_button(c, r, 'PET MENU', r.collidepoint(self.window.mouse()))
        if self.menu:
            g.ui.draw_panel(c, self.menu)
            for i, (key, label) in enumerate(self.menu_entries()[self.menu_page*8:self.menu_page*8+8]):
                if key == "follow": label += " ON" if self.follow else " OFF"
                if key == "quiet": label += " ON" if g.settings.quiet else " OFF"
                if key == "surprises": label += " ON" if g.settings.surprises else " OFF"
                if key == "pause": label = "RESUME" if g.paused else "PAUSE"
                r = pygame.Rect(self.menu.x + 4, self.menu.y + 5 + i * 16, self.menu.w - 8, 15)
                g.ui.small_button(c, r, label, r.collidepoint(self.window.mouse()))
            g.ui.small_button(c, (self.menu.x+4, self.menu.bottom-23, self.menu.w-8, 19),
                              "MORE %d/%d >" % (self.menu_page+1, (len(self.menu_entries())+7)//8), False)
        self.window.present()

    def restore(self):
        self.fun.stop()
        self.cancel_drag()
        self.pet.x, self.pet.y = self.room_pos
        self.pet.hidden = self.pet.carried = self.pet.on_bed = False; self.pet.z = 0
        self.game.household.targets.clear()
        self.game.household.activities.clear()
        for i, friend in enumerate(self.game.household.friends):
            friend.x, friend.y = self.game.world.nearest_free(190 + i * 30, 190) or (240, 190)
            friend.hidden = friend.carried = friend.on_bed = False; friend.z = 0
        self.window.close()
