"""Household, progression and desktop front-door regressions with real Pygame."""
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'teja-pet'))
import pygame
import config

(ROOT / 'review-temp').mkdir(exist_ok=True)
tmp = tempfile.TemporaryDirectory(dir=ROOT / 'review-temp')
config.SAVE_DIR = tmp.name
config.SAVE_PATH = str(Path(tmp.name) / 'save.json')
config.SETTINGS_PATH = str(Path(tmp.name) / 'settings.json')
from game import Game
from save_system import default_data, sanitize
from desktop import DesktopPet
from economy import allowance, meal, start_round, refresh_arcade
from minigame import BugCatchGame, MemoryGardenGame, FireflyRhythmGame

g = Game()
g.start_session(default_data('Mochi', 'Rose'), offline=False)
g.overlay = None
p = g.pet
shots = ROOT / 'upgrade-shots'
shots.mkdir(exist_ok=True)

def test_household():
    p.achievements.update(config.ACHIEVEMENTS)
    p.coins = 5000
    p.hunger = 37
    assert not g.household.add('cat'), 'a second friend requires a slot'
    g._family_action('slot')
    assert p.pet_slots == 2 and p.coins == 4750
    assert not g.household.add('tiger'), 'locked species cannot be added'
    g._buy('species:dino')
    assert p.coins == 4300
    p.set_look('cat')
    assert g.household.add('dino')
    f = g.household.friends[0]
    f.name, f.hunger = 'Fern', 61
    wallet = p.coins
    p.hidden = True
    assert g.household.select(0)
    assert (p.name, p.species, p.hunger, p.coins) == ('Fern', 'dino', 61, wallet)
    assert not p.hidden
    assert (f.name, f.hunger) == ('Mochi', 37)
    g.save_now()
    data = g.saves.load()
    g.start_session(data, offline=False)
    assert g.pet.name == 'Fern' and g.household.friends[0].name == 'Mochi'
    for _ in range(2): g._family_action('slot')
    assert g.pet.pet_slots == 4
    assert g.household.add('cat') and g.household.add('dino')
    assert not g.household.add('cat')
    g.pet.solo = True
    assert not g.household.visible
    g.pet.solo = False
    for kind in ('chat', 'wrestle', 'dance'):
        g.household.socialize(kind)
        assert g.pet.bubble_t > 0
    for _ in range(100): g.household.update(.1)
    assert all(g.world.is_free(f.x, f.y) for f in g.household.friends)
    g.overlay = None
    g.draw(); pygame.image.save(g.canvas, str(shots / 'household-room.png'))

def test_economy_and_migration():
    p = g.pet
    old = sanitize({'version':4, 'coins':432, 'pet_name':'Old friend'})
    assert old['coins'] == 432 and old['version'] == 6 and old['pet_slots'] == 1
    p.reward_times = {}
    assert allowance(p, 'pet', 100) and not allowance(p, 'pet', 101)
    g.save_now(); assert g.saves.load()['reward_times']['pet'] == 220
    p.hunger = 10; p.pantry = {'fish':1}; p.selected_food = 'fish'
    meal(p); assert p.hunger == 48 and p.pantry['fish'] == 0
    meal(p); assert p.hunger == 68, 'empty pantry falls back to the free bowl'
    p.arcade = {}
    assert all(start_round(p, 100) for _ in range(3))
    assert not start_round(p, 100)
    assert refresh_arcade(p, 1899)['lives'] == 0
    assert refresh_arcade(p, 1900)['lives'] == 1
    bad = sanitize({'pet_slots':999,'companions':[None,{},[]], 'desktop_layout':{'home':[-99,999]},'arcade':{'lives':-10,'earned':999}})
    assert bad['pet_slots'] == 4 and bad['desktop_layout']['home'] == [0,1]
    assert bad['arcade']['lives'] == 0 and bad['arcade']['earned'] == 40

def test_taps_and_room_bundles():
    g.overlay = None
    p, f = g.pet, g.household.friends[0]
    p.x, p.y, f.x, f.y = 150, 180, 280, 200
    before = sorted([p.name] + [x.name for x in g.household.friends])
    for _ in range(12): g._on_click(f.rect().center)
    assert sorted([p.name] + [x.name for x in g.household.friends]) == before
    assert (p.x, p.y, f.x, f.y) == (150, 180, 280, 200)
    assert f.anim.name == 'wave' and f.bubble_t > 0
    g.household.select(0)
    assert (p.x, p.y, f.x, f.y) == (280, 200, 150, 180), 'selection keeps identities in place'
    g.household.social_left = 0
    f.hunger = 20
    g.household.start_activity(0, 'eat')
    g.household.activities[0]['path'] = []
    wallet, xp = p.coins, p.xp
    for _ in range(50): g.household.update(.1)
    assert f.hunger > 35 and (p.coins, p.xp) == (wallet, xp)
    f.energy = 10
    g.household.start_activity(0, 'sleep')
    g.household.activities[0]['path'] = []
    for _ in range(50): g.household.update(.1)
    assert f.energy > 10 and f.anim.name == 'sleep'
    p.coins = 1000
    g._buy('room:seaside')
    assert p.coins == 820 and p.room_theme == 'seaside'
    g._buy('room:seaside'); assert p.coins == 820
    g.save_now(); assert g.saves.load()['room_theme'] == 'seaside'
    for theme in ('seaside','cabin','moon'):
        p.room_theme = theme; g.draw()
        pygame.image.save(g.canvas,str(shots/('room-'+theme+'.png')))
    p.room_theme = 'seaside'

def test_rounds():
    p = g.pet
    p.arcade = {'lives':3, 'refill_at':time.time()}
    game = BugCatchGame(g.ui,p,g.audio,g.fx,lambda:None)
    game.score = 99
    before = p.coins, p.xp
    game.on_key(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
    assert not game.completed and before == (p.coins,p.xp)
    memory = MemoryGardenGame(g.ui,p,g.audio,g.fx,lambda:None)
    memory.choose(memory.sequence[0]); assert memory.input_index == 0
    memory.show_time = 2
    sequence = memory.sequence[:]
    for i in sequence: memory.choose(i)
    assert memory.score == 4 and len(memory.sequence) == 3
    memory.update(.01,None); assert memory.flash == -1
    memory.update(46,None)
    before = p.coins,p.xp,p.level
    memory._apply_rewards(); assert before == (p.coins,p.xp,p.level)
    rhythm = FireflyRhythmGame(g.ui,p,g.audio,g.fx,lambda:None)
    rhythm.tap(); rhythm.tap(); assert rhythm.score == 3
    rhythm.update(31,None)
    practice = FireflyRhythmGame(g.ui,p,g.audio,g.fx,lambda:None)
    assert not practice.paid_round
    practice.score = 100; before = p.coins,p.xp
    practice.update(31,None); assert before == (p.coins,p.xp)
    g.overlay = rhythm; g.draw(); pygame.image.save(g.canvas, str(shots/'rhythm-results.png'))
    g.overlay = None

def test_desktop_front_door():
    class Window:
        scale = 1
        def __init__(self): self.canvas = pygame.Surface((640,360)); self.pos = (600,300)
        def mouse(self): return self.pos
        def capture(self,on): pass
        def present(self): pass
        def close(self): pass
    w = Window(); d = DesktopPet(g,w); g.desktop = d
    room = d.room_pos
    for key in ('home','food','water','ball'):
        r = getattr(d,key); start = r.center; end = (start[0]+125,start[1]-80)
        d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=start))
        d.event(pygame.event.Event(pygame.MOUSEMOTION,pos=end))
        d.event(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=end))
        assert r.center == end, key
    d.command('compact'); assert d.home.w == 28
    d.command('hide'); assert d.hidden
    d.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
    assert g.desktop is d, 'Escape must not open the room'
    saved = g.saves.load()['desktop_layout']; assert saved['compact'] and saved['hidden']
    d.command('follow'); before = (g.pet.x,g.pet.y); d.update(.1)
    assert (g.pet.x,g.pet.y) != before
    d.command('dance'); d.update(.1); assert d.state == 'dance'
    d.command('hide'); d.draw(); pygame.image.save(w.canvas,str(shots/'desktop-family.png'))
    d.command('home')
    assert g.desktop is d and d.after == 'enter', 'home must walk before returning'
    for _ in range(1000):
        if g.desktop is None: break
        d.update(.05)
    assert g.desktop is None and not g.pet.hidden
    assert (g.pet.x,g.pet.y) == room

if __name__ == '__main__':
    try:
        for fn in (test_household,test_economy_and_migration,test_taps_and_room_bundles,test_rounds,test_desktop_front_door):
            fn(); print('PASS',fn.__name__,flush=True)
    finally:
        g.shutdown(); tmp.cleanup()
