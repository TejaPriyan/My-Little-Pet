"""Tests for the new features: mini-game, achievements, weather, expanded shop, and stats."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import fake_pygame
pg = fake_pygame.install()
H = pg._harness

import config
import game
from minigame import BugCatchGame, Bug
from save_system import SaveSystem, default_data, sanitize
from world import World, DayNight


def test_shop_new_items():
    data = default_data("TestPet")
    data["coins"] = 200
    save_sys = SaveSystem()
    sanitized = sanitize(data)
    assert "treat" in sanitized["inventory"]
    assert "stats" in sanitized
    assert "achievements" in sanitized


def test_weather_system():
    # Test weather states and transitions
    from assets import Assets
    assets = Assets()
    world = World(assets)
    assert world.weather in config.WEATHER_MODES
    world.set_weather("rain")
    assert world.weather == "rain"
    world.update(0.1)
    assert len(world.rain_drops) > 0
    world.set_weather("snow")
    assert world.weather == "snow"
    world.update(0.1)
    assert len(world.snow_flakes) > 0


def test_minigame_mechanics():
    from assets import Assets
    from ui import UI
    from audio import Audio
    from effects import Effects
    from pet import Pet
    from pixelfont import PixelFont
    from settings import Settings

    assets = Assets()
    font = PixelFont()
    ui = UI(assets, font)
    settings = Settings.load()
    audio = Audio(settings)
    fx = Effects(assets, font)
    pet = Pet(assets, default_data("GamerPet"))

    finished = [False]
    def on_done():
        finished[0] = True

    mg = BugCatchGame(ui, pet, audio, fx, on_done)
    assert mg.state == "playing"
    assert len(mg.bugs) > 0

    # Test clicking a bug
    first_bug = mg.bugs[0]
    mg.on_click((first_bug.x, first_bug.y))
    assert mg.score > 0
    assert mg.combo >= 2

    # Advance time to results
    mg.update(31.0, (100, 100))
    assert mg.state == "results"
    assert pet.stats["games_played"] >= 1
    assert pet.stats["high_score"] >= mg.score

    # Click collect
    mg.on_click((mg.collect_btn.centerx, mg.collect_btn.centery))
    assert finished[0] is True


def test_achievements_unlock():
    from assets import Assets
    from pet import Pet
    assets = Assets()
    pet = Pet(assets, default_data("HeroPet"))

    # Initially empty
    assert len(pet.achievements) == 0

    # Simulate feeding and stats update
    pet.stats["total_feeds"] = 1
    pet.stats["total_plays"] = 1
    pet.stats["total_pettings"] = 10
    pet.stats["distance_walked"] = 2000.0

    # Verify achievement keys exist in config
    for k in ("first_feed", "first_play", "loved", "marathon"):
        assert k in config.ACHIEVEMENTS

    # Simulate unlock
    pet.achievements.add("first_feed")
    d = pet.to_dict()
    assert "first_feed" in d["achievements"]
    assert d["stats"]["total_feeds"] == 1


if __name__ == "__main__":
    test_shop_new_items()
    print("PASS  test_shop_new_items")
    test_weather_system()
    print("PASS  test_weather_system")
    test_minigame_mechanics()
    print("PASS  test_minigame_mechanics")
    test_achievements_unlock()
    print("PASS  test_achievements_unlock")
    print("\nALL NEW FEATURE TESTS PASSED")
