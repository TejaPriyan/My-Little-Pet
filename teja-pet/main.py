"""TEJA PET - a cozy pixel-art desktop virtual pet.

Run with:  python main.py
"""
import os
import sys

# Make sure local modules import correctly no matter where we're launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("TEJA PET needs pygame. Install it with:\n    pip install -r requirements.txt")
        return 1
    from config import SAVE_DIR
    from instance import SingleInstance
    instance = SingleInstance(SAVE_DIR)
    try:
        if instance.already_running:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, "Your pet is already running. Look for My Little Pet on your taskbar or desktop.", "My Little Pet", 64)
            return 0
        from game import Game
        game = Game()
        if "--desktop" in sys.argv and game.session:
            game.enter_desktop()
        game.run()
    finally:
        instance.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
