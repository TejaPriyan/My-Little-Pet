"""Real renderer checks: readable speech and independently sized sharp pets."""
import os
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
tmp = tempfile.TemporaryDirectory(dir=root / "review-temp")
os.environ["MY_LITTLE_PET_SAVE_DIR"] = tmp.name
sys.path.insert(0, str(root / "teja-pet"))
import pygame
from game import Game
from save_system import default_data
from settings import Settings, PET_SIZES
from desktop_pet import DesktopPet
from desktop_render import DesktopRenderer, pet_rect

g = Game()
g.start_session(default_data("Mochi", "Rose"), False)
g.overlay = None

class Window:
    scale = 3
    def __init__(self):
        self.canvas = pygame.Surface((640, 340))
        self.ui_canvas = pygame.Surface((640, 340))
        self.renderer = DesktopRenderer()
    def mouse(self): return 320, 170
    def capture(self, on): pass
    def close(self): pass
    def show(self): pass
    def present(self): pass

d = DesktopPet(g, Window())
g.desktop = d
p = g.pet
furniture = [getattr(d, key).copy() for key in ("home", "food", "water", "ball")]
coins = p.coins
d.command("size")
assert d.menu_mode == "size" and len(d.menu_entries()) == 5
surface = pygame.Surface((1920, 1020))
renderer = DesktopRenderer()
for size in PET_SIZES:
    d.command("size:" + str(size))
    assert Settings.load().pet_scale == size
    assert [getattr(d, key) for key in ("home", "food", "water", "ball")] == furniture
    assert p.coins == coins
    for point in [(-100, -100), (10000, 10000)]:
        p.x, p.y = d.clamp(point)
        assert surface.get_rect().contains(pet_rect(p, 3, size))
        assert d.pet_rect(p).collidepoint(p.x, p.y - 10)
    p.x, p.y = 320, 170
    p.z = 0
    p.anim.transition = 0
    surface.fill((40, 60, 85))
    rect = renderer.draw_pet(surface, p, g.assets, 3, size)
    assert rect.size == (24 * size, 24 * size)
    # Every original opaque pixel remains a solid block of exactly size x size.
    frame = p.frame()
    for y in range(24):
        for x in range(24):
            original = frame.get_at((x, y))
            if original.a != 255: continue
            for dy in range(size):
                for dx in range(size):
                    assert surface.get_at((rect.x+x*size+dx, rect.y+y*size+dy))[:3] == original[:3]
    p.say("DREAMING OF SNACKS... A COZY LITTLE NAP IN MY BED.", 4)
    for x, y in [(1, 1), (639, 339)]:
        p.x, p.y = x, y
        bubbles = renderer.draw(surface, [p], g.assets, 3, size)
        assert all(surface.get_rect().contains(rect) and rect.width <= 300 for rect in bubbles)
d.command("size:99")
assert g.settings.pet_scale == 5
assert renderer.font.get_height() >= 18
assert renderer.bubble("DREAMING OF SNACKS...").get_height() >= 30
d.draw()

# A review image uses the exact production renderer, not an image mock-up.
proof = pygame.Surface((1100, 310))
proof.fill((42, 53, 78))
font = pygame.font.SysFont("segoeui", 18)
for i, size in enumerate(PET_SIZES):
    p.x, p.y, p.z = 140 + i * 270, 240, 0
    p.say("Dreaming of snacks..." if i % 2 else "Wheee!", 4)
    renderer.draw(proof, [p], g.assets, 1, size)
    label = font.render(PET_SIZES[size].title() + " · " + str(size*24) + " px", True, (255, 248, 232))
    proof.blit(label, label.get_rect(center=(p.x, 278)))
pygame.image.save(proof, root / "review-temp" / "desktop-size-and-text.png")
from ui import SettingsMenu
from unittest.mock import patch
menu = SettingsMenu(g.ui, g.settings, lambda: None, lambda: None, lambda: None)
for i in range(len(menu.rows)-1):
    assert not menu._row_rect(i).colliderect(menu._row_rect(i+1))
with patch('webbrowser.open') as opened:
    menu.on_click(menu._row_rect(menu.rows.index('BUY ME A COFFEE')).center)
    opened.assert_called_once_with('https://buymeacoffee.com/tejapriyan')
menu.draw(pygame.Surface((480, 270)))
print('PASS optional support opens the correct external page and menu click areas do not overlap')

d.restore()
pygame.quit()
tmp.cleanup()
print("PASS 4 saved pet sizes, furniture unchanged, pixel-perfect blocks, matching hitboxes, bounded readable speech")
