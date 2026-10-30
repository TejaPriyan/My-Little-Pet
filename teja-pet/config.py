"""Global constants for TEJA PET. Constants only - no logic lives here."""
import os
import sys

# ---------------------------------------------------------------- paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
SAVE_DIR = os.environ.get("MY_LITTLE_PET_SAVE_DIR") or (
    os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "MyLittlePet", "save")
    if getattr(sys, "frozen", False) else os.path.join(BASE_DIR, "save"))
SAVE_PATH = os.path.join(SAVE_DIR, "save_data.json")
SETTINGS_PATH = os.path.join(SAVE_DIR, "settings.json")

# ---------------------------------------------------------------- display
TITLE = "My Little Pet" + (" - " + os.environ['MY_LITTLE_PET_EDITION'] if os.environ.get('MY_LITTLE_PET_EDITION') else "")
W, H = 480, 270            # internal pixel-art resolution
START_SCALE = 2            # window opens at 960 x 540
HUD_H = 34                 # top panel height
BAR_Y = 244                # y of the bottom button bar
FLOOR_Y = 100              # y where the wall ends and the floor begins
FRAME = 24                 # pet sprite frame size (square)

# ---------------------------------------------------------------- colours
INK = (52, 40, 82)
CREAM = (255, 244, 230)
CREAM_DK = (232, 208, 190)
PINK = (255, 128, 164)
GOLD = (255, 205, 70)
WHITE = (255, 255, 255)
BAR_BG = (84, 64, 108)
C_HAPPY = (255, 112, 156)
C_HUNGER = (255, 168, 64)
C_ENERGY = (96, 206, 120)
C_XP = (120, 170, 255)

# ---------------------------------------------------------------- needs
# All rates are "points per second" on a 0-100 scale.
HUNGER_DECAY = 0.06          # 100 -> 0 in roughly half an hour
HAPPINESS_DECAY = 0.03
HUNGRY_EXTRA_DECAY = 0.04    # extra happiness loss while starving
ENERGY_IDLE = 0.015
ENERGY_WALK = 0.05
ENERGY_RUN = 0.12
ENERGY_SLEEP_GAIN = 2.2
NIGHT_ENERGY_FACTOR = 1.3    # pet tires a little faster at night
WAKE_ENERGY = 92

# ---------------------------------------------------------------- movement
WALK_SPEED = 36.0            # internal pixels per second
RUN_SPEED = 78.0
WALK_FPS = 8.0               # animation speed is independent of move speed
RUN_FPS = 12.0

# ---------------------------------------------------------------- actions
FEED_HUNGER = 20
FEED_HAPPY = 5
PLAY_HAPPY = 20
PLAY_ENERGY = 10
PET_HAPPY = 4
TREAT_BONUS = 15

XP_REWARDS = {"feed": 5, "play": 10, "pet": 3, "sleep": 5, "explore": 5}
COIN_REWARDS = {"feed": 0, "play": 1, "pet": 0, "sleep": 0, "explore": 0, "levelup": 8}
REWARD_COOLDOWNS = {"feed": 120, "play": 180, "pet": 120, "sleep": 300, "explore": 300}
SLOT_PRICES = (250, 600, 1000)
DAILY_COINS = 12
FOODS = {
    "kibble": {"name": "EVERYDAY BOWL", "price": 0, "hunger": 20, "happy": 3, "energy": 0},
    "berries": {"name": "BERRY BOWL", "price": 8, "hunger": 28, "happy": 10, "energy": 0},
    "fish": {"name": "FISH BITES", "price": 12, "hunger": 38, "happy": 8, "energy": 3},
    "greens": {"name": "GARDEN GREENS", "price": 10, "hunger": 32, "happy": 6, "energy": 8},
    "milk": {"name": "CREAMY PET MILK", "price": 8, "hunger": 18, "happy": 9, "energy": 6},
    "soup": {"name": "PUMPKIN SOUP", "price": 14, "hunger": 35, "happy": 8, "energy": 10},
    "feast": {"name": "PARTY PLATTER", "price": 24, "hunger": 55, "happy": 20, "energy": 12},
}
EXPLORE_DISTANCE = 600       # pixels walked for one "explore" reward

# ---------------------------------------------------------------- saving
AUTOSAVE_SECONDS = 30
OFFLINE_RATE = 0.1           # fraction of normal decay while the game is closed
OFFLINE_MAX_SECONDS = 12 * 3600
OFFLINE_HUNGER_FLOOR = 15
OFFLINE_HAPPINESS_FLOOR = 25

# ---------------------------------------------------------------- shop
SHOP_ITEMS = {
    "treat": {"name": "TREAT", "price": 10, "desc": "NEXT FEED +15 HUNGER", "repeatable": True},
    "squeaky": {"name": "SQUEAKY TOY", "price": 40, "desc": "PLAY GIVES +5 HAPPY", "repeatable": False},
    "blanket": {"name": "COZY BLANKET", "price": 60, "desc": "SLEEP RESTORES +25% ENERGY", "repeatable": False},
    "catnip": {"name": "JOY CANDY", "price": 25, "desc": "ZOOMIES & +35 HAPPY", "repeatable": True},
    "energy": {"name": "ENERGY SNACK", "price": 20, "desc": "INSTANT +30 ENERGY", "repeatable": True},
}

# ---------------------------------------------------------------- pets & style
SPECIES_ORDER = ("cat", "dog", "bunny", "fox", "dino", "tiger", "parrot")
SPECIES = {
    "cat": {"name": "KITTY", "price": 0, "desc": "CURIOUS & CUDDLY", "voice": "meow"},
    "dog": {"name": "PUPPY", "price": 160, "desc": "LOYAL & PLAYFUL", "voice": "woof"},
    "bunny": {"name": "BUNNY", "price": 200, "desc": "SOFT & BOUNCY", "voice": "squeak"},
    "fox": {"name": "FOX", "price": 260, "desc": "CLEVER & FLUFFY", "voice": "yip"},
    "dino": {"name": "DINO", "price": 450, "desc": "TINY ROARS, BIG HEART", "voice": "chirrup"},
    "tiger": {"name": "TIGER", "price": 650, "desc": "STRIPES & SASS", "voice": "roar"},
    "parrot": {"name": "PARROT", "price": 800, "desc": "CHATTY LITTLE DANCER", "voice": "chirp"},
}
# head accessories (one worn at a time). "hat" is the original Fancy Bow key.
ACCESSORY_ORDER = ("hat", "flower", "party", "crown")
ACCESSORIES = {
    "hat": {"name": "FANCY BOW", "price": 50},
    "flower": {"name": "FLOWER CLIP", "price": 35},
    "party": {"name": "PARTY HAT", "price": 45},
    "crown": {"name": "ROYAL CROWN", "price": 120},
}
VOICE_COOLDOWN = 6.0         # min seconds between spontaneous pet sounds

# ---------------------------------------------------------------- desktop mode
DESKTOP_KEY = (255, 0, 255)  # colour-key that becomes see-through on the desktop
DESKTOP_SCALES = (2, 3, 4)

# ---------------------------------------------------------------- achievements
ACHIEVEMENTS = {
    "first_feed": {"title": "FIRST MEAL", "desc": "Feed your pet once", "icon": "apple", "reward": 10},
    "first_play": {"title": "PLAYFUL", "desc": "Play with the toy ball", "icon": "ball", "reward": 10},
    "loved": {"title": "PURE LOVE", "desc": "Pet your friend 10 times", "icon": "heart", "reward": 20},
    "level_5": {"title": "GROWING UP", "desc": "Reach pet Level 5", "icon": "star", "reward": 25},
    "level_10": {"title": "BEST BUDDY", "desc": "Reach pet Level 10", "icon": "star", "reward": 50},
    "rich": {"title": "PIGGY BANK", "desc": "Hold 100 coins at once", "icon": "coin", "reward": 30},
    "night_owl": {"title": "NIGHT OWL", "desc": "Spend time at night", "icon": "moon", "reward": 15},
    "fashion": {"title": "FASHIONISTA", "desc": "Buy an accessory", "icon": "bow", "reward": 20},
    "bug_hunter": {"title": "BUG CATCHER", "desc": "Score 15+ in Catch the Bug", "icon": "spark", "reward": 30},
    "marathon": {"title": "MARATHON", "desc": "Walk 1500px exploring", "icon": "paw", "reward": 25},
    "treat_master": {"title": "SNACK ATTACK", "desc": "Score 20+ in Treat Drop", "icon": "pad", "reward": 30},
    "adopter": {"title": "PET PARENT", "desc": "Adopt a new species", "icon": "paw", "reward": 25},
    "desktop": {"title": "FREE ROAMER", "desc": "Try Desktop Mode", "icon": "desk", "reward": 15},
}

# ---------------------------------------------------------------- weather & environment
WEATHER_MODES = ("clear", "rain", "snow")

# ---------------------------------------------------------------- AI thresholds
AI_TIRED_THRESHOLD = 22.0
AI_HUNGRY_BEG_THRESHOLD = 28.0
AI_PLAY_ENERGY_MIN = 35.0
AI_REST_THRESHOLD = 45.0
AI_NIGHT_SLEEP_THRESHOLD = 75.0
AI_BORED_THRESHOLD = 40.0
AI_HUNGRY_CHAT = 35.0
AI_TIRED_CHAT = 30.0


def xp_needed(level: int) -> int:
    """XP required to go from `level` to `level + 1`."""
    return 40 + 20 * (level - 1)

