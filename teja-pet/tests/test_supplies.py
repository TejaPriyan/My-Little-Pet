"""Regressions for visible desktop pets, guided adoption and visual supplies."""
import os
import sys
import tempfile
from pathlib import Path
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'teja-pet'))
(ROOT/'review-temp').mkdir(exist_ok=True)
tmp = tempfile.TemporaryDirectory(dir=ROOT/'review-temp')
os.environ['MY_LITTLE_PET_SAVE_DIR'] = tmp.name
import pygame
from game import Game
from save_system import default_data, sanitize
from config import FOODS
from supplies import TOYS
from economy import meal
from desktop_pet import DesktopPet
from decorating import Decorator
from life import DECOR
g = Game(); g.start_session(default_data('Mochi','Teja'),False)
p = g.pet; p.coins=10000; p.solo=True
g._family_action('add')
assert any(k=='slotadd' for k,_ in g.overlay.entries)
wallet=p.coins
g._family_action('slotadd')
assert p.pet_slots==2 and p.coins==wallet-250 and not g.household.friends
g._add_friend('cat')
assert len(g.household.visible)==1 and not p.solo
g._add_friend('cat')
assert len(g.household.friends)==1 and p.coins==wallet-250
for _ in range(15): g.household.interact(0)
assert len(g.household.friends)==1
print('PASS guided second-pet adoption, one slot charge, solo resets, taps never spawn pets')

textures=set()
for key in FOODS:
    p.pantry[key]=0; p.hunger=20; before=p.coins
    g._choose_food(key)
    assert p.selected_food==key and p.coins==before-FOODS[key]['price']
    before=p.coins; g._choose_food(key); assert p.coins==before
    textures.add(pygame.image.tobytes(g.assets.meals[key][0],'RGBA'))
    meal(p)
    assert p.hunger>20 and p.selected_food=='kibble'
assert len(textures)==len(FOODS)
for key in TOYS:
    before=p.coins;g._choose_toy(key)
    assert p.selected_toy==key and p.coins==before-TOYS[key][1]
    before=p.coins;g._choose_toy(key);assert p.coins==before
g.save_now(); saved=g.saves.load()
assert saved['selected_toy']=='butterfly' and set(saved['owned_toys'])==set(TOYS)
assert sanitize({'owned_toys':['missing'],'selected_toy':'missing'})['selected_toy']=='ball'
print('PASS seven different meals, pantry consumption, six toy purchases and save migration')

g.overlay=Decorator(g)
for key in ('flowers','lamp','books'):
    g.overlay.choose(key);g.overlay.move((250,170));before=p.coins
    assert key not in p.owned_decor and p.coins==before
    assert g.overlay.place() and p.coins==before-DECOR[key][1]
    assert g.overlay.place() and p.coins==before-DECOR[key][1]
page=g.overlay.page
g.overlay.on_key(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB))
assert g.overlay.page==(page+1)%((len(DECOR)+3)//4)
g.draw()
shots=ROOT/'upgrade-shots';shots.mkdir(exist_ok=True)
pygame.image.save(g.canvas,str(shots/'supplies-decor.png'))
g._food_menu(); g.overlay.page=1; g.draw();pygame.image.save(g.canvas,str(shots/'supplies-pantry.png'))
g._toy_menu();g.draw();pygame.image.save(g.canvas,str(shots/'supplies-toys.png'))
print('PASS decoration preview, two catalog pages and duplicate-purchase protection')

class Window:
    scale=1
    def __init__(self): self.canvas=pygame.Surface((480,250)); self.pos=(230,200)
    def mouse(self): return self.pos
    def capture(self,on): pass
    def present(self): pass
    def close(self): pass
    def show(self): pass
w=Window();d=DesktopPet(g,w);g.desktop=d;g.overlay=None
p.energy=5;d.command('sleep')
for _ in range(300): d.update(.05)
assert d.state=='sleep' and not p.hidden
for _ in range(10):
    pos=p.rect().center
    d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))
    d.event(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=pos))
    d.update(.1)
    assert not p.hidden and not p.carried and len(g.household.friends)==1
d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=3,pos=(479,249)))
assert 0<=d.menu.top and d.menu.bottom<=250
reachable=set()
for _ in range(3):
    reachable.update(k for k,_ in d.ACTIONS[d.menu_page*8:d.menu_page*8+8])
    d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(d.menu.centerx,d.menu.bottom-10)))
assert len(reachable)==len(d.ACTIONS)
d.menu=None;p.hidden=True;p.solo=True;p.x=-1000;g.paused=True
d.command('rescue');assert not p.hidden and not p.solo and not g.paused and p.x>0
g.settings.quiet=True;p.hunger=20;d.hidden=True;d.put_away.add('food');d.command('feed')
for _ in range(70):d.update(.05)
assert p.hunger>30 and not p.hidden
d.command('home')
for _ in range(1500):
    if not g.desktop:break
    d.update(.05)
assert not g.desktop and not p.hidden
print('PASS desktop naps remain visible, repeated taps, compact menus, recovery, quiet feeding and home entry')
g.shutdown();tmp.cleanup()
