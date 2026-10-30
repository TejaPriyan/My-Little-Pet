"""Export the same native pixel paintings for the local mobile app."""
import os
import sys
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root/'teja-pet'))
import pygame
from supplies import food_frames, toy_image, decor_image, TOYS
from config import FOODS
out = root/'my-little-pet-site'/'dist'/'assets'/'supplies'
out.mkdir(parents=True, exist_ok=True)
for key in FOODS: pygame.image.save(food_frames(key)[0], str(out/f'food-{key}.png'))
for key in TOYS: pygame.image.save(toy_image(key), str(out/f'toy-{key}.png'))
for key in ('flowers','lamp','books'): pygame.image.save(decor_image(key), str(out/f'decor-{key}.png'))
print(f'Exported {len(FOODS)+len(TOYS)+3} matching food, toy and decor paintings')
