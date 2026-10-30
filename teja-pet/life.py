"""Persistent personalities, friendships and small daily adventures."""
import math
import time
import uuid
from datetime import date

TRAITS = {
    "playful": ("PLAYFUL", "BALLS, ZOOMIES AND LITTLE DANCES", .85, .3, .75),
    "shy": ("SHY", "GENTLE STEPS AND QUIET HELLOS", .35, .45, .3),
    "sleepy": ("SLEEPY", "SLOW MORNINGS AND COZY NAPS", .3, .85, .6),
    "curious": ("CURIOUS", "ALWAYS READY TO EXPLORE", .65, .4, .65),
}
from furniture import BASE_DECOR, DECOR


def number(value, low, high, fallback=0):
    if not isinstance(value, (int, float)) or not math.isfinite(value): return fallback
    return max(low, min(high, value))


def identity(value=None):
    return value if isinstance(value, str) and len(value) == 32 and all(c in "0123456789abcdef" for c in value) else uuid.uuid4().hex


def temperament(personality):
    if personality.get("sleepiness", 0) > .72: return "sleepy"
    if personality.get("friendliness", 1) < .4: return "shy"
    return "playful" if personality.get("playfulness", 0) > .6 else "curious"


def set_trait(pet, key):
    if key not in TRAITS: return False
    pet.temperament = key
    _, _, play, sleep, friendly = TRAITS[key]
    pet.personality.update(playfulness=play, sleepiness=sleep, friendliness=friendly,
                           curiosity=.9 if key == "curious" else .45)
    return True


def bond_key(a, b):
    return ":".join(sorted((a.pet_id, b.pet_id)))


def bond_label(points):
    return "BEST FRIENDS" if points >= 60 else "BUDDIES" if points >= 25 else "GETTING TO KNOW YOU"


def bond(pet, a, b, now=None):
    now = time.time() if now is None else now
    key = bond_key(a, b)
    entry = pet.bonds.setdefault(key, {"points": 0, "next": 0})
    if now >= entry["next"]:
        entry["points"] = min(100, entry["points"] + 2)
        entry["next"] = now + 60
    return entry["points"]


def adventure(pet, now=None):
    today = date.fromtimestamp(time.time() if now is None else now).isoformat()
    if pet.adventure.get("date") != today:
        pet.adventure = {"date": today, "find": 0, "game": 0, "cuddle": 0, "claimed": False}
    return pet.adventure


def record_adventure(pet, kind, now=None):
    a = adventure(pet, now)
    limit = {"find": 1, "game": 1, "cuddle": 3}.get(kind)
    if limit: a[kind] = min(limit, a.get(kind, 0) + 1)


def claim_adventure(pet, now=None):
    a = adventure(pet, now)
    if a.get("claimed") or a.get("find", 0) < 1 or a.get("game", 0) < 1 or a.get("cuddle", 0) < 3: return False
    a["claimed"] = True
    pet.coins += 6
    return True


def sanitize_life(raw, data):
    from supplies import TOYS
    owned_toys = raw.get("owned_toys", [])
    data["owned_toys"] = list(dict.fromkeys(["ball"] + ([k for k in owned_toys if isinstance(k, str) and k in TOYS] if isinstance(owned_toys, list) else [])))
    data["selected_toy"] = raw.get("selected_toy") if raw.get("selected_toy") in data["owned_toys"] else "ball"
    data["pet_id"] = identity(raw.get("pet_id"))
    trait = raw.get("temperament")
    data["temperament"] = trait if isinstance(trait, str) and trait in TRAITS else temperament(data["personality"])
    seen = {data["pet_id"]}
    sources = raw.get("companions", [])
    sources = [r for r in sources if isinstance(r, dict) and r.get("species") in data["owned_species"]] if isinstance(sources, list) else []
    for i, friend in enumerate(data["companions"]):
        source = sources[i] if i < len(sources) else {}
        uid = identity(source.get("pet_id"))
        if uid in seen: uid = identity()
        seen.add(uid)
        friend["pet_id"] = uid
        trait = source.get("temperament")
        friend["temperament"] = trait if isinstance(trait, str) and trait in TRAITS else "playful"
    data["bonds"] = {}
    raw_bonds = raw.get("bonds", {})
    if isinstance(raw_bonds, dict):
        for key, value in raw_bonds.items():
            ids = key.split(":")
            if len(ids) == 2 and ids[0] != ids[1] and all(i in seen for i in ids) and isinstance(value, dict):
                data["bonds"][key] = {"points": int(number(value.get("points"), 0, 100)), "next": number(value.get("next"), 0, time.time() + 60)}
    a = raw.get("adventure", {})
    data["adventure"] = {"date": str(a.get("date", ""))[:10], "claimed": a.get("claimed") is True,
                         **{k: int(number(a.get(k), 0, n)) for k, n in (("find", 1), ("game", 1), ("cuddle", 3))}} if isinstance(a, dict) else {}
    owned = raw.get("owned_decor", [])
    data["owned_decor"] = list(dict.fromkeys(list(BASE_DECOR) + ([k for k in owned if isinstance(k, str) and k in DECOR] if isinstance(owned, list) else [])))
    layout = raw.get("room_layout", {})
    data["room_layout"] = {}
    if isinstance(layout, dict):
        for key, xy in layout.items():
            if key in data["owned_decor"] and isinstance(xy, list) and len(xy) == 2:
                data["room_layout"][key] = [number(xy[0], 14, 448, 200), number(xy[1], 100, 224, 170)]
    hidden = raw.get("room_hidden", [])
    data["room_hidden"] = list(dict.fromkeys(k for k in hidden if isinstance(k, str) and k in DECOR)) if isinstance(hidden, list) else []
    desktop = raw.get("desktop_layout", {})
    if isinstance(desktop, dict):
        data['desktop_layout']['items_hidden'] = desktop.get('items_hidden') is True
        data['desktop_layout']['pets_hidden'] = desktop.get('pets_hidden') is True
        items = desktop.get("furniture", {})
        data["desktop_layout"]["furniture"] = {k: [number(xy[0], 0, 1, .5), number(xy[1], 0, 1, .5)]
            for k, xy in items.items() if k in data["owned_decor"] and k not in ("food", "water", "toy")
            and isinstance(xy, list) and len(xy) == 2} if isinstance(items, dict) else {}
        away = desktop.get("put_away", [])
        data["desktop_layout"]["put_away"] = [k for k in ("home", "food", "water", "ball") if k in away] if isinstance(away, list) else []
