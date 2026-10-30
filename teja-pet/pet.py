"""The pet entity: stats, personality, progression and animation state."""
import random
import math
from life import identity, temperament, set_trait
from economy import allowance

import pygame

from config import (FRAME, HUNGER_DECAY, HAPPINESS_DECAY, HUNGRY_EXTRA_DECAY, ENERGY_IDLE,
                    ENERGY_WALK, ENERGY_RUN, ENERGY_SLEEP_GAIN, NIGHT_ENERGY_FACTOR,
                    XP_REWARDS, COIN_REWARDS, OFFLINE_RATE, OFFLINE_MAX_SECONDS,
                    OFFLINE_HUNGER_FLOOR, OFFLINE_HAPPINESS_FLOOR, SPECIES, ACCESSORIES, xp_needed)
from utils import clamp


class Animator:
    """Plays a Clip. Frame rate is independent of movement speed."""

    def __init__(self, clips):
        self.clips = clips
        self.name = None
        self.t = 0.0
        self.index = 0
        self.speed = 1.0
        self.transition = 0.0

    def play(self, name, speed=1.0):
        if name not in self.clips:
            name = "idle"
        if name != self.name:
            self.name, self.t, self.index = name, 0.0, 0
            self.transition = .18
        self.speed = speed

    def set_clips(self, clips):
        self.clips = clips
        self.index = 0 if self.name not in clips else self.index
        if self.name not in clips:
            self.name = "idle"

    def update(self, dt):
        self.transition = max(0, self.transition - dt)
        clip = self.clips[self.name]
        self.t += dt * clip.fps * self.speed
        new = int(self.t) % len(clip.frames)
        changed = new != self.index
        self.index = new
        return changed

    def frame(self, blink=False):
        clip = self.clips[self.name]
        frames = clip.blink if (blink and clip.blink) else clip.frames
        return frames[self.index % len(frames)]

    def anchor(self):
        clip = self.clips[self.name]
        return clip.anchors[self.index % len(clip.anchors)]


class Pet:
    def __init__(self, assets, data):
        self.assets = assets
        self.name = data["pet_name"]
        self.pet_id = identity(data.get("pet_id"))
        self.bonds = dict(data.get("bonds", {}))
        self.adventure = dict(data.get("adventure", {}))
        self.owned_toys = list(data.get("owned_toys", ["ball"]))
        self.selected_toy = data.get("selected_toy", "ball")
        self.owned_decor = list(data.get("owned_decor", ["bed", "toy"]))
        self.room_layout = dict(data.get("room_layout", {}))
        self.room_hidden = list(data.get("room_hidden", []))
        self.owner_name = data.get("owner_name", "Friend")
        self.level = data["level"]
        self.xp = data["experience"]
        self.hunger = data["hunger"]          # 100 = full, 0 = starving
        self.happiness = data["happiness"]
        self.energy = data["energy"]
        self.coins = data["coins"]
        self.companions = list(data.get("companions", []))
        self.pet_slots = data.get("pet_slots", 1)
        self.solo = data.get("solo", False)
        self.pantry = dict(data.get("pantry", {}))
        self.selected_food = data.get("selected_food", "kibble")
        self.reward_times = dict(data.get("reward_times", {}))
        self.arcade = dict(data.get("arcade", {}))
        self.desktop_layout = dict(data.get("desktop_layout", {}))
        self.daily = dict(data.get("daily", {}))
        self.tutorial_seen = data.get("tutorial_seen", False)
        self.room_theme = data.get("room_theme", "classic")
        self.owned_rooms = list(data.get("owned_rooms", ["classic"]))
        self.zoomies = 0.0
        self._stretch_cd = 18.0
        self._stretch_left = 0.0
        self._stretch_anim = None
        self.personality = dict(data["personality"])
        self.temperament = data.get("temperament", temperament(self.personality))
        if "temperament" in data: set_trait(self, self.temperament)
        self.inventory = dict(data.get("inventory", {}))
        self.stats = {
            "total_feeds": 0,
            "total_plays": 0,
            "total_pettings": 0,
            "total_drinks": 0,
            "total_sleeps": 0,
            "games_played": 0,
            "high_score": 0,
            "distance_walked": 0.0,
            "time_played": 0.0,
        }
        if "stats" in data and isinstance(data["stats"], dict):
            self.stats.update(data["stats"])
        self.achievements = set(data.get("achievements", []))
        self.equipped = dict(data.get("equipped", {}))
        self.species = data.get("species", "cat") if data.get("species") in SPECIES else "cat"
        self.coat = int(data.get("coat", 0))
        owned = [s for s in data.get("owned_species", ["cat"]) if s in SPECIES]
        self.owned_species = owned or ["cat"]
        if self.species not in self.owned_species:
            self.owned_species.append(self.species)
        # migrate the old {"hat": True} flag into the single head slot
        head = self.equipped.get("head")
        if head is None and "head" not in self.equipped:
            head = "hat" if (self.inventory.get("hat", 0) > 0 and self.equipped.get("hat", True)) else None
        self.equipped = {"head": head if head in ACCESSORIES else None}
        self.x = float(data["position_x"])
        self.y = float(data["position_y"])
        self.z = 0.0                          # height above ground (hops)
        self.facing = "down"
        self.moving = False
        self.running = False
        self.on_bed = False
        self.hidden = False                   # True while tucked inside the desktop house
        self.carried = False                  # being dragged around by the mouse
        self.anim = Animator(assets.pet_clips(self.species, self.coat))
        self.anim.play("idle")
        self._blink_cd = 3.0
        self._blink_left = 0.0
        self._flip_cache = {}
        self.bubble_text = ""
        self.bubble_t = 0.0
        self.bubble_dur = 1.0

    # ---------------------------------------------------------------- state
    @property
    def sort_y(self):
        return self.y + (200 if self.on_bed else 0)

    @property
    def xp_needed(self):
        return xp_needed(self.level)

    @property
    def voice(self):
        return SPECIES[self.species]["voice"]

    @property
    def accessory(self):
        return self.equipped.get("head")

    def set_look(self, species=None, coat=None):
        """Change species and/or coat colour; swaps the animation set live."""
        if species is not None and species in SPECIES:
            if species != self.species:
                self.coat = 0
            self.species = species
        if coat is not None:
            self.coat = coat
        clips = self.assets.pet_clips(self.species, self.coat)
        self.coat = max(0, min(2, self.coat))
        self._flip_cache.clear()
        self.anim.set_clips(clips)
        self._stretch_anim = None

    def gain_level_rewards(self, xp):
        """Add raw XP (mini-games). Returns levels gained."""
        self.xp += xp
        levels = 0
        while self.xp >= self.xp_needed and self.level < 999:
            self.xp -= self.xp_needed
            self.level += 1
            self.coins += COIN_REWARDS["levelup"]
            levels += 1
        return levels

    @property
    def mood(self):
        if self.happiness < 25 or self.hunger < 15:
            return "sad"
        if self.energy < 25:
            return "sleepy"
        if self.happiness > 75 and self.hunger > 40:
            return "happy"
        return "ok"

    def say(self, text, dur=2.6):
        self.bubble_text, self.bubble_t, self.bubble_dur = text, dur, dur

    def face_vector(self, dx, dy):
        if not dx and not dy:
            return
        ax, ay = abs(dx), abs(dy)
        horiz = "right" if dx > 0 else "left"
        vert = "down" if dy > 0 else "up"
        if ax > ay * 1.15:
            self.facing = horiz
        elif ay > ax * 1.15:
            self.facing = vert
        elif self.facing not in (horiz, vert):
            self.facing = horiz               # diagonal: keep current facing if valid

    # ---------------------------------------------------------------- needs
    def tick_needs(self, dt, activity, night):
        sleeping = activity == "sleep"
        self.hunger -= HUNGER_DECAY * dt * (0.5 if sleeping else 1.0)
        self.happiness -= HAPPINESS_DECAY * dt
        if self.hunger < 20:
            self.happiness -= HUNGRY_EXTRA_DECAY * dt
        if sleeping:
            boost = 1.25 if self.inventory.get("blanket", 0) > 0 else 1.0
            self.energy += ENERGY_SLEEP_GAIN * dt * boost
        else:
            rate = {"run": ENERGY_RUN, "walk": ENERGY_WALK}.get(activity, ENERGY_IDLE)
            self.energy -= rate * dt * (NIGHT_ENERGY_FACTOR if night else 1.0)
        self.hunger = clamp(self.hunger)
        self.happiness = clamp(self.happiness)
        self.energy = clamp(self.energy)

    def apply_offline(self, seconds):
        """Age needs for time spent with the game closed (gentle, with floors)."""
        seconds = max(0.0, min(float(seconds), OFFLINE_MAX_SECONDS))
        if seconds < 30:
            return 0.0
        h = self.hunger - HUNGER_DECAY * seconds * OFFLINE_RATE
        self.hunger = clamp(max(h, min(self.hunger, OFFLINE_HUNGER_FLOOR)))
        a = self.happiness - HAPPINESS_DECAY * seconds * OFFLINE_RATE
        self.happiness = clamp(max(a, min(self.happiness, OFFLINE_HAPPINESS_FLOOR)))
        self.energy = clamp(self.energy + 0.02 * seconds)          # rested while away
        return seconds

    # ---------------------------------------------------------------- progress
    def gain(self, kind):
        """Award XP + coins for an action. Returns the number of levels gained."""
        if not allowance(self, kind):
            return 0
        self.xp += XP_REWARDS.get(kind, 0)
        self.coins += COIN_REWARDS.get(kind, 0)
        levels = 0
        while self.xp >= self.xp_needed and self.level < 999:
            self.xp -= self.xp_needed
            self.level += 1
            self.coins += COIN_REWARDS["levelup"]
            levels += 1
        return levels

    # ---------------------------------------------------------------- update
    def update(self, dt):
        """Advance animation. Returns a list of animation events (e.g. 'step')."""
        self.stats["time_played"] += dt
        self.zoomies = max(0, self.zoomies - dt)
        if self.anim.name in ("idle", "sit") and not self.carried:
            self._stretch_cd -= dt
            if self._stretch_cd <= 0:
                self._stretch_left = 1.9
                self._stretch_cd = random.uniform(18, 35)
                self._stretch_anim = Animator(self.anim.clips)
                self._stretch_anim.play("stretch")
            if self._stretch_left > 0 and self._stretch_anim:
                self._stretch_left -= dt
                self._stretch_anim.update(dt)
        else:
            self._stretch_left = 0
        events = []
        changed = self.anim.update(dt)
        if changed and self.anim.name.startswith("walk_") and self.anim.index in (1, 3):
            events.append("step")
        self._blink_cd -= dt
        if self._blink_cd <= 0:
            self._blink_left, self._blink_cd = 0.13, random.uniform(2.0, 5.0)
        self._blink_left -= dt
        self.bubble_t = max(0.0, self.bubble_t - dt)
        return events

    def frame(self):
        if self._stretch_left > 0 and self._stretch_anim:
            return self._stretch_anim.frame()
        img = self.anim.frame(self._blink_left > 0)
        if self.facing == "left" and self.anim.name == "eat":
            key = id(img)
            flipped = self._flip_cache.get(key)
            if flipped is None:
                flipped = self._flip_cache[key] = pygame.transform.flip(img, True, False)
            return flipped
        return img

    def draw(self, surf, assets, shadow=True):
        if self.hidden:
            return
        x, y = int(round(self.x)), int(round(self.y))
        if shadow and not self.on_bed and not self.carried:
            surf.blit(assets.shadow, (x - 8, y - 4))
        top = y - 22 - int(round(self.z))
        # A small anticipation dip keeps the silhouette crisp on transparent desktops.
        if not self.carried and not self.anim.name.startswith("walk_"):
            top += round(2 * math.sin(math.pi * self.anim.transition / .18))
        left = x - FRAME // 2
        surf.blit(self.frame(), (left, top))
        acc = self.accessory
        if acc and acc in assets.accessories:
            img = assets.accessories[acc]
            ax, ay = (self._stretch_anim if self._stretch_left > 0 and self._stretch_anim else self.anim).anchor()
            if self.facing == "left" and self.anim.name == "eat":
                ax = FRAME - ax
            w, h = img.get_size()
            surf.blit(img, (left + ax - w // 2, top + ay - h + 2))

    def rect(self):
        """Screen-space hit box of the sprite."""
        return pygame.Rect(int(self.x) - 12, int(self.y) - 22 - int(self.z), 24, 24)

    # ---------------------------------------------------------------- save
    def to_dict(self):
        return {
            "version": 6, "pet_name": self.name, "owner_name": self.owner_name, "level": self.level, "experience": self.xp,
            "pet_id": self.pet_id, "temperament": self.temperament, "bonds": self.bonds, "adventure": self.adventure,
            "owned_toys": self.owned_toys, "selected_toy": self.selected_toy,
            "owned_decor": self.owned_decor, "room_layout": self.room_layout, "room_hidden": self.room_hidden,
            "hunger": round(self.hunger, 2), "happiness": round(self.happiness, 2),
            "energy": round(self.energy, 2), "position_x": round(self.x, 1),
            "position_y": round(self.y, 1), "personality": self.personality,
            "coins": self.coins, "inventory": self.inventory,
            "stats": self.stats, "achievements": list(self.achievements),
            "equipped": self.equipped, "species": self.species, "coat": self.coat,
            "owned_species": list(self.owned_species),
            "daily": self.daily, "tutorial_seen": self.tutorial_seen,
            "room_theme": self.room_theme, "owned_rooms": list(self.owned_rooms),
            "companions": self.companions, "pet_slots": self.pet_slots, "solo": self.solo,
            "pantry": self.pantry, "selected_food": self.selected_food,
            "reward_times": self.reward_times, "arcade": self.arcade, "desktop_layout": self.desktop_layout,
        }

