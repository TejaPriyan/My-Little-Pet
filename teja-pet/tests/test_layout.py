"""Real room/desktop placement, hit targets, persistence and ownership regression checks."""
import os
import sys
import tempfile
from pathlib import Path
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'teja-pet'))
(ROOT/'review-temp').mkdir(exist_ok=True)
tmp=tempfile.TemporaryDirectory(dir=ROOT/'review-temp')
os.environ['MY_LITTLE_PET_SAVE_DIR']=tmp.name
import pygame
from game import Game
from save_system import default_data, sanitize
from decorating import Decorator, apply_layout
from desktop_pet import DesktopPet

g=Game();g.start_session(default_data('Mochi','Rose'),False)
p=g.pet;p.coins=1000;p.room_theme='garden';apply_layout(g.world,p)
editor=Decorator(g);g.overlay=editor
# Select the actual right-hand plant and drag its own hit box, not a new copy.
before=len(g.world.extra_props)
editor.on_click((446,115));assert editor.key=='room_plant'
editor.on_motion((260,165));editor.on_release((260,165))
assert g.world.plant.x==250 and p.coins==1000
assert len(g.world.extra_props)==before
assert g.world.object_at((446,115))!='plant'
editor.put_away();assert not g.world.plant.visible and not editor.show_preview
assert g.world.plant.collider not in g.world.colliders
editor.choose('room_plant');assert editor.place() and p.coins==1000
# Each garden plant is independent; hiding one never hides its siblings.
editor.choose('garden_2');editor.put_away()
assert [i.name for i in g.world.extra_props]==['garden_1','garden_3']
editor.choose('garden_1');editor.move((210,150));assert editor.place()
editor.choose('food');editor.move((350,195));assert editor.place()
assert g.world.anchors['food']==(336,203)
assert g.world.find_path((240,190),g.world.anchors['food'])
editor.choose('bed');editor.move((140,110));assert editor.place()
assert g.world.find_path((240,190),g.world.anchors['bed_approach'])
editor.put_away();assert g.world.anchors['bed_spot']==g.world.anchors['bed_approach']
editor.choose('toy');editor.move((310,180));assert editor.place()
assert g.world.toy==[310,180]
editor.put_away();assert not g.world.toy_visible and g.world.object_at((310,180))!='toy'
g.brain._auto_play();assert not g.world.toy_visible
g.brain.command('play');g.brain._start_pending();assert g.world.toy_visible and 'toy' not in p.room_hidden
editor.choose('flowers');editor.move((320,160));assert editor.place()
wallet=p.coins;editor.put_away();editor.choose('flowers');assert editor.place() and p.coins==wallet
g.draw();(ROOT/'upgrade-shots').mkdir(exist_ok=True)
pygame.image.save(g.canvas,str(ROOT/'upgrade-shots/layout-room.png'))
g.save_now();saved=g.saves.load()
assert saved['room_hidden']==p.room_hidden and saved['room_layout']==p.room_layout
assert sanitize({'room_hidden':['bogus',{},'bed'], 'desktop_layout':{'furniture':{'books':[0,0],'bed':[float('nan'),4]},'put_away':['ball',{}]}})['desktop_layout']['furniture']=={'bed':[.5,1]}
print('PASS individual room props, drag/drop, hide/restore, care anchors, navigation, migration')

class Window:
    scale=1
    def __init__(self):self.canvas=pygame.Surface((640,360));self.pos=(400,180)
    def mouse(self):return self.pos
    def capture(self,on):pass
    def present(self):pass
    def close(self):pass
    def show(self):pass
w=Window();d=DesktopPet(g,w);g.desktop=d;g.overlay=None
wallet=p.coins
d.command('furn:bed');d.command('furn:room_plant');d.command('furn:lamp')
assert set(d.furniture)=={'bed','room_plant','lamp'} and p.coins==wallet-85
assert not d.furniture['bed'].colliderect(d.furniture['room_plant'])
assert not d.furniture['bed'].colliderect(d.furniture['lamp'])
d.command('furn:lamp');d.command('furn:lamp');assert p.coins==wallet-85
assert 'bed' in p.room_hidden and 'bed' in d.furniture
# Real press/motion/release keeps offsets and saves normalized coordinates.
d.menu=None;p.x=100;p.y=100
r=d.furniture['room_plant'];r.topleft=(200,140)
for event in [pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(208,148)),pygame.event.Event(pygame.MOUSEMOTION,pos=(408,228)),pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=(408,228))]:d.event(event)
assert r.topleft==(400,220) and d.drag_item is None
d.command('sleep');assert d.target==d.clamp((d.furniture['bed'].x+22,d.furniture['bed'].y+25))
d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=3,pos=(405,225)))
assert d.menu_entries()[0][0]=='remove_item'
d.command('remove_item');assert 'room_plant' not in d.furniture
d.command('furn:room_plant');d.menu=None
d.command('hide');assert '@bed' in d.visible_props() and 'home' not in d.visible_props()
d.draw();pygame.image.save(w.canvas,str(ROOT/'upgrade-shots/layout-desktop.png'))
d.save_layout();restored=g.saves.load()
assert restored['desktop_layout']['furniture']==p.desktop_layout['furniture']
assert restored['room_hidden']==p.room_hidden
# X always leaves a reachable menu, even with all pets and furnishings hidden.
d.command('showhome');d.menu=None
d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=d.controls()[1].center))
assert 'home' not in d.visible_props() and d.recovery_visible()
d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=d.recovery_rect().center))
assert d.menu_mode=='visibility' and d.menu_entries()[0]==('showhome','SHOW HOUSE')
d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(d.menu.x+20,d.menu.y+10)))
assert 'home' in d.visible_props()
positions={k:tuple(r) for k,r in d.furniture.items()};wallet=p.coins
d.command('toggle_items');assert d.visible_props()==['home'] and d.recovery_visible()
d.command('toggle_items');assert '@bed' in d.visible_props()
d.command('hideall');d.menu=None
assert not d.visible_props() and not d.visible_pets() and d.recovery_visible()
needs=(p.hunger,p.happiness,p.energy,p.x,p.y)
d.update(10);assert needs==(p.hunger,p.happiness,p.energy,p.x,p.y)
d.draw()
assert w.canvas.get_at(d.recovery_rect().center)[:3]!=(255,0,255)
pygame.image.save(w.canvas,str(ROOT/'upgrade-shots/desktop-hidden-controls.png'))
hidden_save=g.saves.load();assert hidden_save['desktop_layout']['pets_hidden'] and hidden_save['desktop_layout']['items_hidden']
d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=d.recovery_rect().center))
assert ('showall','SHOW EVERYTHING') in d.menu_entries()
d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(d.menu.x+20,d.menu.y+5+3*16+7)))
assert d.visible_pets() and 'home' in d.visible_props() and '@bed' in d.visible_props()
assert p.coins==wallet and positions=={k:tuple(r) for k,r in d.furniture.items()}
d.put_away.add('home');d.hidden=False;d.command('hide');assert 'home' in d.visible_props()
d.command('hideall');g._tray_action('showall');assert not d.pets_hidden and not d.items_hidden and not d.hidden
d.command('toggle_pets');g._tray_action('rescue');assert d.visible_pets()
assert not sanitize({'desktop_layout':{'pets_hidden':'true','items_hidden':[]}})['desktop_layout']['pets_hidden']
print('PASS X recovery button, independent visibility, hidden-pet rest, persisted layout, menu and tray restoration')
d.restore();g.desktop=None;g.shutdown();tmp.cleanup()
print('PASS desktop furniture ownership, drag, context removal, bed naps, independent persistent layouts')
