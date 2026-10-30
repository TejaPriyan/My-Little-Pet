"""Export native 24px frames without GIF palette loss or CSS stretching."""
import os,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'teja-pet'))
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from assets import Assets
pygame.init();pygame.display.set_mode((1,1))
a=Assets();out=root/'my-little-pet-site/dist/assets/pets';meta={}
for species in ('cat','dog','bunny','fox','dino','tiger','parrot'):
 for coat in range(3):
  clips=a.pet_clips(species,coat);poses=('idle','sit','sleep','eat','play','dance','wave','walk_left','walk_right','walk_up','walk_down')
  width=max(len(clips[k].frames) for k in poses)*24
  sheet=pygame.Surface((width,len(poses)*24),pygame.SRCALPHA);rows={}
  for row,key in enumerate(poses):
   clip=clips[key];rows[key]={'row':row,'count':len(clip.frames),'fps':clip.fps}
   for col,frame in enumerate(clip.frames):sheet.blit(frame,(col*24,row*24))
  key=f'{species}-{coat}';pygame.image.save(sheet,str(out/f'{key}-sheet.png'));meta[key]=rows
(out/'clips.json').write_text(json.dumps(meta),encoding='utf8')
pygame.quit()
