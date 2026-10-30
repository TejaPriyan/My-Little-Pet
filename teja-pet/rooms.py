"""Permanent room bundles: wallpaper, floor, bed and desktop house."""
import pygame
from config import W, HUD_H, FLOOR_Y

ROOMS = {"classic": ("COZY ROOM", 1), "garden": ("GARDEN ROOM", 3), "starlight": ("STAR ROOM", 5),
         "seaside": ("SEASIDE COTTAGE", 1), "cabin": ("WOODLAND CABIN", 1), "moon": ("MOON SUITE", 1)}
ROOM_PRICES = {"seaside": 180, "cabin": 260, "moon": 400}
PALETTES = {
    "garden": ((221, 235, 196), (197, 217, 168), (180, 161, 117), (98, 147, 100)),
    "starlight": ((192, 190, 224), (173, 171, 207), (135, 135, 179), (123, 104, 179)),
    "seaside": ((211, 240, 239), (172, 220, 222), (237, 210, 161), (69, 159, 181)),
    "cabin": ((228, 214, 179), (196, 185, 146), (172, 124, 89), (102, 137, 88)),
    "moon": ((75, 79, 123), (63, 65, 105), (140, 137, 179), (157, 125, 197)),
}


def recolor(surface, mapping):
    out = surface.copy()
    for y in range(out.get_height()):
        for x in range(out.get_width()):
            col = out.get_at((x, y))
            replacement = mapping.get(tuple(col[:3]))
            if replacement: out.set_at((x, y), (*replacement, col[3]))
    return out


def style(assets, key):
    if key not in PALETTES:
        return {"room": assets.room, "bed": assets.bed, "house": assets.house}
    wall, stripe, floor, accent = PALETTES[key]
    room = assets.room.copy()
    wh, height = FLOOR_Y - HUD_H, room.get_height()
    room.fill(wall, (0, 0, W, wh))
    for x in range(0, W, 20): room.fill(stripe, (x, 0, 2 if key != "cabin" else 10, wh))
    room.fill(tuple(max(0, c - 30) for c in accent), (0, wh - 5, W, 5))
    room.fill(floor, (0, wh, W, height - wh))
    seam = tuple(max(0, c - 25) for c in floor)
    for y in range(wh, height, 14):
        room.fill(seam, (0, y, W, 1))
        for x in range((y // 14 % 2) * 28, W, 56): room.fill(seam, (x, y, 1, 14))
    if key in ("moon", "starlight"):
        for x in range(20, W, 37):
            y = 9 + (x * 7 % max(1, wh - 19))
            room.fill((250, 230, 170), (x, y, 1, 4)); room.fill((250, 230, 170), (x - 1, y + 1, 3, 1))
    if key == "seaside":
        for x in range(0, W, 20): pygame.draw.arc(room, accent, (x, wh - 23, 20, 10), 0, 3.14, 2)
    if key == "cabin":
        for x in (34, 170, 310, 458): pygame.draw.polygon(room, accent, [(x, 20), (x - 9, 39), (x + 9, 39)])
    light = tuple(min(255, c + 35) for c in accent)
    dark = tuple(max(0, c - 32) for c in accent)
    bed = recolor(assets.bed, {(112,190,204): accent, (140,210,220): light, (150,220,228): light})
    if key == "moon":
        for x in (35, 45, 55): bed.fill((255, 235, 172), (x, 15, 2, 2))
    house = recolor(assets.house, {(236,104,120): accent, (196,74,98): dark, (255,146,156): light,
                                   (255,238,216): wall, (232,204,178): stripe})
    return {"room": room, "bed": bed, "house": house}
