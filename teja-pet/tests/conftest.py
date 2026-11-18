"""Isolate sys.modules, os.environ, sys.path, and pygame state between test modules."""
import os
import sys
import pytest

_TEJA_MODULES = frozenset({
    "activities", "ai", "assets", "audio", "config", "decorating", "desktop",
    "desktop_furniture", "desktop_pet", "desktop_render", "display", "economy",
    "effects", "fake_pygame", "furniture", "game", "household", "instance",
    "life", "main", "menus", "minigame", "pet", "pet_games", "petart",
    "pixelfont", "playful", "plus_main", "rooms", "save_system", "settings",
    "sprites", "supplies", "supply_menu", "tray", "ui", "utils", "world",
})


def _clear_teja_modules():
    for name in list(sys.modules):
        if name in _TEJA_MODULES:
            sys.modules.pop(name, None)


def _is_real_pygame(mod):
    return mod is not None and bool(getattr(mod, "__file__", None))


@pytest.fixture(scope="module", autouse=True)
def _isolate_test_module():
    saved_env = os.environ.copy()
    saved_path = sys.path[:]
    saved_pygame = sys.modules.get("pygame")
    _clear_teja_modules()
    try:
        yield
    finally:
        pg = sys.modules.get("pygame")
        if _is_real_pygame(pg) and hasattr(pg, "quit"):
            try:
                pg.quit()
            except Exception:
                pass
        _clear_teja_modules()
        if _is_real_pygame(saved_pygame):
            sys.modules["pygame"] = saved_pygame
        elif _is_real_pygame(pg):
            # Keep real pygame cached once imported so C extensions never partially re-import.
            sys.modules["pygame"] = pg
        else:
            sys.modules.pop("pygame", None)
        os.environ.clear()
        os.environ.update(saved_env)
        sys.path[:] = saved_path
