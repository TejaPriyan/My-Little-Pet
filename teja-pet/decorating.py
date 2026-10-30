"""Select existing furniture, drag a preview, and put owned items away safely."""
import pygame
from furniture import DECOR, BASE_DECOR, BASE_POS, PROP_NAMES, COLLIDERS, decor_image, visible_in_room, room_position
from config import INK, GOLD


def apply_layout(world, pet):
    from world import Prop
    for key, name in PROP_NAMES.items():
        prop = getattr(world, name)
        x, y = room_position(pet, key)
        x, y = max(14, min(464 - prop.rect.w, x)), max(100, min(188 if key == 'bed' else 236 - prop.rect.h, y))
        if key in pet.room_layout: pet.room_layout[key] = [x, y]
        prop.x, prop.y = x, y
        prop.rect.topleft = (x, y)
        prop.sort_y = prop.rect.bottom
        prop.visible = visible_in_room(pet, key)
        if key in COLLIDERS:
            dx, dy, w, h = COLLIDERS[key]
            prop.collider = pygame.Rect(x + dx, y + dy, w, h)
    world.toy_home = tuple(room_position(pet, 'toy'))
    world.toy[:] = world.toy_home
    world.toy_visible = visible_in_room(pet, 'toy')
    world.extra_props = []
    for key in DECOR:
        if key in PROP_NAMES or key == 'toy' or not visible_in_room(pet, key): continue
        prop = Prop(key, decor_image(world.assets, key, pet.room_theme), room_position(pet, key))
        if key in ('rug', 'cushion'): prop.sort_y = 99
        world.extra_props.append(prop)
    world._build_grid()
    bed = world.bed
    def stand(x, y):
        return (x, y) if world.is_free(x, y) else world.nearest_free(x, y) or (240, 190)
    approach = stand(bed.x + 34, bed.y + 50)
    world.anchors['bed_approach'] = approach
    world.anchors['bed_spot'] = (bed.x + 22, bed.y + 25) if bed.visible else approach
    for key, offset in (('food', (-14, 8)), ('water', (24, 8))):
        prop = getattr(world, key)
        world.anchors[key] = stand(prop.x + offset[0], prop.y + offset[1])
    for key in ('plant', 'table', 'cushion'):
        prop = getattr(world, key)
        point = world.nearest_free(prop.rect.centerx, prop.rect.bottom + 12) or (240, 190)
        world.landmarks[key] = (point, world.landmarks[key][1])


def draw_decor(surf, assets, pet):
    # Furniture now uses World's depth-sorted draw list.
    pass


class Decorator:
    modal = True

    def __init__(self, game):
        self.game, self.ui = game, game.ui
        self.key = 'bed'
        self.xy = room_position(game.pet, 'bed')
        self.message = 'CLICK AN ITEM. DRAG TO MOVE. DELETE PUTS IT AWAY.'
        self.mouse = None
        self.page = 0
        self.dragging = self.drag_moved = False
        self.show_preview = True
        self.offset = (0, 0)

    def image(self, key=None):
        p = self.game.pet
        return decor_image(self.game.assets, key or self.key, p.room_theme, p.selected_toy, p.selected_food)

    def rect(self, key, xy=None):
        x, y = xy or room_position(self.game.pet, key)
        if key == 'toy': x, y = x - 8, y - 12
        return self.image(key).get_rect(topleft=(x, y))

    def choose(self, key):
        self.show_preview = True
        self.key, self.xy = key, room_position(self.game.pet, key)
        self.page = list(DECOR).index(key) // 4
        self.message = DECOR[key][0] + (' - IN INVENTORY' if not visible_in_room(self.game.pet, key) else ' - DRAG TO MOVE')

    def move(self, pos):
        self.show_preview = True
        w, h = self.image().get_size()
        if self.key == 'toy':
            self.xy = [max(24, min(452, int(pos[0]))), max(118, min(232, int(pos[1])))]
        else:
            self.xy = [max(14, min(464 - w, int(pos[0]))), max(100, min(188 if self.key == 'bed' else 236 - h, int(pos[1])))]

    def refresh(self):
        g, p = self.game, self.game.pet
        apply_layout(g.world, p)
        from ai import Brain
        for member in [p] + g.household.friends:
            member.hidden = member.on_bed = member.carried = False
            member.z = 0
            if not g.world.is_free(member.x, member.y):
                member.x, member.y = g.world.nearest_free(member.x, member.y) or (240, 190)
        g.brain = Brain(p, g.world, g.fx, g._on_event)
        g.household.activities.clear(); g.household.targets.clear()
        g.save_now()

    def place(self):
        g, p = self.game, self.game.pet
        cost = 0 if self.key in p.owned_decor else DECOR[self.key][1]
        if p.coins < cost:
            self.message = 'NOT ENOUGH COINS. PREVIEW IS FREE.'
            return False
        self.move(self.xy)
        if self.key in COLLIDERS:
            dx, dy, w, h = COLLIDERS[self.key]
            r = pygame.Rect(self.xy[0] + dx, self.xy[1] + dy, w, h).inflate(8, 4)
            current = getattr(g.world, PROP_NAMES[self.key])
            if any(r.colliderect(prop.collider) for prop in g.world.floor_props if prop is not current and prop.visible and prop.collider):
                self.message = 'LEAVE A LITTLE SPACE AROUND THE FURNITURE.'
                return False
        p.coins -= cost
        if self.key not in p.owned_decor: p.owned_decor.append(self.key)
        p.room_layout[self.key] = list(self.xy)
        if self.key in p.room_hidden: p.room_hidden.remove(self.key)
        self.refresh()
        self.message = 'SAVED! MOVING AND RESTORING OWNED ITEMS IS FREE.'
        return True

    def put_away(self):
        p = self.game.pet
        if self.key not in p.owned_decor: return
        if self.key not in p.room_hidden: p.room_hidden.append(self.key)
        self.dragging = False
        self.refresh()
        self.show_preview = False
        self.message = 'PUT AWAY. SELECT IT AND PLACE TO BRING IT BACK.'

    def update(self, dt, mouse): self.mouse = mouse

    def on_key(self, ev):
        if ev.key == pygame.K_ESCAPE: self.game._close_overlay()
        elif ev.key == pygame.K_TAB: self.page = (self.page + 1) % ((len(DECOR) + 3) // 4)
        elif ev.key in (pygame.K_DELETE, pygame.K_BACKSPACE): self.put_away()
        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER): self.place()
        elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            self.move((self.xy[0] + (5 if ev.key == pygame.K_RIGHT else -5 if ev.key == pygame.K_LEFT else 0),
                       self.xy[1] + (5 if ev.key == pygame.K_DOWN else -5 if ev.key == pygame.K_UP else 0)))

    def on_click(self, pos):
        if pygame.Rect(388, 51, 78, 22).collidepoint(pos):
            self.page = (self.page + 1) % ((len(DECOR) + 3) // 4); return
        for i, key in enumerate(list(DECOR)[self.page*4:self.page*4+4]):
            if pygame.Rect(12 + i * 93, 51, 90, 22).collidepoint(pos): self.choose(key); return
        if pygame.Rect(300, 237, 162, 23).collidepoint(pos): self.place(); return
        if pygame.Rect(90, 237, 112, 23).collidepoint(pos): self.put_away(); return
        if pygame.Rect(15, 237, 65, 23).collidepoint(pos): self.game._close_overlay(); return
        if not 100 <= pos[1] < 237: return
        candidates = [key for key in DECOR if visible_in_room(self.game.pet, key) and self.rect(key).collidepoint(pos)]
        if candidates:
            key = max(candidates, key=lambda k: self.rect(k).bottom if k not in ('rug', 'room_rug') else 0)
            self.choose(key)
            self.offset = (pos[0] - self.xy[0], pos[1] - self.xy[1])
            self.dragging, self.drag_moved = True, False
        else: self.move(pos)

    def on_motion(self, pos):
        if self.dragging:
            old = list(self.xy)
            self.move((pos[0] - self.offset[0], pos[1] - self.offset[1]))
            self.drag_moved = self.drag_moved or self.xy != old

    def on_release(self, pos):
        if self.dragging:
            self.on_motion(pos)
            self.dragging = False
            if self.drag_moved: self.place()

    def draw(self, surf):
        u, p = self.ui, self.game.pet
        u.draw_panel(surf, (5, 31, 470, 49))
        u.text(surf, 'EDIT YOUR ROOM', (16, 38), INK)
        u.text(surf, '%d COINS' % p.coins, (463, 38), GOLD, anchor='topright')
        for i, (key, (label, price)) in enumerate(list(DECOR.items())[self.page*4:self.page*4+4]):
            u.small_button(surf, (12 + i * 93, 51, 90, 22), label, False, key == self.key)
        u.small_button(surf, (388, 51, 78, 22), 'MORE %d/%d' % (self.page+1, (len(DECOR)+3)//4), False)
        r = self.rect(self.key, self.xy)
        if self.show_preview:
            surf.blit(self.image(), r)
            pygame.draw.rect(surf, GOLD, r.inflate(2, 2), 1)
        u.draw_panel(surf, (5, 237, 470, 30))
        u.draw_panel(surf, (5, 80, 470, 18))
        u.text(surf, self.message, (240, 86), INK, anchor='midtop')
        price = 0 if self.key in p.owned_decor else DECOR[self.key][1]
        u.small_button(surf, (300, 237, 162, 23), 'PLACE FREE' if not price else 'BUY + PLACE %d COINS' % price, False)
        u.small_button(surf, (15, 237, 65, 23), 'DONE', False)
        u.small_button(surf, (90, 237, 112, 23), 'PUT AWAY', False)
        u.text(surf, 'V: EDIT', (224, 245), INK)
