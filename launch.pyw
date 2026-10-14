"""Double-click launcher. Uses local dependencies; logs errors instead of hiding them."""
import os
import sys
import traceback
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path[:0] = [str(root / ".runtime"), str(root / "teja-pet")]
os.chdir(root / "teja-pet")
try:
    from main import main
    main()
except Exception:
    (root / "launch-error.log").write_text(traceback.format_exc(), encoding="utf-8")
    if os.name == "nt":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, "Teja Pet could not start. See launch-error.log in the project folder.", "Teja Pet", 0x10)
