"""A visual, paged pantry and toy box with explicit prices and selection."""
import pygame
from config import FOODS, INK, GOLD
from supplies import TOYS


class SupplyMenu:
    modal = True

    def __init__(self, game, kind):
        self.game, self.ui, self.kind = game, game.ui, kind
        self.keys = list(FOODS if kind == 'food' else TOYS)
        self.page = 0
        self.selected = 0
        self.mouse = None

    def update(self, dt, mouse): self.mouse = mouse

    def row(self, i): return pygame.Rect(38, 63 + i * 35, 404, 32)

    def choose(self, key):
        page = self.page
        (self.game._choose_food if self.kind == 'food' else self.game._choose_toy)(key)
        if isinstance(self.game.overlay, SupplyMenu): self.game.overlay.page = page

    def on_key(self, ev):
        if ev.key == pygame.K_ESCAPE: self.game._close_overlay()
        elif ev.key in (pygame.K_UP, pygame.K_DOWN):
            self.selected = (self.selected + (1 if ev.key == pygame.K_DOWN else -1)) % len(self.keys)
            self.page = self.selected // 4
        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER): self.choose(self.keys[self.selected])
        elif ev.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN, pygame.K_LEFT, pygame.K_PAGEUP):
            self.page = (self.page + (1 if ev.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN) else -1)) % ((len(self.keys)+3)//4)
            self.selected = self.page * 4

    def on_click(self, pos):
        if pygame.Rect(350, 215, 88, 24).collidepoint(pos):
            self.page = (self.page+1) % ((len(self.keys)+3)//4); return
        if pygame.Rect(40, 215, 72, 24).collidepoint(pos): self.game._close_overlay(); return
        for i, key in enumerate(self.keys[self.page*4:self.page*4+4]):
            if self.row(i).collidepoint(pos): self.choose(key); return

    def draw(self, surf):
        u, p = self.ui, self.game.pet
        surf.blit(u.dim, (0, 0)); u.draw_panel(surf, (28, 28, 424, 218))
        u.text(surf, 'PANTRY' if self.kind == 'food' else 'TOY BOX', (43, 40), INK, 2)
        u.text(surf, '%d COINS' % p.coins, (436, 42), GOLD, anchor='topright')
        for i, key in enumerate(self.keys[self.page*4:self.page*4+4]):
            r = self.row(i)
            food = self.kind == 'food'
            label = FOODS[key]['name'] if food else TOYS[key][0]
            selected = key == (p.selected_food if food else p.selected_toy)
            owned = key == 'kibble' or p.pantry.get(key, 0) > 0 if food else key in p.owned_toys
            price = FOODS[key]['price'] if food else TOYS[key][1]
            detail = ('SELECTED' if selected else 'SELECT') if owned else 'BUY + SELECT %d COINS' % price
            if food and key != 'kibble': detail += ' / %d LEFT' % p.pantry.get(key, 0)
            u.small_button(surf, r, '', bool(self.mouse and r.collidepoint(self.mouse)), selected)
            img = self.game.assets.meals[key][0] if food else self.game.assets.toys[key]
            surf.blit(pygame.transform.scale(img, (28, 28)), (r.x+5, r.y+2))
            u.text(surf, label, (r.x+44, r.y+5), INK)
            u.text(surf, detail, (r.x+44, r.y+18), INK)
        u.small_button(surf, (40, 215, 72, 24), 'DONE', False)
        u.text(surf, 'FEED USES ONE PORTION' if self.kind == 'food' else 'PLAY USES YOUR SELECTED TOY', (123, 223), INK)
        if len(self.keys) > 4: u.small_button(surf, (350, 215, 88, 24), 'MORE %d/%d' % (self.page+1, (len(self.keys)+3)//4), False)
