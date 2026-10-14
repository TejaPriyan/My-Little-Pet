"""Main game: owns the window, scenes, input routing and the game loop."""
import time

import pygame

from ai import Brain, State
from assets import Assets
from audio import Audio
from config import (W, H, HUD_H, BAR_Y, AUTOSAVE_SECONDS, SHOP_ITEMS, ACHIEVEMENTS, INK, GOLD, SPECIES, ACCESSORIES)
from display import DisplayManager
from effects import Effects
from minigame import BugCatchGame, TreatDropGame
from activities import record, refresh, unlock_rooms, ROOMS
from menus import ShopMenu, ChoiceMenu, Tutorial
from pet import Pet
from pixelfont import PixelFont
from save_system import SaveSystem, default_data, clean_name
from settings import Settings, TIME_MODES
from ui import (UI, NameScreen, SettingsMenu, ConfirmDialog, StatsAndAwardsMenu, Fade, RED)
from world import World, DayNight

SHORTCUTS = {
    pygame.K_h: "home", pygame.K_f: "feed", pygame.K_p: "play", pygame.K_s: "sleep",
    pygame.K_e: "pet", pygame.K_g: "game", pygame.K_c: "follow", pygame.K_b: "shop",
    pygame.K_t: "stats",
    pygame.K_d: "desktop", pygame.K_q: "quiet",
}


class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        self.settings = Settings.load()
        self.display = DisplayManager(self.settings.fullscreen)
        self.canvas = pygame.Surface((W, H)).convert()
        self.assets = Assets()
        self.font = PixelFont()
        try:
            icon = pygame.transform.scale(self.assets.pet["idle"].frames[0], (48, 48))
            pygame.display.set_icon(icon)
        except pygame.error:
            pass
        self.audio = Audio(self.settings)
        self.audio.apply_settings()
        self.saves = SaveSystem()
        self.ui = UI(self.assets, self.font)
        self.fx = Effects(self.assets, self.font)
        self.fade = Fade()
        self.clock = pygame.time.Clock()
        self.daynight = DayNight(self.settings.time_mode)
        self.running = True
        self.desktop = None
        self.voice_timer = 0.0
        self.chatter_timer = 20.0
        self.t = 0.0
        self.autosave_t = 0.0
        self.ach_timer = 0.0
        self.overlay = None
        self.session = False
        self.world = World(self.assets)
        self.pet = self.brain = None
        self.mouse = (W / 2, H / 2)
        self.follow_pt = (240.0, 190.0)

        data = self.saves.load()
        if data:
            self.start_session(data, offline=True)
        else:
            self.open_name_screen()
        if self.settings.desktop and self.session:
            self.enter_desktop()

    # ================================================================ sessions
    def open_name_screen(self):
        self.session = False
        self.pet = self.brain = None
        self.world = World(self.assets)
        self.fx.parts.clear()
        self.fx.texts.clear()
        self.overlay = NameScreen(self.ui, self.assets, self._submit_name)

    def _submit_name(self, name, owner_name="Friend"):
        self.audio.play("click")
        self.fade.start(lambda: self._begin_new(name, owner_name))

    def _begin_new(self, name, owner_name="Friend"):
        self.overlay = None
        self.start_session(default_data(name, owner_name), offline=False)
        self.brain._enter(State.HAPPY, 2.2)
        self.pet.say("HI " + self.pet.owner_name.upper() + "!", 4)
        self.fx.hearts(self.pet.x, self.pet.y - 16, 4)
        self.save_now()
        self.show_help()

    def start_session(self, data, offline):
        self.world = World(self.assets)
        self.pet = Pet(self.assets, data)
        refresh(self.pet)
        unlock_rooms(self.pet)
        self.world.set_weather(self.settings.weather)
        away = 0.0
        if offline:
            away = self.pet.apply_offline(time.time() - data.get("last_saved_time", time.time()))
        if not self.world.is_free(self.pet.x, self.pet.y):
            pt = self.world.nearest_free(self.pet.x, self.pet.y)
            if pt:
                self.pet.x, self.pet.y = pt
        self.fx.parts.clear()
        self.fx.texts.clear()
        self.brain = Brain(self.pet, self.world, self.fx, self._on_event)
        self.ui.disp_init = False
        self.ui.button("follow").active = False
        self.session = True
        self.pet.say("HI " + self.pet.owner_name.upper() + "!", 4)

    def save_now(self):
        if self.session and self.pet:
            data = self.pet.to_dict()
            if self.desktop:
                data["position_x"], data["position_y"] = self.desktop.room_pos
            if not self.saves.save(data):
                self.ui.toast("SAVE FAILED - CHECK FOLDER ACCESS", RED, 5)

    def voice(self, name=None):
        if self.settings.voice and self.voice_timer <= 0:
            self.audio.play(name or self.pet.voice, .55)
            self.voice_timer = 6.0

    def daily_event(self, kind):
        if record(self.pet, kind):
            self.ui.toast("DAILY CARE COMPLETE! +30 COINS", GOLD, 4)
            self.pet.say("BEST DAY TOGETHER!")
            self.audio.play("coin")

    def show_help(self):
        self.overlay = Tutorial(self.ui, self._finish_help)

    def _finish_help(self):
        self.pet.tutorial_seen = True
        self._close_overlay()
        self.pet.say("HI " + self.pet.owner_name.upper() + "!", 4)

    def enter_desktop(self):
        if self.desktop or not self.session: return
        from desktop import DesktopPet
        window = None
        try:
            window = self.display.enter_overlay_mode(self.settings.pet_scale)
            self.desktop = DesktopPet(self, window)
        except (OSError, pygame.error, AttributeError) as exc:
            if window: window.close()
            self.settings.desktop = False
            self.display.restore_room()
            self.ui.toast("DESKTOP MODE COULD NOT OPEN", RED, 5)
            print("Desktop mode:", exc)
            return
        self.overlay = None
        self.settings.desktop = True
        self.pet.stats["desktop_visits"] = self.pet.stats.get("desktop_visits", 0) + 1
        self.check_achievements()
        self.save_now()
        self.settings.save()

    def leave_desktop(self):
        if not self.desktop: return
        self.desktop.restore()
        self.desktop = None
        self.settings.desktop = False
        self.display.restore_room()
        self.brain = Brain(self.pet, self.world, self.fx, self._on_event)
        self.ui.button("follow").active = False
        self.settings.save()
        self.save_now()

    # ================================================================ brain events
    def _on_event(self, name, **kw):
        pet = self.pet
        if name == "step":
            self.fx.dust(pet.x, pet.y)
            self.audio.play("walk", 0.5)
        elif name == "munch":
            self.audio.play("eat", 0.8)
        elif name == "happy":
            self.audio.play("happy", 0.8)
        elif name == "sleep_start":
            self.audio.play("sleep")
        elif name == "bounce":
            self.audio.play("click", 0.3)
        elif name == "bang":
            self.fx.bang(kw["x"], kw["y"])
        elif name in ("fed", "played", "slept", "petted"):
            if name == "fed": self.daily_event("feed")
            if name == "played": self.daily_event("play")
            if name == "petted": self.voice("purr" if pet.species == "cat" else pet.voice)
            self.check_achievements()
            self.save_now()
        elif name == "levelup":
            unlock_rooms(pet)
            self.audio.play("levelup")
            self.fx.burst(pet.x, pet.y - 12)
            self.ui.show_banner(pet.name, kw["level"])
            self.check_achievements()
            self.save_now()

    # ================================================================ input
    def handle_events(self):
        self.mouse = self.display.to_internal(pygame.mouse.get_pos())
        for ev in pygame.event.get():
            if self.desktop:
                self.desktop.event(ev)
                continue
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.VIDEORESIZE:
                self.display.on_resize(pygame.display.get_surface().get_size())
            elif ev.type == pygame.KEYDOWN:
                self._on_key(ev)
            elif ev.type == pygame.MOUSEBUTTONDOWN and getattr(ev, "button", 1) == 1:
                self._on_click(self.display.to_internal(ev.pos))

    def _on_key(self, ev):
        if self.overlay:
            self.overlay.on_key(ev)
            return
        k = ev.key
        if k == pygame.K_F11:
            self.settings.fullscreen = not self.settings.fullscreen
            self._settings_changed()
            return
        if self.fade.busy or not self.session:
            return
        if k == pygame.K_ESCAPE:
            self.do_action("menu")
        elif k == pygame.K_n:
            i = (TIME_MODES.index(self.settings.time_mode) + 1) % len(TIME_MODES)
            self.settings.time_mode = TIME_MODES[i]
            self.ui.toast("TIME: " + TIME_MODES[i].upper())
            self._settings_changed()
        elif k in SHORTCUTS:
            self.do_action(SHORTCUTS[k])
        elif k in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
            self._fresh_arrow = True

    def _on_click(self, pos):
        self.mouse = pos
        if self.overlay:
            self.audio.play("click", 0.6)
            self.overlay.on_click(pos)
            return
        if self.fade.busy or not self.session:
            return
        key = self.ui.click(pos)
        if key:
            self.audio.play("click", 0.6)
            self.do_action(key)
            return
        if not (HUD_H <= pos[1] < BAR_Y):
            return
        pet = self.pet
        if pygame.Rect(int(pet.x) - 12, int(pet.y) - 22 - int(pet.z), 24, 24).collidepoint(pos):
            self.do_action("pet", look_at=pos)
            return
        obj = self.world.object_at(pos)
        if obj:
            self._click_object(obj)
            return
        b = self.world.BOUNDS
        px, py = max(b.x, min(b.right - 1, pos[0])), max(b.y, min(b.bottom - 1, pos[1]))
        pt = (px, py) if self.world.is_free(px, py) else self.world.nearest_free(px, py)
        if pt:
            self.brain.command("goto", point=pt)

    def _click_object(self, name):
        w = self.world
        if name == "food":
            self.do_action("feed")
        elif name == "water":
            self.brain.command("drink")
        elif name == "bed":
            self.do_action("sleep")
        elif name == "toy":
            self.do_action("play")
        elif name in w.landmarks:
            self.brain.command("visit", point=w.landmarks[name][0], name=name)

    def do_action(self, key, **kw):
        pet, brain = self.pet, self.brain
        if key == "menu":
            self._open_settings()
        elif key == "shop":
            self.overlay = ShopMenu(self.ui, pet, self._buy, self._close_overlay)
        elif key == "stats":
            self.overlay = StatsAndAwardsMenu(self.ui, pet, self._close_overlay)
        elif key == "game":
            self.overlay = ChoiceMenu(self.ui, "LET'S PLAY!", [("bugs", "CATCH THE BUG"), ("treats", "TREAT DROP"),
                ("daily", "DAILY CARE GOALS")], self._pick_game, self._close_overlay)
        elif key == "desktop":
            self.enter_desktop()
        elif key == "quiet":
            self.settings.quiet = not self.settings.quiet
            self._settings_changed()
            self.ui.toast("QUIET: " + ("ON" if self.settings.quiet else "OFF"))
        elif key == "follow":
            on = not brain.follow
            brain.set_follow(on)
            self.ui.button("follow").active = on
            self.ui.toast("FOLLOW MODE: " + ("ON" if on else "OFF"))
        elif key == "pet":
            brain.command("pet", look_at=kw.get("look_at") or self.mouse)
        elif key == "feed":
            if pet.hunger >= 98:
                pet.say("I'M FULL!", 2.0)
            else:
                brain.command("feed")
        elif key == "play":
            if pet.energy < 12:
                pet.say("TOO TIRED...", 2.2)
            else:
                brain.command("play")
        elif key in ("home", "sleep"):
            brain.command(key)

    def _read_input(self):
        if self.overlay or self.fade.busy or not self.session:
            self._fresh_arrow = False
            return (0, 0, False, False)
        keys = pygame.key.get_pressed()
        dx = int(bool(keys[pygame.K_RIGHT])) - int(bool(keys[pygame.K_LEFT]))
        dy = int(bool(keys[pygame.K_DOWN])) - int(bool(keys[pygame.K_UP]))
        run = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
        fresh, self._fresh_arrow = self._fresh_arrow, False
        return (dx, dy, run, fresh)

    _fresh_arrow = False

    # ================================================================ overlays
    def _close_overlay(self):
        self.overlay = None
        self.check_achievements()
        self.save_now()

    def _on_minigame_finish(self):
        if getattr(self.overlay, "rewarded", False):
            self.daily_event("game")
        if getattr(self.overlay, "levels_gained", 0):
            self._on_event("levelup", level=self.pet.level)
        self._close_overlay()
        self.check_achievements()

    def _pick_game(self, key):
        if key == "daily":
            refresh(self.pet)
            d = self.pet.daily
            entries = [("back", "FEED %d/3  PLAY %d/2  GAME %d/1" % (d.get("feed", 0), d.get("play", 0), d.get("game", 0))),
                       ("back", "30 COINS CLAIMED!" if d.get("claimed") else "FINISH ALL THREE FOR 30 COINS")]
            self.overlay = ChoiceMenu(self.ui, "DAILY CARE", entries, lambda _: self.do_action("game"), self._close_overlay)
        else:
            cls = TreatDropGame if key == "treats" else BugCatchGame
            self.overlay = cls(self.ui, self.pet, self.audio, self.fx, self._on_minigame_finish)

    def _open_settings(self, sel=0):
        self.overlay = SettingsMenu(self.ui, self.settings, self._settings_changed,
                                    self._ask_reset, self._close_settings)
        self.overlay.sel = sel
        self.overlay.on_help = self.show_help
        self.overlay.on_profile = self._open_profile

    def _open_profile(self):
        self.overlay = NameScreen(self.ui, self.assets, self._save_profile,
                                  self.pet.name, self.pet.owner_name, self._open_settings)

    def _save_profile(self, name, owner_name):
        self.pet.name = clean_name(name, self.pet.name)
        self.pet.owner_name = clean_name(owner_name, self.pet.owner_name)
        self.save_now()
        self.overlay = None
        self.pet.say("HI " + self.pet.owner_name.upper() + "!", 4)
        self.ui.toast("NAMES SAVED - SAME HAPPY PET!")

    def _close_settings(self):
        self.overlay = None
        self.settings.save()

    def _settings_changed(self):
        self.audio.apply_settings()
        self.display.set_fullscreen(self.settings.fullscreen)
        self.daynight.set_mode(self.settings.time_mode)
        self.world.set_weather(self.settings.weather)
        if self.settings.desktop and not self.desktop:
            self.enter_desktop()
        self.settings.save()

    def _ask_reset(self):
        self.overlay = ConfirmDialog(
            self.ui, ["RESET YOUR PET?", "ALL PROGRESS WILL BE LOST."],
            self._do_reset, lambda: self._open_settings(6))

    def _do_reset(self):
        self.overlay = None
        self.saves.delete()
        self.fade.start(self.open_name_screen)

    def _buy(self, key):
        pet = self.pet
        if key == "coat":
            pet.set_look(coat=(pet.coat + 1) % 3)
            self.save_now()
            return
        if key == "none":
            pet.equipped["head"] = None
            self.save_now()
            return
        if key.startswith("room:"):
            room = key.split(":", 1)[1]
            unlock_rooms(pet)
            if room in pet.owned_rooms:
                pet.room_theme = room
                self.save_now()
            else: self.ui.toast("KEEP GROWING TO UNLOCK THIS ROOM")
            return
        if key.startswith("species:") or key.startswith("style:"):
            group, choice = key.split(":", 1)
            catalog = SPECIES if group == "species" else ACCESSORIES
            if choice not in catalog: return
            owned = choice in pet.owned_species if group == "species" else pet.inventory.get(choice, 0) > 0
            if not owned:
                price = catalog[choice]["price"]
                if pet.coins < price:
                    self.ui.toast("NOT ENOUGH COINS", RED)
                    return
                pet.coins -= price
                if group == "species": pet.owned_species.append(choice)
                else: pet.inventory[choice] = 1
                self.audio.play("coin")
            if group == "species": pet.set_look(species=choice)
            else: pet.equipped["head"] = choice
            self.check_achievements()
            self.save_now()
            return
        if key not in SHOP_ITEMS: return
        item, pet = SHOP_ITEMS[key], self.pet
        repeatable = item.get("repeatable", True)
        owned = pet.inventory.get(key, 0)
        if not repeatable and owned > 0:
            if key == "hat":
                pet.equipped["hat"] = not pet.equipped.get("hat", True)
                state_str = "EQUIPPED" if pet.equipped["hat"] else "UNEQUIPPED"
                self.ui.toast("FANCY BOW " + state_str)
                self.audio.play("click", 0.6)
                self.save_now()
            else:
                self.ui.toast("ALREADY OWNED")
            return
        if pet.coins < item["price"]:
            self.ui.toast("NOT ENOUGH COINS", RED)
            return

        pet.coins -= item["price"]
        pet.inventory[key] = owned + 1
        self.ui.toast("BOUGHT " + item["name"])
        self.audio.play("happy", 0.6)

        if key == "catnip":
            pet.zoomies = 15.0
            pet.happiness = min(100.0, pet.happiness + 35.0)
            pet.say("ZOOMIES! WHEEE!", 2.8)
            self.fx.hearts(pet.x, pet.y - 16, 6)
            self.fx.sparkles(pet.x, pet.y - 10, 8)
            pet.inventory[key] -= 1
        elif key == "energy":
            pet.energy = min(100, pet.energy + 30)
            pet.inventory[key] -= 1
            pet.say("READY TO PLAY!")
        elif key == "hat":
            pet.equipped["hat"] = True
            pet.say("SO STYLISH!", 2.5)
            self.fx.sparkles(pet.x, pet.y - 20, 6)

        self.check_achievements()
        self.save_now()

    def check_achievements(self):
        if not self.session or not self.pet:
            return
        pet = self.pet
        st = pet.stats

        checks = {
            "first_feed": st.get("total_feeds", 0) >= 1,
            "first_play": st.get("total_plays", 0) >= 1,
            "loved": st.get("total_pettings", 0) >= 10,
            "level_5": pet.level >= 5,
            "level_10": pet.level >= 10,
            "rich": pet.coins >= 100,
            "night_owl": self.brain is not None and self.brain.night and st.get("time_played", 0) >= 45,
            "fashion": any(pet.inventory.get(k, 0) for k in ACCESSORIES),
            "bug_hunter": st.get("high_score", 0) >= 15,
            "marathon": st.get("distance_walked", 0.0) >= 1500.0,
            "treat_master": st.get("treat_high_score", 0) >= 20,
            "adopter": len(pet.owned_species) > 1,
            "desktop": st.get("desktop_visits", 0) > 0,
        }

        for ach_id, earned in checks.items():
            if earned and ach_id not in pet.achievements:
                pet.achievements.add(ach_id)
                ach = ACHIEVEMENTS.get(ach_id, {"title": ach_id.upper(), "reward": 10})
                reward = ach.get("reward", 10)
                pet.coins += reward
                self.ui.toast("UNLOCKED: " + ach["title"], GOLD, 3.5)
                self.audio.play("award", 0.9)
                self.fx.sparkles(pet.x, pet.y - 20, 8, spread=16)
                self.save_now()

    # ================================================================ loop
    def update(self, dt):
        self.t += dt
        self.voice_timer = max(0, self.voice_timer - dt)
        if self.session and not self.overlay:
            self.chatter_timer -= dt
            if self.chatter_timer <= 0:
                self.chatter_timer = 20 + 20 * (1 - self.pet.personality["friendliness"])
                if not self.pet.hidden and self.pet.anim.name not in ("sleep", "eat"):
                    self.voice()
        if self.desktop:
            self.daynight.update(dt)
            self.desktop.update(dt)
            self.autosave_t += dt
            if self.autosave_t >= AUTOSAVE_SECONDS:
                self.autosave_t = 0
                self.check_achievements()
                self.save_now()
            return
        mouse = self.display.to_internal(pygame.mouse.get_pos())
        self.mouse = mouse
        self.fade.update(dt)
        self.daynight.update(dt)
        self.fx.update(dt)
        self.world.update(dt)
        if self.session:
            if HUD_H <= mouse[1] < BAR_Y and 0 <= mouse[0] < W:
                b = self.world.BOUNDS
                self.follow_pt = (max(b.x, min(b.right, mouse[0])), max(b.y, min(b.bottom, mouse[1])))
            self.brain.night = self.daynight.darkness > 0.6
            if not self.overlay:
                self.brain.update(dt, self._read_input(), self.follow_pt if self.brain.follow else None, mouse)
                for ev in self.pet.update(dt): self._on_event(ev)
                self.pet.tick_needs(dt, self.brain.activity, self.brain.night)
            self.ui.update(dt, mouse, self.pet)
            self.autosave_t += dt
            if self.autosave_t >= AUTOSAVE_SECONDS:
                self.autosave_t = 0.0
                self.save_now()
            self.ach_timer += dt
            if self.ach_timer >= 1.5:
                self.ach_timer = 0.0
                self.check_achievements()
        else:
            self.ui.update(dt, mouse, None)
        if self.overlay:
            self.overlay.update(dt, mouse)

    def draw(self):
        if self.desktop:
            self.desktop.draw()
            return
        c = self.canvas
        c.fill((20, 10, 36))
        self.world.draw_background(c, self.t, self.daynight)
        if self.session and self.pet.room_theme != "classic":
            tint = pygame.Surface((W, BAR_Y - HUD_H), pygame.SRCALPHA)
            tint.fill((60, 180, 130, 35) if self.pet.room_theme == "garden" else (70, 80, 200, 45))
            c.blit(tint, (0, HUD_H))
            if self.pet.room_theme == "garden":
                for x in (170, 310, 450): c.blit(self.assets.plant[0], (x, 105))
            else:
                for x in range(35, W, 45): c.blit(self.assets.icons["star"], (x, 50 + (x % 3) * 8))
        self.world.draw_objects(c, self.t, self.pet if self.session else None, self.assets)
        self.fx.draw(c)
        self.world.draw_overlay(c, self.t, self.daynight)
        if self.session:
            self.ui.draw_bubble(c, self.pet)
            self.ui.draw_hud(c, self.pet)
            self.ui.draw_bar(c)
            self.ui.draw_overlays(c, self.brain.follow)
        else:
            self.ui.draw_panel(c, (0, 0, W, HUD_H))
            self.ui.draw_panel(c, (0, BAR_Y, W, H - BAR_Y))
        if self.overlay:
            self.overlay.draw(c)
        self.fade.draw(c)

    def run(self):
        try:
            while self.running:
                dt = min(self.clock.tick(self.settings.fps) / 1000.0, 0.05)
                self.handle_events()
                self.update(dt)
                self.draw()
                if not self.desktop: self.display.present(self.canvas)
        finally:
            self.shutdown()

    def shutdown(self):
        self.save_now()
        if self.desktop: self.desktop.window.close()
        self.settings.save()
        pygame.quit()
