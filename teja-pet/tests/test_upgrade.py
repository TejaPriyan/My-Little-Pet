"""Upgrade regressions using REAL pygame with SDL's dummy driver.

Uses an isolated save folder. Does not touch the user's pet or settings.
"""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / ".runtime"), str(ROOT / "teja-pet")]
import pygame
import config

(ROOT / "review-temp").mkdir(exist_ok=True)
tmp = tempfile.TemporaryDirectory(dir=ROOT / "review-temp")
config.SAVE_DIR = tmp.name
config.SAVE_PATH = str(Path(tmp.name) / "save.json")
config.SETTINGS_PATH = str(Path(tmp.name) / "settings.json")
from game import Game
from save_system import default_data, sanitize, SaveSystem
from minigame import BugCatchGame, TreatDropGame
from menus import ShopMenu, Tutorial
from desktop import DesktopPet
from activities import record, unlock_rooms


g = Game()
g.start_session(default_data("Upgrade"), offline=False)
g.overlay = None
shots = ROOT / "upgrade-shots"
shots.mkdir(exist_ok=True)


def shot(name):
    g.draw()
    pygame.image.save(g.canvas, str(shots / (name + ".png")))


def test_rewards():
    p = g.pet
    p.achievements.clear(); p.coins = 0
    p.stats["total_feeds"] = 1
    g.check_achievements()
    assert p.coins == 10
    g.check_achievements()
    assert p.coins == 10, "achievement must pay exactly once"
    p.coins = 100; p.energy = 11
    p.achievements.update(config.ACHIEVEMENTS)
    g._buy("energy")
    assert p.energy == 41 and p.coins == 80 and p.inventory["energy"] == 0
    g._buy("catnip")
    assert p.zoomies > 0


def test_appearance_save_roundtrip():
    p = g.pet
    p.coins = 1000
    g._buy("species:fox"); g._buy("style:crown"); g._buy("coat")
    assert p.species == "fox" and p.coat == 1 and p.accessory == "crown"
    g.save_now()
    data = g.saves.load()
    assert data["species"] == "fox" and data["coat"] == 1
    assert data["equipped"]["head"] == "crown" and "fox" in data["owned_species"]
    g.start_session(data, offline=False)
    assert g.pet.accessory == "crown"
    bad = sanitize({"species": [], "owned_species": {}, "coat": "bad", "equipped": {"head": []}, "room_theme": []})
    assert bad["species"] == "cat" and bad["coat"] == 0 and bad["equipped"]["head"] is None
    old = sanitize({"inventory": {"hat": 1}, "equipped": {"hat": True}})
    assert old["equipped"]["head"] == "hat"


def test_weather():
    for weather in config.WEATHER_MODES:
        g.world.set_weather(weather); g.world.update(300)
        assert g.world.weather == weather
    g.world.set_weather("auto"); g.world.update(1)
    assert g.world.weather_override is None


def test_games():
    for cls in (BugCatchGame, TreatDropGame):
        p = g.pet; p.xp = p.xp_needed - 1
        game = cls(g.ui, p, g.audio, g.fx, g._on_minigame_finish)
        g.overlay = game
        game.score = 24
        previous_level = p.level
        game.update(31, (240, 210))
        assert game.state == "results" and p.level > previous_level
        assert p.stats[game.SCORE_KEY] >= 24
        before = (p.coins, p.xp, p.level)
        game._apply_rewards()
        assert before == (p.coins, p.xp, p.level), "collect twice must not pay twice"
        shot(cls.__name__ + "-results")
        g._on_minigame_finish()
        assert g.ui.banner is not None
    game = BugCatchGame(g.ui, g.pet, g.audio, g.fx, lambda: None)
    bug = game.bugs[0]; bug.x, bug.y = 100, 100
    game.on_click((100, 100)); score = game.score
    game.on_click((100, 100)); assert game.score == score
    treat = TreatDropGame(g.ui, g.pet, g.audio, g.fx, lambda: None)
    treat.score = 5; treat.drops = [[240, 218, 100, "thorn"]]
    treat.update(.05, (240, 200)); assert treat.score == 2
    treat.drops = [[240, 218, 100, "star"]]
    treat.update(.05, (240, 200)); assert treat.score == 5
    g.overlay = treat; shot("TreatDrop-playing")
    g.overlay = None


def test_shop_and_menus():
    for tab in range(3):
        menu = ShopMenu(g.ui, g.pet, g._buy, g._close_overlay)
        menu.tab = tab; g.overlay = menu
        for page in range((len(menu.keys) + 4) // 5):
            menu.page = page
            shot("shop-%d-%d" % (tab, page))
    g._open_settings(); shot("settings")
    g.show_help(); shot("tutorial")
    g.do_action("stats"); shot("journal")
    g.overlay.tab = "awards"
    for page in range(4):
        g.overlay.award_page = page; shot("awards-%d" % page)
    g.do_action("game"); shot("game-picker")
    g._pick_game("daily"); shot("daily")
    g.overlay = None


def test_daily_rooms():
    p = g.pet; p.daily = {}
    base = p.coins
    for kind in ("feed", "feed", "feed", "play", "play", "game"): record(p, kind)
    assert p.coins == base + 30
    record(p, "game"); assert p.coins == base + 30
    p.level = 5; unlock_rooms(p)
    assert set(p.owned_rooms) == {"classic", "garden", "starlight"}
    for key in p.owned_rooms:
        g._buy("room:" + key); shot("room-" + key)
    g.save_now(); assert g.saves.load()["daily"]["claimed"]


def test_desktop_logic():
    p = g.pet
    room = (p.x, p.y)
    class Window:
        def __init__(self): self.canvas = pygame.Surface((640, 360)); self.pos = (240, 200)
        def mouse(self): return self.pos
        def present(self): pass
        def close(self): pass
    window = Window(); desk = DesktopPet(g, window); g.desktop = desk
    p.energy = 20
    desk.command("home")
    for _ in range(500): desk.update(.05)
    assert desk.state == "sleep" and p.hidden, (desk.state, p.energy)
    g.save_now()
    data = g.saves.load()
    assert (data["position_x"], data["position_y"]) == (round(room[0], 1), round(room[1], 1))
    desk.draw(); pygame.image.save(window.canvas, str(shots / "desktop-sleep.png"))
    for _ in range(900): desk.update(.05)
    assert not p.hidden and p.energy > 90
    p.hunger = 30; desk.command("feed")
    for _ in range(350): desk.update(.05)
    assert p.hunger > 45
    desk.wake(); desk.target = None
    p.x, p.y = 180, 160
    window.pos = (p.x, p.y - 10)
    desk.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))
    window.pos = (320, 180); desk.update(.05)
    assert p.carried
    desk.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1))
    assert not p.carried and abs(p.x - 320) < 1
    # A fast native drag can queue down/move/up before the next animation tick.
    desk.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(p.x, p.y - 10)))
    desk.event(pygame.event.Event(pygame.MOUSEMOTION, pos=(420, 130)))
    desk.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(420, 130)))
    assert (p.x, p.y) == (420, 142) and not p.carried
    desk.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3))
    assert desk.menu is not None
    desk.draw(); pygame.image.save(window.canvas, str(shots / "desktop-menu.png"))
    desk.restore(); g.desktop = None
    assert (p.x, p.y) == room


def test_assets_and_sounds():
    assert not g.assets.fallbacks, g.assets.fallbacks
    import audio
    for name in audio.SFX + ("music",): assert audio.wav_file(name).read(4) == b"RIFF"
    for species in config.SPECIES_ORDER:
        for coat in range(3):
            g.pet.set_look(species, coat)
            for clip in g.pet.anim.clips:
                g.pet.anim.play(clip); g.pet.update(.05); g.pet.draw(g.canvas, g.assets)


if __name__ == "__main__":
    try:
        for name, fn in list(globals().items()):
            if name.startswith("test_"):
                fn(); print("PASS", name, flush=True)
    finally:
        g.shutdown()
        tmp.cleanup()
