"""Identity, purchases, reward limits and pet-led game regressions."""
import os
import sys
import tempfile
from pathlib import Path
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'teja-pet'))
tmp = tempfile.TemporaryDirectory(dir=ROOT / 'review-temp')
os.environ['MY_LITTLE_PET_SAVE_DIR'] = tmp.name
import pygame
from game import Game
from save_system import default_data, sanitize
from life import set_trait, bond, bond_key, record_adventure, claim_adventure
from pet_games import PetGame, GardenHurdles
from decorating import Decorator

g = Game()
g.start_session(default_data('Mochi', 'Rose'), False)
p = g.pet
p.coins = 1000
p.pet_slots = 2
assert g.household.add('cat')
f = g.household.friends[0]
set_trait(p, 'shy'); set_trait(f, 'sleepy')
ids = p.pet_id, f.pet_id
assert ids[0] != ids[1]
assert bond(p, p, f, 100) == 2
assert bond(p, p, f, 101) == 2
assert bond(p, p, f, 160) == 4
key = bond_key(p, f)
g.household.select(0)
assert (p.pet_id, p.temperament, f.pet_id, f.temperament) == (ids[1], 'sleepy', ids[0], 'shy')
assert bond_key(p, f) == key
g.save_now()
saved = g.saves.load()
assert saved['bonds'][key]['points'] == 4
assert saved['companions'][0]['temperament'] == 'shy'
assert saved['coins'] == 1000
print('PASS stable identity, personality and friendships across selection + save')

for kind in ('find', 'game', 'cuddle', 'cuddle', 'cuddle'): record_adventure(p, kind, 1000)
wallet = p.coins
assert claim_adventure(p, 1000) and not claim_adventure(p, 1001)
assert p.coins == wallet + 6
assert not claim_adventure(p, 100000)
bad = sanitize({'pet_id': [], 'temperament': [], 'room_layout': {'bed': [float('nan'), -500]}, 'owned_decor': ['bogus']})
assert bad['room_layout']['bed'] == [200,100] and 'bogus' not in bad['owned_decor']
print('PASS once-per-day adventure rewards and malformed save handling')

g.overlay = Decorator(g)
editor = g.overlay
editor.choose('plant'); editor.move((255,165))
wallet = p.coins
assert p.coins == wallet and 'plant' not in p.owned_decor
assert editor.place() and p.coins == wallet - 55
editor.move((280,175)); assert editor.place() and p.coins == wallet - 55
editor.choose('bed'); editor.move((160,120)); assert editor.place()
assert g.world.anchors['bed_approach'] == (194,170)
assert g.world.find_path((240,190), g.world.anchors['bed_approach'])
assert g.world.find_path((240,190), g.world.anchors['food'])
g.draw()
pygame.image.save(g.canvas, str(ROOT/'upgrade-shots'/'life-decorating.png'))
print('PASS preview is free, purchases charge once, moved bed remains reachable')

g.settings.quiet = False
for cls in (PetGame, GardenHurdles):
    p.arcade = {}
    wallet, xp, levels = p.coins, p.xp, p.level
    game = cls(g.ui,p,g.audio,g.fx,lambda:None,watch=True)
    g.overlay = game
    for _ in range(100): game.update(.05,(300,170))
    g.draw(); pygame.image.save(g.canvas, str(ROOT/'upgrade-shots'/('life-'+game.KIND+'.png')))
    for _ in range(810): game.update(.05,(300,170))
    assert game.completed and game.score > 0
    assert (p.coins,p.xp,p.level) == (wallet,xp,levels)
    assert p.arcade.get('lives',3) == 3
    game._apply_rewards(); assert p.coins == wallet
    active = cls(g.ui,p,g.audio,g.fx,lambda:None)
    assert p.arcade['lives'] == 2
    active.score = 400
    active.on_key(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
    assert not active.completed and p.coins == wallet
print('PASS pets autonomously fetch + jump, watch uses no lives/rewards, early exit earns nothing')
g.overlay = None
g.settings.quiet = True
for _ in range(100): g.update(.05)
assert p.anim.name in ('sit','sleep') and f.anim.name in ('sit','sleep')
g.paused = True
before = (p.hunger,p.energy,p.x,p.y)
g.update(30)
assert before == (p.hunger,p.energy,p.x,p.y)
print('PASS quiet time settles pets; pause freezes the household')
g.shutdown()
tmp.cleanup()
