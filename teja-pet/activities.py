"""Daily care goals and room unlocks; local dates, no network or account."""
from datetime import date

GOALS = {"feed": 3, "play": 2, "game": 1}
ROOMS = {"classic": ("COZY ROOM", 1), "garden": ("GARDEN ROOM", 3), "starlight": ("STAR ROOM", 5)}


def refresh(pet):
    today = date.today().isoformat()
    if pet.daily.get("date") != today:
        pet.daily = {"date": today, "feed": 0, "play": 0, "game": 0, "claimed": False}


def record(pet, kind):
    refresh(pet)
    if kind in GOALS:
        pet.daily[kind] = min(GOALS[kind], pet.daily.get(kind, 0) + 1)
    if not pet.daily.get("claimed") and all(pet.daily.get(k, 0) >= n for k, n in GOALS.items()):
        pet.daily["claimed"] = True
        pet.coins += 30
        return True
    return False


def unlock_rooms(pet):
    unlocked = []
    for key, (_, level) in ROOMS.items():
        if pet.level >= level and key not in pet.owned_rooms:
            pet.owned_rooms.append(key)
            unlocked.append(key)
    return unlocked
