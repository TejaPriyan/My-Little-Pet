"""Desktop furniture inventory: one persistent instance of each owned item."""
import pygame
from furniture import DECOR, decor_image


class DesktopFurniture:
    def init_furniture(self, layout):
        self.furniture = {}
        self.items_hidden = layout.get('items_hidden', False)
        self.pets_hidden = layout.get('pets_hidden', False)
        self.put_away = set(layout.get('put_away', []))
        for key, xy in layout.get('furniture', {}).items():
            if key in DECOR and key in self.pet.owned_decor:
                r = self.furniture_image(key).get_rect(topleft=(xy[0] * self.w, xy[1] * self.h))
                self.clamp_rect(r)
                self.furniture[key] = r
        self.menu_mode = 'actions'
        self.context_item = None

    def furniture_image(self, key):
        p = self.pet
        return decor_image(self.game.assets, key, p.room_theme, p.selected_toy, p.selected_food)

    def prop_rect(self, key):
        return self.furniture[key[1:]] if key.startswith('@') else getattr(self, key)

    def visible_props(self):
        basics = [k for k in ('home', 'food', 'water', 'ball') if k not in self.put_away and not (k == 'home' and self.hidden)]
        if self.items_hidden: return [k for k in basics if k == 'home']
        return basics + ['@' + k for k in self.furniture]

    def visible_pets(self):
        return [] if self.pets_hidden else [self.pet] + self.game.household.visible

    def recovery_visible(self):
        return 'home' not in self.visible_props() or self.items_hidden or self.pets_hidden

    def recovery_rect(self):
        return pygame.Rect(max(2, self.w - 78), self.h - 26, 74, 20)

    def visibility_command(self, action):
        if action == 'visibility':
            self.open_menu(getattr(self, 'menu_origin', self.window.mouse()), 'visibility')
            return True
        if action not in ('toggle_items', 'toggle_pets', 'showitems', 'showpets', 'hideall', 'showall'): return False
        self.cancel_drag()
        self.follow = False; self.target = None; self.wake()
        if action == 'toggle_items': self.items_hidden = not self.items_hidden
        elif action == 'toggle_pets': self.pets_hidden = not self.pets_hidden
        elif action == 'showitems': self.items_hidden = False
        elif action == 'showpets': self.pets_hidden = False; self.pet.solo = False
        elif action == 'hideall': self.hidden = self.items_hidden = self.pets_hidden = True
        elif action == 'showall':
            self.hidden = self.items_hidden = self.pets_hidden = False
            self.put_away.clear()
            self.pet.solo = False
        if not self.pets_hidden:
            for member in [self.pet] + self.game.household.friends:
                member.hidden = member.carried = member.on_bed = False; member.z = 0
                member.x, member.y = self.clamp((member.x, member.y))
        self.game.household.targets.clear(); self.game.household.activities.clear()
        self.window.show()
        self.save_layout()
        return True

    def item_at(self, pos):
        return next((k for k in reversed(self.visible_props()) if self.prop_rect(k).collidepoint(pos)), None)

    def menu_entries(self):
        if self.menu_mode == 'size':
            from settings import PET_SIZES
            return [('size:' + str(scale), name + (' (SELECTED)' if scale == self.game.settings.pet_scale else ''))
                    for scale, name in PET_SIZES.items()] + [('actions', 'BACK TO PET MENU')]
        if self.menu_mode == 'visibility':
            return [('hide' if 'home' in self.visible_props() else 'showhome',
                     'HIDE HOUSE' if 'home' in self.visible_props() else 'SHOW HOUSE'),
                    ('toggle_items', 'SHOW ITEMS' if self.items_hidden else 'HIDE ITEMS'),
                    ('toggle_pets', 'SHOW PETS' if self.pets_hidden else 'HIDE PETS'),
                    ('showall', 'SHOW EVERYTHING'), ('hideall', 'HIDE EVERYTHING'),
                    ('furniture', 'STORED ITEMS / FURNITURE'), ('actions', 'BACK TO PET MENU')]
        if self.menu_mode == 'furniture':
            entries = []
            for key, (name, price) in DECOR.items():
                if key in ('food', 'water', 'toy'):
                    basic = {'toy': 'ball'}.get(key, key)
                    entries.append(('toggle:' + basic, ('PUT AWAY ' if basic in self.visible_props() else 'ADD ') + name))
                    continue
                prefix = 'PUT AWAY ' if key in self.furniture else 'ADD ' if key in self.pet.owned_decor else 'BUY '
                entries.append(('furn:' + key, prefix + name + ((' %d' % price) if key not in self.pet.owned_decor else '')))
            return entries + [('actions', 'BACK TO PET MENU')]
        entries = list(self.ACTIONS)
        if self.context_item:
            entries.insert(0, ('remove_item', 'PUT THIS ITEM AWAY'))
        return entries

    def open_menu(self, pos, mode='actions'):
        self.menu_mode, self.menu_page = mode, 0
        height = 8 * 16 + 30
        self.menu = pygame.Rect(max(0, min(int(pos[0]), self.w - 200)), max(0, min(int(pos[1]), self.h - height)), 200, height)
        self.menu_origin = self.menu.topleft

    def new_furniture_rect(self, key):
        r = self.furniture_image(key).get_rect()
        occupied = [self.prop_rect(k).inflate(8, 8) for k in self.visible_props()]
        occupied += [self.pet_rect(p).inflate(16, 16) for p in [self.pet] + self.game.household.visible]
        candidates = [(self.pet.x + 25 + dx, self.pet.y - 45 + dy)
                      for dy in (0, -60, -120, 60) for dx in (0, 85, -85, 170, -170)]
        candidates += [(x, y) for y in range(30, self.h, 50) for x in range(10, self.w, 70)]
        for point in candidates:
            r.topleft = point; self.clamp_rect(r)
            if not any(r.colliderect(other) for other in occupied): break
        return r

    def furniture_command(self, action):
        if action in ('furniture', 'actions'):
            self.open_menu(getattr(self, 'menu_origin', self.window.mouse()), 'furniture' if action == 'furniture' else 'actions')
        elif action == 'remove_item':
            key = self.context_item
            if not key: return True
            if key.startswith('@'): self.furniture.pop(key[1:], None)
            else: self.put_away.add(key)
            self.target = None; self.wake(); self.save_layout()
            self.pet.say('STORED SAFELY. ADD IT BACK ANY TIME!')
        elif action.startswith('toggle:'):
            key = action.split(':', 1)[1]
            if key in self.put_away: self.put_away.remove(key)
            else: self.put_away.add(key)
            self.items_hidden = False
            self.save_layout(); self.open_menu(getattr(self, 'menu_origin', self.window.mouse()), 'furniture')
        elif action.startswith('furn:'):
            key = action.split(':', 1)[1]
            if key not in DECOR: return True
            if key in self.furniture:
                self.furniture.pop(key)
                self.target = None; self.wake()
                self.pet.say('KEPT IN YOUR INVENTORY!')
            else:
                cost = 0 if key in self.pet.owned_decor else DECOR[key][1]
                if self.pet.coins < cost:
                    self.pet.say('A FEW MORE COINS FIRST!'); return True
                self.pet.coins -= cost
                if key not in self.pet.owned_decor: self.pet.owned_decor.append(key)
                self.items_hidden = False
                self.furniture[key] = self.new_furniture_rect(key)
                self.pet.say('DRAG IT ANYWHERE. RIGHT-CLICK TO STORE!')
            self.save_layout()
            page = self.menu_page
            self.open_menu(getattr(self, 'menu_origin', self.window.mouse()), 'furniture')
            self.menu_page = page
        else: return False
        return True
