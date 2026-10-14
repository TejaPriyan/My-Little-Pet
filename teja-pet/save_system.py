"""Persistent pet data: atomic writes and tolerant loading of broken files."""
import json
import os
import random
import time

from config import SAVE_DIR, SAVE_PATH, SHOP_ITEMS, SPECIES, ACCESSORIES, ACHIEVEMENTS

PERSONALITY_KEYS = ("curiosity", "playfulness", "sleepiness", "friendliness")


def new_personality(rng=random):
    return {k: round(rng.uniform(0.25, 0.9), 2) for k in PERSONALITY_KEYS}


def clean_name(value, fallback):
    """The pixel font supports ASCII letters, numbers, spaces and hyphens."""
    if not isinstance(value, str):
        return fallback
    return "".join(c for c in value if c.isascii() and (c.isalnum() or c in " -")).strip()[:12] or fallback


def default_data(name="Teja", owner_name="Friend"):
    return {
        "version": 4,
        "species": "cat", "coat": 0, "owned_species": ["cat"],
        "room_theme": "classic", "owned_rooms": ["classic"],
        "daily": {}, "tutorial_seen": False,
        "pet_name": clean_name(name, "Mochi"),
        "owner_name": clean_name(owner_name, "Friend"),
        "level": 1,
        "experience": 0,
        "hunger": 80.0,
        "happiness": 85.0,
        "energy": 90.0,
        "position_x": 240.0,
        "position_y": 190.0,
        "personality": new_personality(),
        "coins": 20,
        "inventory": {"treat": 0, "squeaky": 0},
        "stats": {
            "total_feeds": 0,
            "total_plays": 0,
            "total_pettings": 0,
            "total_drinks": 0,
            "total_sleeps": 0,
            "games_played": 0,
            "high_score": 0,
            "distance_walked": 0.0,
            "time_played": 0.0,
            "treat_high_score": 0, "desktop_visits": 0,
        },
        "achievements": [],
        "equipped": {"hat": True},
        "last_saved_time": time.time(),
    }


def _num(v, lo, hi, default):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    if v != v:                       # NaN guard
        return default
    return max(lo, min(hi, v))


def sanitize(raw):
    """Validate untrusted JSON into a complete, well-typed save dict."""
    if not isinstance(raw, dict):
        return None
    d = default_data()
    d["pet_name"] = clean_name(raw.get("pet_name"), d["pet_name"])
    d["owner_name"] = clean_name(raw.get("owner_name"), "Friend")
    d["level"] = int(_num(raw.get("level"), 1, 999, 1))
    d["experience"] = int(_num(raw.get("experience"), 0, 10 ** 7, 0))
    d["hunger"] = _num(raw.get("hunger"), 0, 100, d["hunger"])
    d["happiness"] = _num(raw.get("happiness"), 0, 100, d["happiness"])
    d["energy"] = _num(raw.get("energy"), 0, 100, d["energy"])
    d["position_x"] = _num(raw.get("position_x"), 0, 480, d["position_x"])
    d["position_y"] = _num(raw.get("position_y"), 0, 270, d["position_y"])
    d["coins"] = int(_num(raw.get("coins"), 0, 10 ** 9, d["coins"]))
    d["last_saved_time"] = _num(raw.get("last_saved_time"), 0, 4e9, time.time())
    pers = raw.get("personality")
    if isinstance(pers, dict):
        for k in PERSONALITY_KEYS:
            d["personality"][k] = _num(pers.get(k), 0, 1, d["personality"][k])
    inv = raw.get("inventory")
    if isinstance(inv, dict):
        for k in inv:
            if k in SHOP_ITEMS or k in ACCESSORIES:
                d["inventory"][k] = int(_num(inv.get(k), 0, 999, 0))
    stats = raw.get("stats")
    if isinstance(stats, dict):
        for k, v in d["stats"].items():
            d["stats"][k] = _num(stats.get(k), 0, 10 ** 9, v)
    achs = raw.get("achievements")
    if isinstance(achs, (list, tuple)):
        d["achievements"] = [a for a in achs if isinstance(a, str) and a in ACHIEVEMENTS]
    eq = raw.get("equipped")
    if isinstance(eq, dict):
        head = eq.get("head") if "head" in eq else ("hat" if eq.get("hat") else None)
        d["equipped"] = {"head": head if isinstance(head, str) and head in ACCESSORIES and d["inventory"].get(head, 0) else None}
    species = raw.get("species")
    d["species"] = species if isinstance(species, str) and species in SPECIES else "cat"
    d["coat"] = int(_num(raw.get("coat"), 0, 2, 0))
    owned = raw.get("owned_species", ["cat"])
    d["owned_species"] = list(dict.fromkeys(["cat", d["species"]] +
        ([s for s in owned if isinstance(s, str) and s in SPECIES] if isinstance(owned, list) else [])))
    rooms = ("classic", "garden", "starlight")
    owned = raw.get("owned_rooms", ["classic"])
    d["owned_rooms"] = list(dict.fromkeys(["classic"] + ([r for r in owned if isinstance(r, str) and r in rooms] if isinstance(owned, list) else [])))
    theme = raw.get("room_theme")
    d["room_theme"] = theme if theme in d["owned_rooms"] else "classic"
    daily = raw.get("daily")
    if isinstance(daily, dict):
        d["daily"] = {"date": str(daily.get("date", ""))[:10], "feed": int(_num(daily.get("feed"), 0, 3, 0)),
                      "play": int(_num(daily.get("play"), 0, 2, 0)), "game": int(_num(daily.get("game"), 0, 1, 0)),
                      "claimed": bool(daily.get("claimed", False))}
    d["tutorial_seen"] = bool(raw.get("tutorial_seen", False))
    return d


class SaveSystem:
    def __init__(self, path=SAVE_PATH):
        self.path = path

    def exists(self):
        return os.path.isfile(self.path)

    def load(self):
        """Return a sanitized save dict, or None for a fresh start."""
        if not self.exists():
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = sanitize(json.load(f))
            if data is not None:
                return data
        except (OSError, ValueError):
            pass
        # Corrupted: keep a copy for inspection and start fresh.
        try:
            os.replace(self.path, self.path + ".corrupt")
        except OSError:
            pass
        return None

    def save(self, data):
        """Atomic write (temp file + replace) so a crash can't corrupt saves."""
        data = dict(data)
        data["last_saved_time"] = time.time()
        tmp = self.path + ".tmp"
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self.path)
            return True
        except OSError:
            return False

    def delete(self):
        for p in (self.path, self.path + ".tmp"):
            try:
                os.remove(p)
            except OSError:
                pass
