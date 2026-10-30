"""Stable furniture identities shared by the room editor and desktop inventory."""
BASE_DECOR = {
    'bed': ('COZY BED', 0), 'toy': ('CURRENT TOY', 0),
    'room_plant': ('ROOM PLANT', 0), 'table': ('FLOWER TABLE', 0),
    'food': ('FOOD BOWL', 0), 'water': ('WATER BOWL', 0),
    'room_rug': ('ROOM RUG', 0), 'room_cushion': ('ROOM PILLOW', 0),
    'garden_1': ('GARDEN PLANT 1', 0), 'garden_2': ('GARDEN PLANT 2', 0),
    'garden_3': ('GARDEN PLANT 3', 0),
}
DECOR = {**BASE_DECOR, 'rug': ('PICNIC RUG', 45), 'plant': ('EXTRA PLANT', 55),
         'cushion': ('SOFT PILLOW', 70), 'flowers': ('FLOWER VASE', 60),
         'lamp': ('HONEY LAMP', 85), 'books': ('STORY SHELF', 120)}
BASE_POS = {'bed': (14, 102), 'toy': (292, 220), 'room_plant': (436, 100),
            'table': (326, 108), 'food': (400, 214), 'water': (428, 214),
            'room_rug': (170, 164), 'room_cushion': (286, 176),
            'garden_1': (170, 105), 'garden_2': (275, 105), 'garden_3': (374, 105)}
PROP_NAMES = {'bed': 'bed', 'table': 'table', 'room_plant': 'plant', 'food': 'food',
              'water': 'water', 'room_rug': 'rug', 'room_cushion': 'cushion'}
COLLIDERS = {'bed': (0, 14, 64, 26), 'table': (3, 22, 30, 10),
             'room_plant': (4, 24, 16, 10), 'food': (2, 4, 12, 6), 'water': (2, 4, 12, 6)}


def decor_image(assets, key, theme='classic', toy='ball', food='kibble'):
    if key in assets.extra_decor: return assets.extra_decor[key]
    if key in ('plant', 'room_plant') or key.startswith('garden_'): return assets.plant[0]
    return {'bed': assets.room_style(theme)['bed'], 'toy': assets.toys[toy],
            'rug': assets.rug, 'room_rug': assets.rug, 'table': assets.table,
            'food': assets.meals[food][0], 'water': assets.water[0],
            'cushion': assets.decor['cushion'], 'room_cushion': assets.decor['cushion']}[key]


def visible_in_room(pet, key):
    if key in pet.room_hidden: return False
    if key in BASE_DECOR:
        return not key.startswith('garden_') or pet.room_theme == 'garden' or key in pet.room_layout
    return key in pet.owned_decor and key in pet.room_layout


def room_position(pet, key):
    return list(pet.room_layout.get(key, BASE_POS.get(key, (200, 160))))
