"""Shop, game picker, and a short keyboard/mouse tutorial."""
import pygame
import petart
from activities import ROOMS, ROOM_PRICES, GOALS, refresh
from config import SHOP_ITEMS, SPECIES, SPECIES_ORDER, ACCESSORIES, ACCESSORY_ORDER, INK, GOLD, WHITE, CREAM_DK
from ui import GREY, RED


class ChoiceMenu:
    def __init__(self, ui, title, entries, on_select, on_close):
        self.ui, self.title, self.entries = ui, title, entries
        self.on_select, self.on_close = on_select, on_close
        self.sel, self.mouse, self.modal, self.page = 0, None, True, 0
        self.rect = pygame.Rect(65, 43, 350, 182)

    def row(self, i):
        return pygame.Rect(self.rect.x + 12, self.rect.y + 36 + i * 25, self.rect.w - 24, 23)

    def update(self, dt, mouse):
        self.mouse = mouse

    def on_key(self, ev):
        if ev.key == pygame.K_ESCAPE:
            self.on_close()
        elif ev.key in (pygame.K_UP, pygame.K_DOWN):
            self.sel = (self.sel + (1 if ev.key == pygame.K_DOWN else -1)) % len(self.entries)
            self.page = self.sel // 5
        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.on_select(self.entries[self.sel][0])

    def on_click(self, pos):
        if pygame.Rect(320, 209, 80, 13).collidepoint(pos) and len(self.entries) > 5:
            self.page = (self.page + 1) % ((len(self.entries) + 4) // 5)
            self.sel = self.page * 5
            return
        for i, (key, _) in enumerate(self.entries[self.page * 5:self.page * 5 + 5]):
            if self.row(i).collidepoint(pos):
                self.on_select(key)
                return
        if not self.rect.collidepoint(pos):
            self.on_close()

    def draw(self, surf):
        u = self.ui
        surf.blit(u.dim, (0, 0))
        u.draw_panel(surf, self.rect)
        u.text(surf, self.title, (240, self.rect.y + 12), INK, 2, WHITE, "midtop")
        for i, (_, label) in enumerate(self.entries[self.page * 5:self.page * 5 + 5]):
            u.small_button(surf, self.row(i), label, bool(self.mouse and self.row(i).collidepoint(self.mouse)), self.sel == self.page * 5 + i)
        u.text(surf, "ARROWS / ENTER   ESC CLOSES", (240, self.rect.bottom - 14), GREY, anchor="midtop")
        if len(self.entries) > 5: u.small_button(surf, (320, 209, 80, 13), "MORE >", False)


class Tutorial:
    def __init__(self, ui, on_close):
        self.ui, self.on_close = ui, on_close
        self.modal, self.mouse = True, None
        self.rect = pygame.Rect(50, 32, 380, 208)

    def update(self, dt, mouse):
        self.mouse = mouse

    def on_key(self, ev):
        if ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE): self.on_close()

    def on_click(self, pos):
        if pygame.Rect(180, 209, 120, 20).collidepoint(pos): self.on_close()

    def draw(self, surf):
        u = self.ui
        surf.blit(u.dim, (0, 0)); u.draw_panel(surf, self.rect)
        u.text(surf, "HELLO, LITTLE FRIEND!", (240, 44), INK, 2, WHITE, "midtop")
        lines = ["CLICK THE FLOOR TO WALK. ARROWS WORK TOO!", "F FEEDS   P PLAYS   E PETS   H GOES TO BED",
                 "G OPENS GAMES. B OPENS PETS, STYLE & SHOP.", "D SENDS YOUR PET ONTO THE WINDOWS DESKTOP.",
                 "DRAG ITEMS. RIGHT-CLICK: FURNITURE / DECOR.", "V: MOVE ROOM ITEMS. DELETE: PUT AWAY.",
                 "R: FAMILY   J: ADVENTURES   V: DECORATE", "DAILY CARE = 12 COINS. NO CLICK FARMING.",
                 "3 ARCADE LIVES. 1 REFILLS EVERY 30 MIN."]
        for i, line in enumerate(lines): u.text(surf, line, (65, 74 + i * 14), INK)
        u.small_button(surf, (180, 209, 120, 20), "LET'S PLAY!", False)


class ShopMenu:
    TABS = ("ITEMS", "PETS", "STYLE")
    def __init__(self, ui, pet, on_buy, on_close):
        self.ui, self.pet, self.on_buy, self.on_close = ui, pet, on_buy, on_close
        self.modal, self.mouse, self.sel, self.tab, self.page = True, None, 0, 0, 0
        self.rect = pygame.Rect(50, 18, 380, 234)

    @property
    def keys(self):
        if self.tab == 0: return list(SHOP_ITEMS)
        if self.tab == 1: return ["species:" + s for s in SPECIES_ORDER]
        return ["coat", "none"] + ["style:" + s for s in ACCESSORY_ORDER] + ["room:" + s for s in ROOMS]

    def _row(self, i):
        return pygame.Rect(60, 65 + i * 31, 360, 29)

    def tabs(self, i): return pygame.Rect(60 + i * 120, 43, 116, 17)

    def update(self, dt, mouse): self.mouse = mouse

    def on_key(self, ev):
        if ev.key in (pygame.K_ESCAPE, pygame.K_b): self.on_close()
        elif ev.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT):
            self.tab = (self.tab + (-1 if ev.key == pygame.K_LEFT else 1)) % 3
            self.sel = self.page = 0
        elif ev.key in (pygame.K_UP, pygame.K_DOWN):
            self.sel = (self.sel + (1 if ev.key == pygame.K_DOWN else -1)) % len(self.keys)
            self.page = self.sel // 5
        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE): self.on_buy(self.keys[self.sel])

    def on_click(self, pos):
        for i in range(3):
            if self.tabs(i).collidepoint(pos):
                self.tab, self.sel, self.page = i, 0, 0
                return
        for i, key in enumerate(self.keys[self.page * 5:self.page * 5 + 5]):
            if self._row(i).collidepoint(pos):
                self.sel = self.page * 5 + i
                self.on_buy(key)
                return
        if pygame.Rect(320, 223, 96, 17).collidepoint(pos) and len(self.keys) > 5:
            self.page = (self.page + 1) % ((len(self.keys) + 4) // 5)
            self.sel = self.page * 5
        elif not self.rect.collidepoint(pos): self.on_close()

    def info(self, key):
        p = self.pet
        if key in SHOP_ITEMS:
            d = SHOP_ITEMS[key]
            owned = p.inventory.get(key, 0)
            tag = "OWNED" if owned and not d.get("repeatable", True) else str(d["price"]) + " C"
            return d["name"], d["desc"], tag, None
        if key.startswith("species:"):
            sp = key.split(":")[1]; d = SPECIES[sp]
            tag = "ACTIVE" if sp == p.species else ("SELECT" if sp in p.owned_species else str(d["price"]) + " C")
            return d["name"], d["desc"], tag, self.ui.assets.pet_clips(sp)["idle"].frames[0]
        if key.startswith("style:"):
            s = key.split(":")[1]; d = ACCESSORIES[s]
            tag = "ON" if s == p.accessory else ("WEAR" if p.inventory.get(s) else str(d["price"]) + " C")
            return d["name"], "ONE HEAD ACCESSORY AT A TIME", tag, self.ui.assets.accessories[s]
        if key.startswith("room:"):
            s = key.split(":")[1]; name, level = ROOMS[s]
            if s in ROOM_PRICES:
                tag = ("ON" if p.room_theme == s else "SELECT") if s in p.owned_rooms else "%d C" % ROOM_PRICES[s]
                return name, "WALLS + FLOOR + BED + DESKTOP HOUSE", tag, None
            return name, "UNLOCK AT LEVEL %d" % level, ("ON" if p.room_theme == s else "SELECT") if s in p.owned_rooms else "LOCKED", None
        if key == "coat": return "COAT: " + petart.COATS[p.species][p.coat][0], "CLICK TO CYCLE THREE FREE COLOURS", "FREE", p.frame()
        return "NO ACCESSORY", "TAKE OFF YOUR HAT", "SELECT", None

    def draw(self, surf):
        u = self.ui
        surf.blit(u.dim, (0, 0)); u.draw_panel(surf, self.rect)
        u.text(surf, "LITTLE PET SHOP", (62, 25), INK, 2, WHITE)
        u.text(surf, "%d COINS" % self.pet.coins, (416, 28), GOLD, anchor="topright")
        for i, tab in enumerate(self.TABS): u.small_button(surf, self.tabs(i), tab, False, self.tab == i)
        for i, key in enumerate(self.keys[self.page * 5:self.page * 5 + 5]):
            r = self._row(i)
            if self.sel == self.page * 5 + i: surf.fill(CREAM_DK, r)
            name, desc, tag, img = self.info(key)
            if img: surf.blit(img, (r.x + 2, r.y + 2))
            x = r.x + 29 if img else r.x + 7
            u.text(surf, name, (x, r.y + 3), INK)
            u.text(surf, desc, (x, r.y + 17), GREY)
            u.text(surf, tag, (r.right - 5, r.y + 3), INK, anchor="topright")
        u.text(surf, "TAB: SWITCH  ESC: CLOSE", (63, 229), GREY)
        if len(self.keys) > 5: u.small_button(surf, (320, 223, 96, 17), "MORE >", False)
