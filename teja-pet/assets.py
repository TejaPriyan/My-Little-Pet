"""Asset loading with graceful procedural fallbacks.

Every asset is looked up on disk first (assets/...png). If a file is missing or
unreadable, the matching painter in sprites.py / petart.py generates it in
memory, so the game is always playable. Replace any PNG with your own art (same
frame size) and it is picked up automatically - no code changes needed.
"""
import os

import pygame

import petart
import sprites
from config import ASSET_DIR, FRAME, SPECIES_ORDER


class Clip:
    """One animation: frames (+ optional blink variants) played at `fps`.
    `anchors` holds the head-top point of every frame (for accessories)."""
    __slots__ = ("frames", "blink", "fps", "anchors")

    def __init__(self, frames, fps, blink=None, anchors=None):
        self.frames = frames
        self.blink = blink
        self.fps = fps
        self.anchors = anchors or [(FRAME // 2, 3)] * len(frames)


def _pet_factory(species, clip):
    return lambda: petart.make_clip(species, clip)


# relative path -> (factory, frame width or None).  Used by the loader and
# by tools/generate_assets.py so both always agree on the file layout.
def file_specs():
    specs = {}
    for sp in SPECIES_ORDER:
        for clip in petart.PET_CLIPS:
            specs["sprites/pet/%s/%s.png" % (sp, clip)] = (_pet_factory(sp, clip), FRAME)
    specs.update({
        "environment/room.png": (sprites.make_room, None),
        "environment/bed.png": (sprites.make_bed, None),
        "environment/food.png": (sprites.make_food, 16),
        "environment/water.png": (sprites.make_water, 16),
        "environment/toy.png": (sprites.make_toy, None),
        "environment/table.png": (sprites.make_table, None),
        "environment/plant.png": (sprites.make_plant, 24),
        "environment/window.png": (sprites.make_window, None),
        "environment/door.png": (sprites.make_door, None),
        "environment/rug.png": (sprites.make_rug, None),
        "environment/decorations.png": (sprites.make_decorations, None),
        "environment/house.png": (sprites.make_house, None),
        "ui/panels.png": (sprites.make_panel, None),
        "ui/buttons.png": (sprites.make_buttons, 16),
        "ui/icons.png": (lambda: sprites.make_icons()[1], 9),
        "ui/fx.png": (sprites.make_fx, 7),
        "ui/treats.png": (sprites.make_treats, 12),
        "sprites/shadow.png": (sprites.make_shadow, None),
    })
    for name in sprites.ACCESSORY_ART:
        specs["sprites/accessories/%s.png" % name] = (
            (lambda n=name: sprites.make_accessories()[n]), None)
    return specs


def _slice(img, fw):
    n = max(1, img.get_width() // fw)
    return [img.subsurface(pygame.Rect(i * fw, 0, fw, img.get_height())).copy() for i in range(n)]


class Assets:
    def __init__(self):
        self.fallbacks = []          # files that had to be generated in memory
        self.specs = file_specs()

        # base (coat 0) frames per species; coats are palette-swapped lazily
        self._base = {}
        for sp in SPECIES_ORDER:
            self._base[sp] = {clip: self._get("sprites/pet/%s/%s.png" % (sp, clip))
                              for clip in petart.PET_CLIPS}
        self._pet_cache = {}
        self.pet = self.pet_clips("cat", 0)       # default set (icon, name screen)

        self.room = self._get("environment/room.png", opaque=True)
        self.bed = self._get("environment/bed.png")
        self.food = self._get("environment/food.png")
        self.water = self._get("environment/water.png")
        self.toy = self._get("environment/toy.png")
        self.table = self._get("environment/table.png")
        self.plant = self._get("environment/plant.png")
        self.window = self._get("environment/window.png")
        self.door = self._get("environment/door.png")
        self.rug = self._get("environment/rug.png")
        self.house = self._get("environment/house.png")

        deco = self._get("environment/decorations.png")
        self.decor = {k: deco.subsurface(pygame.Rect(*r)).copy()
                      for k, r in sprites.DECOR_SLICES.items()}

        self.panel = self._get("ui/panels.png")
        self.buttons = self._get("ui/buttons.png")
        names = list(sprites.ICONS)
        icons = self._get("ui/icons.png")
        if len(icons) < len(names):              # older icon sheet: fill in new icons
            icons = list(icons) + _slice(sprites.make_icons()[1], 9)[len(icons):]
        self.icons = {n: icons[i] for i, n in enumerate(names) if i < len(icons)}
        fx = self._get("ui/fx.png")
        self.fx = {n: fx[i] for i, n in enumerate(sprites.FX_NAMES) if i < len(fx)}
        treats = self._get("ui/treats.png")
        self.treats = {n: treats[i % len(treats)] for i, n in enumerate(sprites.TREAT_NAMES)}
        self.shadow = self._get("sprites/shadow.png")
        self.accessories = {n: self._get("sprites/accessories/%s.png" % n)
                            for n in sprites.ACCESSORY_ART}
        self._scaled = {}

    # ------------------------------------------------------------------ pets
    def pet_clips(self, species, coat=0):
        """Dict clip-name -> Clip for a species/coat (cached)."""
        if species not in self._base:
            species = "cat"
        coat = max(0, min(coat, len(petart.COATS[species]) - 1))
        key = (species, coat)
        clips = self._pet_cache.get(key)
        if clips is not None:
            return clips
        clips = {}
        for name, (fps, has_blink) in petart.PET_CLIPS.items():
            frames = petart.recolor(self._base[species][name], species, coat)
            anchors = petart.clip_anchors(species, name)
            blink = None
            if has_blink and len(frames) >= 2 and len(frames) % 2 == 0:
                half = len(frames) // 2
                frames, blink = frames[:half], frames[half:]
                anchors = anchors[:half]
            if len(anchors) < len(frames):
                anchors = (anchors * len(frames))[:len(frames)] if anchors else None
            clips[name] = Clip(frames, fps, blink, anchors)
        for d in ("up", "left", "right"):            # still "looking" poses
            w = clips["walk_" + d]
            clips["stand_" + d] = Clip([w.frames[0]], 1.0, None, [w.anchors[0]])
        self._pet_cache[key] = clips
        return clips

    def scaled(self, img, factor):
        """Nearest-neighbour upscale with caching (previews, desktop icons)."""
        key = (id(img), factor)
        out = self._scaled.get(key)
        if out is None:
            w, h = img.get_size()
            out = self._scaled[key] = pygame.transform.scale(img, (w * factor, h * factor))
        return out

    # ------------------------------------------------------------------
    def _get(self, rel, opaque=False):
        factory, fw = self.specs[rel]
        img = self._load_file(rel, opaque)
        if img is None:
            self.fallbacks.append(rel)
            img = factory()
        if isinstance(img, list):
            return img
        if fw:
            return _slice(img, fw)
        return img

    @staticmethod
    def _load_file(rel, opaque):
        path = os.path.join(ASSET_DIR, *rel.split("/"))
        if not os.path.isfile(path):
            return None
        try:
            img = pygame.image.load(path)
            try:
                img = img.convert() if opaque else img.convert_alpha()
            except pygame.error:
                pass                     # no display yet (tools) - keep raw
            return img
        except (pygame.error, OSError):
            return None
