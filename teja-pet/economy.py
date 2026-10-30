"""Shared household rewards, food pantry and arcade lives. No network payments."""
import time
from datetime import date
from config import FOODS, REWARD_COOLDOWNS

LIFE_SECONDS = 1800
MAX_LIVES = 3
GAME_DAILY_CAP = 40


def allowance(pet, kind, now=None):
    now = time.time() if now is None else now
    if now < pet.reward_times.get(kind, 0):
        return False
    pet.reward_times[kind] = now + REWARD_COOLDOWNS.get(kind, 180)
    return True


def meal(pet):
    key = pet.selected_food
    if key not in FOODS or (key != "kibble" and pet.pantry.get(key, 0) < 1):
        key = "kibble"
    if key != "kibble":
        pet.pantry[key] -= 1
    food = FOODS[key]
    bonus = 15 if pet.inventory.get("treat", 0) else 0
    if bonus:
        pet.inventory["treat"] -= 1
    pet.hunger = min(100, pet.hunger + food["hunger"] + bonus)
    pet.happiness = min(100, pet.happiness + food["happy"])
    pet.energy = min(100, pet.energy + food["energy"])
    if key != "kibble" and pet.pantry.get(key, 0) == 0:
        pet.selected_food = "kibble"
    return food["hunger"] + bonus


def refresh_arcade(pet, now=None):
    now = time.time() if now is None else now
    a = pet.arcade
    a.setdefault("lives", MAX_LIVES)
    a.setdefault("refill_at", now)
    # A clock correction never creates extra lives.
    a["refill_at"] = min(now, a["refill_at"])
    if a["lives"] >= MAX_LIVES:
        a["refill_at"] = now
    else:
        count = int(max(0, now - a["refill_at"]) // LIFE_SECONDS)
        a["lives"] = min(MAX_LIVES, a["lives"] + count)
        a["refill_at"] += count * LIFE_SECONDS
    today = date.fromtimestamp(now).isoformat()
    if a.get("date") != today:
        a.update(date=today, earned=0)
    return a


def start_round(pet, now=None):
    a = refresh_arcade(pet, now)
    if a["lives"] <= 0:
        return False  # Practice is always available.
    a["lives"] -= 1
    return True


def game_reward(pet, score, completed, paid, now=None):
    a = refresh_arcade(pet, now)
    if not completed or not paid:
        return 0, 0, 0
    points = max(0, int(score))
    coins = min(8, points // 4, max(0, GAME_DAILY_CAP - a["earned"]))
    a["earned"] += coins
    pet.coins += coins
    xp = min(18, points)
    return coins, xp, pet.gain_level_rewards(xp)
