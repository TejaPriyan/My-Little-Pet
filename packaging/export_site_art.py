"""Render original game art and a demo room; never read the player's save."""
import os
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.runtime'), str(ROOT / 'teja-pet')]
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
(ROOT / 'review-temp').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=ROOT / 'review-temp') as temp:
    os.environ['MY_LITTLE_PET_SAVE_DIR'] = temp
    import pygame
    from game import Game
    from save_system import default_data
    from PIL import Image
    g = Game()
    g.start_session(default_data('Mochi', 'Rose'), False)
    g.overlay = None
    g.settings.time_mode = 'day'
    g.daynight.set_mode('day')
    g.world.set_weather('clear')
    out = ROOT / 'my-little-pet-site' / 'dist' / 'assets'
    (out / 'pets').mkdir(parents=True, exist_ok=True)
    for species in ('cat', 'dog', 'bunny', 'fox'):
        for coat in range(3):
            clips = g.assets.pet_clips(species, coat)
            for pose in ('idle', 'sleep', 'eat', 'happy'):
                clip = clips.get(pose, clips['idle'])
                frames = []
                for frame in clip.frames:
                    raw = pygame.image.tostring(frame, 'RGBA')
                    frames.append(Image.frombytes('RGBA', frame.get_size(), raw).resize((192,192), Image.Resampling.NEAREST))
                frames[0].save(out / 'pets' / f'{species}-{coat}-{pose}.gif', save_all=True, append_images=frames[1:], duration=220, loop=0, disposal=2, transparency=0)
            pygame.image.save(pygame.transform.scale(clips['idle'].frames[0], (192,192)), str(out / 'pets' / f'{species}-{coat}.png'))
    g.pet.x, g.pet.y = 270, 176
    g.pet.say('HI ROSE!', 100)
    g.draw()
    pygame.image.save(pygame.transform.scale(g.canvas,(960,540)), str(out / 'room.png'))
    g._open_profile(); g.draw()
    pygame.image.save(pygame.transform.scale(g.canvas,(960,540)), str(out / 'profile.png'))
    for name in ('house','food','water','toy','plant'):
        asset = getattr(g.assets, name)
        frame = asset[0] if isinstance(asset,list) else asset
        pygame.image.save(frame, str(out / (name+'.png')))
    cat = Image.open(out / 'pets' / 'cat-0.png').convert('RGBA')
    for size in (192,512):
        icon = Image.new('RGBA',(size,size),(232,222,251,255))
        inner = cat.resize((int(size*.75),int(size*.75)),Image.Resampling.NEAREST)
        icon.alpha_composite(inner, (size//8,size//8))
        icon.save(out / f'icon-{size}.png')
    icon.save(ROOT / 'packaging' / 'pet.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    g.shutdown()
print('Exported original artwork and demo screenshots.')
