"""Free Plus installer entry point. Keep its saves separate from the Free edition."""
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

_SAVE_FILES = ("save_data.json", "settings.json")


def resolve_save_dir(base=None):
    """Use MyLittlePetPlus/save, migrating legacy MyLittlePetPlusTest saves if present."""
    configured = os.environ.get("MY_LITTLE_PET_SAVE_DIR")
    if configured:
        return configured
    root = Path(base) if base is not None else Path(os.environ.get("LOCALAPPDATA") or Path.home())
    target = root / "MyLittlePetPlus" / "save"
    legacy = root / "MyLittlePetPlusTest" / "save"
    target_has_data = any((target / name).is_file() for name in _SAVE_FILES)
    legacy_files = [legacy / name for name in _SAVE_FILES if (legacy / name).is_file()] if legacy.is_dir() else []
    if not target_has_data and legacy_files:
        try:
            target.mkdir(parents=True, exist_ok=True)
            for src in legacy_files:
                dst = target / src.name
                if not dst.is_file():
                    tmp = target / (src.name + ".tmp")
                    shutil.copy2(src, tmp)
                    os.replace(tmp, dst)
        except OSError:
            return str(legacy)
    return str(target)


if not (len(sys.argv) > 2 and sys.argv[1] == "--check-install") and not os.environ.get("MY_LITTLE_PET_SAVE_DIR"):
    os.environ["MY_LITTLE_PET_SAVE_DIR"] = resolve_save_dir()
os.environ["MY_LITTLE_PET_EDITION"] = "Plus - Free"
from main import main  # noqa: E402


def check_install(report):
    """Headless packaged-app smoke check, using only a temporary profile."""
    import json
    import tempfile
    import traceback

    os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    result = {"ok": False}
    try:
        with tempfile.TemporaryDirectory(dir=Path(report).resolve().parent) as tmp:
            os.environ["MY_LITTLE_PET_SAVE_DIR"] = tmp
            from game import Game
            from save_system import default_data
            from supplies import TOYS

            g = Game()
            g.start_session(default_data("Mochi", "Tester"), False)
            g.overlay = None
            for key in TOYS:
                g.pet.selected_toy = key
                g.pet.energy = 90
                g.brain._start_play()
                for _ in range(30):
                    g.brain.update(1 / 60)
                    g.draw()
            g.shutdown()
            result = {"ok": True, "toys": list(TOYS), "edition": "Plus Free"}
    except Exception:
        result["error"] = traceback.format_exc()
    Path(report).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(check_install(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--check-install" else main())
