"""User settings (sound, music, fps, fullscreen, volume, time of day)."""
import json
import os
from dataclasses import dataclass, asdict

from config import SAVE_DIR, SETTINGS_PATH

FPS_OPTIONS = (30, 60, 120)
TIME_MODES = ("real", "fast", "day", "night")


@dataclass
class Settings:
    sound: bool = True
    music: bool = True
    fps: int = 60
    fullscreen: bool = False
    volume: int = 70            # 0-100
    time_mode: str = "real"     # real clock / fast cycle / forced day / forced night
    voice: bool = True
    quiet: bool = False
    pet_scale: int = 3
    desktop: bool = False
    weather: str = "auto"

    @classmethod
    def load(cls):
        s = cls()
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if not isinstance(raw, dict):
                return s
            s.sound = bool(raw.get("sound", s.sound))
            s.music = bool(raw.get("music", s.music))
            s.fullscreen = bool(raw.get("fullscreen", s.fullscreen))
            fps = int(raw.get("fps", s.fps))
            s.fps = fps if fps in FPS_OPTIONS else 60
            s.volume = max(0, min(100, int(raw.get("volume", s.volume))))
            tm = raw.get("time_mode", s.time_mode)
            s.time_mode = tm if tm in TIME_MODES else "real"
            s.voice = bool(raw.get("voice", True))
            s.quiet = bool(raw.get("quiet", False))
            s.pet_scale = int(raw.get("pet_scale", 3))
            if s.pet_scale not in (2, 3, 4):
                s.pet_scale = 3
            s.desktop = bool(raw.get("desktop", False))
            weather = raw.get("weather", "auto")
            s.weather = weather if weather in ("auto", "clear", "rain", "snow") else "auto"
        except (OSError, ValueError, TypeError):
            pass                      # missing or corrupt -> defaults
        return s

    def save(self):
        try:
            os.makedirs(SAVE_DIR, exist_ok=True)
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except OSError:
            pass
