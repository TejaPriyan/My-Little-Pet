"""Exercise real desktop commands with isolated saves and deterministic toy motion."""
import os,sys,tempfile,random,math
from pathlib import Path
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
root=Path(__file__).resolve().parents[2]
tmp=tempfile.TemporaryDirectory(dir=root/'review-temp');os.environ['MY_LITTLE_PET_SAVE_DIR']=tmp.name
sys.path.insert(0,str(root/'teja-pet'))
import pygame
from playful import ToyMotion
from supplies import TOYS
from game import Game
from save_system import default_data
from desktop_pet import DesktopPet
positions={}
for kind in TOYS:
    motion=ToyMotion(kind,(18,40,620,340),(320,200),random.Random(42))
    for i in range(1800):
        motion.update(1/60)
        assert 18<=motion.x<=620 and 40<=motion.y<=340 and math.isfinite(motion.z)
        if i%120==0:motion.bat()
    positions[kind]=(round(motion.x),round(motion.y),round(motion.z))
assert len(set(positions.values()))==6
g=Game();g.start_session(default_data('Mochi','Rose'),False)
class Window:
    scale=1
    def __init__(self):self.canvas=pygame.Surface((640,360));self.pos=(400,180)
    def mouse(self):return self.pos
    def capture(self,on):pass
    def present(self):pass
    def close(self):pass
    def show(self):pass
d=DesktopPet(g,Window());g.desktop=d;p=g.pet;coins=p.coins
d.command('play');assert d.fun.mode=='toy';home=d.fun.home
for _ in range(600):d.update(1/60)
assert d.ball.topleft!=home
d.save_layout();assert p.desktop_layout['ball']==[home[0]/d.w,home[1]/d.h]
d.command('quiet');assert d.fun.mode is None and d.ball.topleft==home
d.command('quiet');d.command('peek');assert d.fun.mode=='peek'
pos=(int(p.x),int(p.y-12))
d.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))
d.event(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=pos))
assert 'FOUND ME' in p.bubble_text and d.fun.mode is None
d.command('mouse');assert d.fun.mode=='mouse'
for _ in range(1500):d.update(1/60)
assert d.fun.mode is None and p.coins==coins
d.command('play');d.command('hideall');assert d.fun.mode is None
d.command('showall');d.command('surprises');d.fun.next_surprise=0;d.fun.next_chat=0
for _ in range(30):d.update(1/60)
assert d.fun.mode is None
d.command('rescue');assert not p.hidden and 14<=p.x<=d.w-14
# House controls appear only around the house and remain reachable above it.
d.window.pos=(d.w/2,d.h/2)
assert not d.controls_visible()
d.window.pos=d.home.center
assert d.controls_visible()
d.window.pos=d.controls()[0].center
assert d.controls_visible()
# Unattended balls lose all momentum; a new bat starts a fresh bounce.
m=ToyMotion('ball',(18,40,620,340),(320,200),random.Random(7))
for _ in range(360): m.update(1/60)
assert m.z==0 and m.vx==0 and m.vy==0
m.bat();m.update(.1);assert m.z>0
# Toys wait for a distant pet instead of bouncing by themselves.
d.command('rescue');p.x,p.y=40,80;d.ball.center=(560,300)
d.command('play');initial=d.ball.center
for _ in range(20): d.update(1/60)
assert d.ball.center==initial and not d.fun.engaged
# Peeking clips only part of the pet; stopping brings it fully on-screen.
d.command('peek');d.fun.goal=(1,48)
for _ in range(600): d.update(1/60)
assert p.x<14 and p.rect().clip(d.window.canvas.get_rect()).width>=10
d.fun.stop();assert p.x>=14
# Automatic play never issues play rewards.
plays=p.stats['total_plays'];coins=p.coins
d.fun.start('toy',automatic=True)
d.fun.elapsed=23.99;d.fun.update(.02)
assert p.stats['total_plays']==plays and p.coins==coins
d.draw()
# A catch keeps its play animation visible instead of switching next frame.
d.fun.start('toy');p.x,p.y=d.fun.motion.x,d.fun.motion.y;d.fun.catch_cd=0
d.fun.update(.02);assert d.fun.play_hold>0 and p.anim.name=='play'
d.fun.update(.02);assert p.anim.name=='play'
d.restore();pygame.quit();tmp.cleanup()
print('PASS six bounded toy patterns, quiet/hide interruption, saved positions, hide-and-seek tap, no ambient coins')
