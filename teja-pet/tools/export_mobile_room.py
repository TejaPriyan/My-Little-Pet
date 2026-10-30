"""Share native walls, beds and walking art with the installed landscape room."""
import os,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'teja-pet'))
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
with tempfile.TemporaryDirectory(dir=root/'review-temp') as tmp:
 os.environ['MY_LITTLE_PET_SAVE_DIR']=tmp
 import pygame
 from PIL import Image
 from game import Game
 from save_system import default_data
 from config import HUD_H,BAR_Y,W
 g=Game();g.start_session(default_data('Mochi','Rose'),False)
 g.daynight.set_mode('day');g.world.set_weather('clear')
 g.world.rug.visible=False;g.world.cushion.visible=False
 out=root/'my-little-pet-site/dist/assets'
 for theme in ('classic','garden','starlight','seaside','cabin','moon'):
  g.world.draw_background(g.canvas,0,g.daynight,theme)
  pygame.image.save(g.canvas.subsurface((0,HUD_H,W,BAR_Y-HUD_H)),str(out/'rooms'/f'{theme}-background.png'))
  pygame.image.save(g.assets.room_style(theme)['bed'],str(out/'rooms'/f'{theme}-bed.png'))
 for species in ('cat','dog','bunny','fox','dino','tiger','parrot'):
  for coat in range(3):
   for pose in ('walk_left','walk_right'):
    clip=g.assets.pet_clips(species,coat)[pose]
    frames=[Image.frombytes('RGBA',frame.get_size(),pygame.image.tobytes(frame,'RGBA')).resize((192,192),Image.Resampling.NEAREST) for frame in clip.frames]
    frames[0].save(out/'pets'/f'{species}-{coat}-{pose}.gif',save_all=True,append_images=frames[1:],duration=round(1000/clip.fps),loop=0,disposal=2,transparency=0)
 g.shutdown()
print('Exported six native room backgrounds, six beds and 42 walking animations.')
