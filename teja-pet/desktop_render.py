"""Screen-resolution desktop pets and readable speech.

Only sprite pixels are enlarged, always by a whole number. Text is rendered
at its final screen size, independently of the pixel-art furniture canvas.
"""
import math
import os
import pygame
from config import DESKTOP_KEY, INK, FRAME


def pet_rect(pet, world_scale, pet_scale):
    top = round(pet.y * world_scale - 22 * pet_scale - pet.z * world_scale)
    if not pet.carried and not pet.anim.name.startswith("walk_"):
        top += round(2 * math.sin(math.pi * pet.anim.transition / .18)) * pet_scale
    return pygame.Rect(round(pet.x * world_scale) - FRAME * pet_scale // 2,
                       top, FRAME * pet_scale, FRAME * pet_scale)


class DesktopRenderer:
    def __init__(self):
        regular = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "segoeui.ttf")
        self.font = pygame.font.Font(regular, 18) if os.path.isfile(regular) else pygame.font.SysFont("dejavusans", 18)
        self.cache = {}

    def draw_pet(self, surface, pet, assets, world_scale, pet_scale):
        rect = pet_rect(pet, world_scale, pet_scale)
        surface.blit(pygame.transform.scale(pet.frame(), rect.size), rect)
        if pet.accessory in assets.accessories:
            image = assets.accessories[pet.accessory]
            animation = pet._stretch_anim if pet._stretch_left > 0 and pet._stretch_anim else pet.anim
            ax, ay = animation.anchor()
            if pet.facing == "left" and pet.anim.name == "eat":
                ax = FRAME - ax
            w, h = image.get_size()
            image = pygame.transform.scale(image, (w * pet_scale, h * pet_scale))
            surface.blit(image, (rect.x + (ax - w // 2) * pet_scale,
                                 rect.y + (ay - h + 2) * pet_scale))
        return rect

    def bubble(self, text, max_width=300):
        key = (text, max_width)
        if key in self.cache:
            return self.cache[key]
        limit = max(30, max_width - 24)
        # Character-safe wrapping also handles a single unusually long word.
        lines, line = [], ""
        for word in text.split():
            trial = (line + " " + word).strip()
            if self.font.size(trial)[0] <= limit:
                line = trial
                continue
            if line:
                lines.append(line)
                line = ""
            for char in word:
                if line and self.font.size(line + char)[0] > limit:
                    lines.append(line)
                    line = ""
                line += char
        if line:
            lines.append(line)
        lines = lines or [""]
        width = min(max_width, max(self.font.size(line)[0] for line in lines) + 24)
        result = pygame.Surface((width, len(lines) * self.font.get_linesize() + 16))
        result.fill(DESKTOP_KEY)
        result.set_colorkey(DESKTOP_KEY)
        cream = (255, 248, 232)
        pygame.draw.rect(result, cream, result.get_rect(), border_radius=6)
        pygame.draw.rect(result, INK, result.get_rect(), 2, border_radius=6)
        for i, line in enumerate(lines):
            label = self.font.render(line, True, INK, cream)
            result.blit(label, (12, 8 + i * self.font.get_linesize()))
        if len(self.cache) >= 64:
            self.cache.clear()
        self.cache[key] = result
        return result

    def draw(self, surface, pets, assets, world_scale, pet_scale):
        bounds = surface.get_rect().inflate(-8, -8)
        bubbles = []
        for pet in sorted(pets, key=lambda p: p.y):
            if pet.hidden:
                continue
            sprite = self.draw_pet(surface, pet, assets, world_scale, pet_scale)
            if pet.bubble_t > 0 and pet.bubble_text:
                image = self.bubble(pet.bubble_text, min(300, bounds.w))
                rect = image.get_rect(midbottom=(sprite.centerx, sprite.top - 10))
                if rect.top < bounds.top:
                    rect.top = sprite.bottom + 10
                rect.clamp_ip(bounds)
                # Prefer a free position for companions speaking together.
                for other, _ in bubbles:
                    if rect.colliderect(other.inflate(6, 6)):
                        above = rect.copy()
                        above.bottom = other.top - 6
                        if above.top >= bounds.top:
                            rect = above
                        else:
                            rect.top = other.bottom + 6
                            rect.clamp_ip(bounds)
                bubbles.append((rect, image))
        for rect, image in bubbles:
            surface.blit(image, rect)
        return [rect for rect, _ in bubbles]
