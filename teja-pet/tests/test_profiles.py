"""Profile editing must preserve progress; old saves must still work."""
import os
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / '.runtime'), str(ROOT / 'teja-pet')]
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
(ROOT / 'review-temp').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=ROOT / 'review-temp') as temp:
    os.environ['MY_LITTLE_PET_SAVE_DIR'] = temp
    import pygame
    from save_system import default_data, sanitize
    from game import Game
    from instance import SingleInstance
    assert sanitize({'pet_name':'Teja'})['owner_name'] == 'Friend'
    assert sanitize({'owner_name': [], 'pet_name': None})['owner_name'] == 'Friend'
    g = Game()
    menu = g.overlay
    for letter in 'Mochi': menu.on_key(pygame.event.Event(pygame.KEYDOWN,key=ord(letter.lower()),unicode=letter))
    menu.on_key(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB))
    for letter in 'Rose': menu.on_key(pygame.event.Event(pygame.KEYDOWN,key=ord(letter.lower()),unicode=letter))
    assert menu.text == 'Mochi' and menu.owner_text == 'Rose'
    g._begin_new(menu.text, menu.owner_text)
    g._finish_help()
    assert g.pet.owner_name == 'Rose' and g.pet.name == 'Mochi'
    g.pet.coins = 345; g.pet.level = 4
    g._open_settings(); g.overlay._adjust(13,1)
    assert g.overlay.owner_text == 'Rose'
    g._save_profile('Luna','Sam')
    loaded = g.saves.load()
    assert loaded['pet_name'] == 'Luna' and loaded['owner_name'] == 'Sam'
    assert loaded['coins'] == 345 and loaded['level'] == 4 and loaded['version'] == 6
    if os.name == 'nt':
        a, b = SingleInstance(temp), SingleInstance(temp)
        assert not a.already_running and b.already_running
        b.close(); a.close()
        c = SingleInstance(temp); assert not c.already_running; c.close()
    g.shutdown()
print('PASS profiles, migration, save roundtrip, progress retention, single instance')
