"""Main game: owns the window, scenes, input routing and the game loop."""
import time
import os

import pygame

from ai import Brain, State
from assets import Assets
from audio import Audio
from config import (W, H, HUD_H, BAR_Y, AUTOSAVE_SECONDS, SHOP_ITEMS, ACHIEVEMENTS, INK, GOLD, SPECIES, ACCESSORIES)
from display import DisplayManager, configure_dpi_awareness
from effects import Effects
from minigame import BugCatchGame, TreatDropGame, MemoryGardenGame, FireflyRhythmGame
from pet_games import PetGame, GardenHurdles
from life import TRAITS, set_trait, bond_key, bond_label, adventure, record_adventure, claim_adventure
from decorating import Decorator, apply_layout, draw_decor
from supplies import TOYS
from supply_menu import SupplyMenu
from household import Household, react
from economy import refresh_arcade
from config import FOODS, SLOT_PRICES
from activities import record, refresh, unlock_rooms, ROOMS, ROOM_PRICES
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
    pygame.K_r: "family", pygame.K_m: "food", pygame.K_SPACE: "dance",
    pygame.K_j: "adventure", pygame.K_v: "decorate",
}


class Game:
    def __init__(self):
        # Apply before SDL creates any windows, including owner-test launches.
        configure_dpi_awareness()
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
        self.paused = False
        self.tray = None
        self.desktop = None
        self.voice_timer = 0.0
        self.chatter_timer = 20.0
        self.dance_left = 0
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
        try:
            if os.environ.get("SDL_VIDEODRIVER") == "dummy": raise OSError("headless checks")
            from tray import Tray
            self.tray = Tray(self._tray_action)
        except (OSError, AttributeError) as exc:
            print("Tray controls unavailable:", exc)

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
        apply_layout(self.world, self.pet)
        self.household = Household(self)
        refresh(self.pet)
        unlock_rooms(self.pet)
        self.world.set_weather(self.settings.weather)
        away = 0.0
        if offline:
            away = self.pet.apply_offline(time.time() - data.get("last_saved_time", time.time()))
            for friend in self.household.friends: friend.apply_offline(away)
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
            self.household.save()
            data = self.pet.to_dict()
            if self.desktop:
                data["position_x"], data["position_y"] = self.desktop.room_pos
            if not self.saves.save(data):
                self.ui.toast("SAVE FAILED - CHECK FOLDER ACCESS", RED, 5)

    def voice(self, name=None):
        if not self.settings.quiet and self.settings.voice and self.voice_timer <= 0:
            self.audio.play(name or self.pet.voice, .55)
            self.voice_timer = 6.0

    def daily_event(self, kind):
        if record(self.pet, kind):
            self.ui.toast("DAILY CARE COMPLETE! +12 COINS", GOLD, 4)
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
            # Furniture uses a fixed grid; pet-only size is applied at presentation.
            window = self.display.enter_overlay_mode(3)
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
            if name == "petted":
                self.voice("purr" if pet.species == "cat" else pet.voice)
                record_adventure(pet, "cuddle")
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
            elif ev.type == pygame.MOUSEMOTION and isinstance(self.overlay, Decorator):
                self.overlay.on_motion(self.display.to_internal(ev.pos))
            elif ev.type == pygame.MOUSEBUTTONUP and getattr(ev, "button", 1) == 1 and isinstance(self.overlay, Decorator):
                self.overlay.on_release(self.display.to_internal(ev.pos))
            elif ev.type == getattr(pygame, "WINDOWFOCUSLOST", -1) and isinstance(self.overlay, Decorator):
                self.overlay.dragging = False

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
        if not adventure(pet).get("find") and self.adventure_rect().collidepoint(pos):
            record_adventure(pet, "find")
            pet.say("YOU FOUND MY LOST STAR!")
            self.ui.toast("LOST STAR FOUND! J: TODAY'S ADVENTURE")
            self.save_now()
            return
        if pygame.Rect(int(pet.x) - 12, int(pet.y) - 22 - int(pet.z), 24, 24).collidepoint(pos):
            self.do_action("pet", look_at=pos)
            return
        for i, friend in enumerate(self.household.visible):
            if friend.rect().collidepoint(pos):
                self.household.interact(i)
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
        self.paused = False
        if key == "menu":
            self._open_settings()
        elif key == "shop":
            self.overlay = ChoiceMenu(self.ui, "LITTLE PET SHOP", [("family", "ADD A PET / FAMILY"), ("catalog", "PET LOOKS / ACCESSORIES"), ("toys", "TOY BOX - CHOOSE A TOY"), ("rooms", "ROOMS / FLOORS / BEDS / HOUSES"), ("decorate", "DECORATE - PREVIEW + PLACE"), ("food", "PANTRY / CHOOSE FOOD"), ("family", "HOUSEHOLD / PET SLOTS")], self._shop_route, self._close_overlay)
        elif key == "stats":
            self.overlay = StatsAndAwardsMenu(self.ui, pet, self._close_overlay)
        elif key == "game":
            a = refresh_arcade(pet)
            self.overlay = ChoiceMenu(self.ui, "ARCADE: %d/3 LIVES" % a["lives"], [("fetch", "FETCH RELAY - THROW FOR YOUR PET"), ("hurdles", "GARDEN HURDLES - HELP THEM JUMP"), ("watch", "WATCH MY PET PLAY - FREE"), ("bugs", "CATCH THE BUG"), ("treats", "TREAT DROP"), ("memory", "MEMORY GARDEN"), ("rhythm", "FIREFLY RHYTHM"), ("refill", "REFILL LIVES - 20 COINS"), ("daily", "DAILY CARE / REWARD RULES")], self._pick_game, self._close_overlay)
        elif key == "decorate": self.overlay = Decorator(self)
        elif key == "adventure": self._adventure_menu()
        elif key == "family": self._family_menu()
        elif key == "food": self._food_menu()
        elif key == "toys": self._toy_menu()
        elif key == "dance":
            brain.command("idle")
            self.dance_left = 5
            pet.say("ONE, TWO, WIGGLE!")
            self.household.socialize("dance")
            self.voice()
        elif key == "desktop":
            self.enter_desktop()
        elif key == "quiet":
            self.settings.quiet = not self.settings.quiet
            brain.command("idle")
            brain.set_follow(False)
            self.ui.button("follow").active = False
            self._settings_changed()
            self.ui.toast("QUIET: " + ("ON" if self.settings.quiet else "OFF"))
        elif key == "follow":
            on = not brain.follow
            brain.set_follow(on)
            self.ui.button("follow").active = on
            self.ui.toast("FOLLOW MODE: " + ("ON" if on else "OFF"))
        elif key == "pet":
            brain.command("pet", look_at=kw.get("look_at") or self.mouse)
            react(pet)
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
        if getattr(self.overlay, "completed", False) and not getattr(self.overlay, "watch", False):
            self.daily_event("game")
            if isinstance(self.overlay, PetGame) and not self.overlay.watch and self.overlay.score > 0:
                record_adventure(self.pet, "game")
        if getattr(self.overlay, "levels_gained", 0):
            self._on_event("levelup", level=self.pet.level)
        self._close_overlay()
        self.check_achievements()

    def _pick_game(self, key):
        if key == "watch":
            self.overlay = ChoiceMenu(self.ui, "WATCH + RELAX", [("watch:fetch", "WATCH FETCH - NO LIVES / NO COINS"), ("watch:hurdles", "WATCH HURDLES - NO LIVES / NO COINS")], self._pick_game, self._close_overlay)
            return
        if key in ("fetch", "hurdles", "watch:fetch", "watch:hurdles"):
            cls = PetGame if key.endswith("fetch") else GardenHurdles
            self.overlay = cls(self.ui, self.pet, self.audio, self.fx, self._on_minigame_finish, watch=key.startswith("watch:"))
            self.overlay.spectators = self.household.visible
            self.save_now()
            return
        if key == "refill":
            a = refresh_arcade(self.pet)
            if a["lives"] == 3: self.ui.toast("LIVES ALREADY FULL")
            elif self.pet.coins < 20: self.ui.toast("NEED 20 COINS. PRACTICE IS FREE!")
            else: self.pet.coins -= 20; a["lives"] = 3; a["refill_at"] = time.time(); self.save_now()
            self.do_action("game")
            return
        if key == "daily":
            refresh(self.pet)
            d = self.pet.daily
            entries = [("back", "FEED %d/3  PLAY %d/2  GAME %d/1" % (d.get("feed", 0), d.get("play", 0), d.get("game", 0))),
                       ("back", "12 COINS CLAIMED!" if d.get("claimed") else "FINISH ALL THREE FOR 12 COINS"), ("back", "1 LIFE / 30 MIN. NO LIVES? FREE PRACTICE."), ("back", "FULL ROUNDS: UP TO 8 COINS. 40 PER DAY.")]
            self.overlay = ChoiceMenu(self.ui, "DAILY CARE", entries, lambda _: self.do_action("game"), self._close_overlay)
        else:
            cls = {"treats": TreatDropGame, "memory": MemoryGardenGame, "rhythm": FireflyRhythmGame}.get(key, BugCatchGame)
            self.overlay = cls(self.ui, self.pet, self.audio, self.fx, self._on_minigame_finish)
            self.save_now()

    def _shop_route(self, key):
        if key == "catalog": self.overlay = ShopMenu(self.ui, self.pet, self._buy, self._close_overlay)
        elif key == "rooms":
            entries = [("room:" + k, n + (" - OWNED" if k in self.pet.owned_rooms else " - %d COINS" % ROOM_PRICES[k] if k in ROOM_PRICES else " - LEVEL %d" % level)) for k, (n, level) in ROOMS.items()]
            self.overlay = ChoiceMenu(self.ui, "ROOM BUNDLES - %d COINS" % self.pet.coins, entries, self._buy, self._close_overlay)
        else: self.do_action(key)

    def _food_menu(self):
        p = self.pet
        self.overlay = SupplyMenu(self, "food")

    def _toy_menu(self):
        self.overlay = SupplyMenu(self, "toys")

    def _choose_toy(self, key):
        if key not in TOYS: return
        p = self.pet
        price = 0 if key in p.owned_toys else TOYS[key][1]
        if p.coins < price:
            self.ui.toast("NEED MORE COINS"); return
        p.coins -= price
        if key not in p.owned_toys: p.owned_toys.append(key)
        p.selected_toy = key
        self.save_now(); self._toy_menu()
        self.ui.toast("READY TO PLAY: " + TOYS[key][0])

    def _choose_food(self, key):
        if key not in FOODS: return
        p, food = self.pet, FOODS[key]
        if key != "kibble" and p.pantry.get(key, 0) < 1:
            if p.coins < food["price"]: self.ui.toast("NEED MORE COINS. EVERYDAY BOWL IS FREE."); return
            p.coins -= food["price"]; p.pantry[key] = 1
        p.selected_food = key
        self.world.bowl_full, self.world.bowl_timer = True, 30.0
        self.world.food.frame_index = 0
        self.save_now(); self._food_menu()
        self.ui.toast("NEXT MEAL: " + food["name"])

    def _family_menu(self):
        p = self.pet
        entries = [("add", "ADD A PET - CHOOSE A FRIEND"), ("solo", "SHOW ALL PETS" if p.solo else "ALL PETS VISIBLE"), ("rename", "RENAME " + p.name.upper()), ("personality", "PERSONALITY: " + p.temperament.upper()), ("bonds", "OUR FRIENDSHIPS")]
        for i, friend in enumerate(self.household.friends): entries.append(("select:%d" % i, "CARE FOR " + friend.name.upper()))
        if p.pet_slots < 4: entries.append(("slot", "UNLOCK SLOT %d - %d COINS" % (p.pet_slots + 1, SLOT_PRICES[p.pet_slots - 1])))
        entries.extend([("chat", "LET'S CHAT"), ("wrestle", "FRIENDLY PILLOW DUEL"), ("dance", "FAMILY DANCE")])
        self.overlay = ChoiceMenu(self.ui, "FAMILY %d/%d" % (len(self.household.friends) + 1, p.pet_slots), entries, self._family_action, self._close_overlay)

    def _select_friend(self, index):
        if self.household.select(index):
            self.brain = Brain(self.pet, self.world, self.fx, self._on_event)
            self.ui.button("follow").active = False
            self.overlay = None; self.dance_left = 0
            react(self.pet); self.save_now()

    def _family_action(self, key):
        p = self.pet
        if key == "slotadd":
            if len(self.household.friends) + 1 >= p.pet_slots:
                if p.pet_slots >= 4: return
                price = SLOT_PRICES[p.pet_slots - 1]
                if p.coins < price: self.ui.toast("NEED %d COINS FOR A SLOT" % price); return
                p.coins -= price; p.pet_slots += 1; self.save_now()
            self._family_action("add"); return
        if key == "personality":
            self.overlay = ChoiceMenu(self.ui, "A LITTLE PERSONALITY", [("trait:" + k, n + " - " + d) for k, (n, d, *_) in TRAITS.items()], self._family_action, self._family_menu)
            return
        if key.startswith("trait:"):
            set_trait(p, key.split(":")[1]); self.save_now(); self._family_menu(); return
        if key == "bonds":
            entries = [("back", f.name.upper() + ": " + bond_label(p.bonds.get(bond_key(p, f), {}).get("points", 0))) for f in self.household.friends]
            self.overlay = ChoiceMenu(self.ui, "GROWING TOGETHER", entries or [("back", "ADD A FRIEND TO GROW A FRIENDSHIP")], lambda _: self._family_menu(), self._family_menu)
            return
        if key.startswith("select:"): self._select_friend(int(key.split(":")[1])); return
        if key == "rename": self._open_profile(); return
        if key == "solo": p.solo = not p.solo
        elif key == "slot" and p.pet_slots < 4:
            price = SLOT_PRICES[p.pet_slots - 1]
            if p.coins < price: self.ui.toast("NOT ENOUGH COINS"); return
            p.coins -= price; p.pet_slots += 1
        elif key == "add":
            if len(self.household.friends) + 1 >= p.pet_slots:
                if p.pet_slots >= 4: self.ui.toast("YOUR FOUR-PET FAMILY IS FULL"); return
                self.overlay = ChoiceMenu(self.ui, "MAKE ROOM FOR A FRIEND", [("slotadd", "BUY SLOT %d - %d COINS" % (p.pet_slots + 1, SLOT_PRICES[p.pet_slots - 1])), ("back", "BACK - NO PURCHASE")], self._family_action, self._family_menu)
                return
            self.overlay = ChoiceMenu(self.ui, "CHOOSE A FRIEND", [(s, SPECIES[s]["name"] + " - UNLOCKED") for s in p.owned_species], self._add_friend, self._family_menu)
            return
        elif key in ("chat", "wrestle", "dance"):
            self.overlay = None
            if key == "dance": self.do_action("dance")
            else: self.household.socialize(key)
            return
        self.save_now(); self._family_menu()

    def _add_friend(self, species):
        if self.household.add(species): self.ui.toast("WELCOME HOME! SELECT THEM TO RENAME.")
        self.save_now(); self.overlay = None
        self.pet.say("OUR FAMILY IS GROWING!")

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
            if room in ROOM_PRICES and room not in pet.owned_rooms:
                if pet.coins < ROOM_PRICES[room]: self.ui.toast("NOT ENOUGH COINS"); return
                pet.coins -= ROOM_PRICES[room]
                pet.owned_rooms.append(room)
            if room in pet.owned_rooms:
                pet.room_theme = room
                apply_layout(self.world, pet)
                self.save_now()
                self.ui.toast(ROOMS[room][0] + " READY!")
                if isinstance(self.overlay, ChoiceMenu): self.overlay = None
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
        if self.tray: self.tray.poll()
        if self.paused: return
        self.t += dt
        self.voice_timer = max(0, self.voice_timer - dt)
        if self.session and not self.overlay:
            self.chatter_timer -= dt
            if self.chatter_timer <= 0:
                self.chatter_timer = 20 + 20 * (1 - self.pet.personality["friendliness"])
                if not self.pet.hidden and not (self.desktop and self.desktop.pets_hidden) and self.pet.anim.name not in ("sleep", "eat"):
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
                quiet_rest = self.settings.quiet and self.brain.state in (State.IDLE, State.SIT, State.WANDER) and self.dance_left <= 0
                if quiet_rest:
                    self.pet.anim.play("sleep" if self.pet.energy < 60 else "sit")
                elif self.dance_left > 0:
                    self.dance_left = max(0, self.dance_left - dt); self.pet.anim.play("dance")
                else: self.brain.update(dt, self._read_input(), self.follow_pt if self.brain.follow else None, mouse)
                for ev in self.pet.update(dt): self._on_event(ev)
                self.pet.tick_needs(dt, "sleep" if quiet_rest else self.brain.activity, self.brain.night)
                self.household.update(dt)
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
        self.world.draw_background(c, self.t, self.daynight, self.pet.room_theme if self.session else "classic")
        if self.session and self.pet.room_theme in ("garden", "starlight"):
            tint = pygame.Surface((W, BAR_Y - HUD_H), pygame.SRCALPHA)
            tint.fill((60, 180, 130, 35) if self.pet.room_theme == "garden" else (70, 80, 200, 45))
            c.blit(tint, (0, HUD_H))
            if self.pet.room_theme == "starlight":
                for x in range(35, W, 45): c.blit(self.assets.icons["star"], (x, 50 + (x % 3) * 8))
        if self.session:
            draw_decor(c, self.assets, self.pet)
            if not adventure(self.pet).get("find"):
                r = self.adventure_rect()
                c.blit(self.assets.icons["star"], r.topleft)
        if self.session:
            self.world.food.frames = self.assets.meals[self.pet.selected_food]
            self.world.active_toy = self.pet.selected_toy
        self.world.draw_objects(c, self.t, ([self.pet] + self.household.visible) if self.session else None, self.assets)
        self.fx.draw(c)
        self.world.draw_overlay(c, self.t, self.daynight)
        if self.session:
            self.ui.draw_bubble(c, self.pet)
            for friend in self.household.visible: self.ui.draw_bubble(c, friend)
            self.ui.draw_hud(c, self.pet)
            self.ui.draw_bar(c)
            self.ui.draw_overlays(c, self.brain.follow)
        else:
            self.ui.draw_panel(c, (0, 0, W, HUD_H))
            self.ui.draw_panel(c, (0, BAR_Y, W, H - BAR_Y))
        if self.overlay:
            self.overlay.draw(c)
        if self.paused:
            self.ui.draw_panel(c, (155, 5, 170, 20))
            self.ui.text(c, "PAUSED - TRAY TO RESUME", (240, 12), INK, anchor="midtop")
        self.fade.draw(c)

    def adventure_rect(self):
        a = adventure(self.pet)
        seed = sum(map(ord, a["date"]))
        return pygame.Rect(100 + (seed * 37) % 260, 178 + seed % 35, 14, 14)

    def _adventure_menu(self):
        a = adventure(self.pet)
        entries = [("hint", "FIND THE LOST STAR: %d/1" % a.get("find", 0)),
                   ("game", "FINISH FETCH / HURDLES: %d/1" % a.get("game", 0)),
                   ("cuddle", "THREE LITTLE CUDDLES: %d/3" % a.get("cuddle", 0)),
                   ("claim", "6 COINS COLLECTED" if a.get("claimed") else "CLAIM 6 COINS"),
                   ("quiet", "QUIET TIME: " + ("ON" if self.settings.quiet else "OFF"))]
        self.overlay = ChoiceMenu(self.ui, "TODAY'S LITTLE ADVENTURE", entries, self._adventure_action, self._close_overlay)

    def _adventure_action(self, key):
        if key == "claim":
            self.ui.toast("+6 COINS! SEE YOU TOMORROW." if claim_adventure(self.pet) else "FINISH ALL THREE. CLAIM ONCE PER DAY.")
            self.save_now(); self._adventure_menu()
        elif key == "game": self.do_action("game")
        elif key == "quiet": self.do_action("quiet"); self._adventure_menu()
        else:
            self._close_overlay()
            self.pet.say("A LITTLE GOLD STAR ON THE FLOOR!" if key == "hint" else "TAP ME OR A FRIEND FOR A CUDDLE!")

    def _tray_action(self, key):
        if key == "quit": self.running = False; return
        if not self.session: return
        if key == "pause": self.paused = not self.paused; self.save_now(); return
        self.paused = False
        if key == "room":
            if self.desktop: self.leave_desktop()
            return
        if key in ("rescue", "showhome", "showitems", "showpets", "showall", "hideall"):
            if not self.desktop: self.enter_desktop()
            if self.desktop: self.desktop.command(key)
        elif key == "quiet":
            if self.desktop: self.desktop.command(key)
            else: self.do_action(key)

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
        if self.tray: self.tray.close()
        if self.desktop: self.desktop.window.close()
        self.settings.save()
        pygame.quit()
