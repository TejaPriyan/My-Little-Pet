"""Export TEJA PET's procedural placeholder art and sounds as real files.

    python tools/generate_assets.py

Creates every PNG/WAV under assets/ using the exact file layout the game
loads. Edit or replace any file with your own art (keep the frame sizes) and
the game will use it automatically; delete a file and the game falls back to
the built-in placeholder.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pygame  # noqa: E402

import audio  # noqa: E402
from assets import file_specs  # noqa: E402
from config import ASSET_DIR  # noqa: E402
from sprites import strip  # noqa: E402


def main():
    count = 0
    for rel, (factory, _fw) in file_specs().items():
        made = factory()
        surf = strip(made) if isinstance(made, list) else made
        path = os.path.join(ASSET_DIR, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pygame.image.save(surf, path)
        count += 1
    os.makedirs(os.path.join(ASSET_DIR, "audio"), exist_ok=True)
    for name in audio.SFX + ("music",):
        audio.write_wav(os.path.join(ASSET_DIR, "audio", name + ".wav"), audio.synth(name))
        count += 1
    print("Wrote %d asset files to %s" % (count, ASSET_DIR))


if __name__ == "__main__":
    main()
