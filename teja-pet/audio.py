"""Sound effects and music.

Looks for assets/audio/<name>.wav first; if missing, a tiny synthesizer builds
a subtle placeholder in memory. If no audio device exists the game simply runs
silent (never crashes).
"""
import array
import io
import math
import os
import random
import wave

import pygame

from config import ASSET_DIR

SR = 22050
SFX = ("walk", "eat", "happy", "sleep", "click", "levelup", "catch", "award",
       "meow", "purr", "woof", "squeak", "yip", "coin", "pop")


# ------------------------------------------------------------------ synthesis
def _tone(freq, dur, vol=0.4, shape="sine", decay=6.0):
    n = int(SR * dur)
    out = []
    for i in range(n):
        t = i / SR
        ph = 2 * math.pi * freq * t
        if shape == "tri":
            v = 2 / math.pi * math.asin(math.sin(ph))
        elif shape == "square":
            v = 0.6 if math.sin(ph) > 0 else -0.6
        else:
            v = math.sin(ph)
        env = math.exp(-decay * i / n) * min(1.0, i / (SR * 0.004))
        out.append(v * env * vol)
    return out


def _noise(dur, vol=0.4, lp=0.3, seed=1):
    rng = random.Random(seed)
    n = int(SR * dur)
    y, out = 0.0, []
    for i in range(n):
        y += lp * (rng.uniform(-1, 1) - y)
        out.append(y * math.exp(-8 * i / n) * vol * 3)
    return out


def _silence(dur):
    return [0.0] * int(SR * dur)


def _pcm(samples):
    a = array.array("h", (int(max(-1.0, min(1.0, s)) * 32000) for s in samples))
    return a.tobytes()


def _music():
    beat = 60.0 / 84.0
    chords = [(261.63, [1, 1.26, 1.5, 2]), (220.0, [1, 1.2, 1.5, 2]),
              (174.61, [1, 1.26, 1.5, 2]), (196.0, [1, 1.25, 1.5, 2])]
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]
    total = int(SR * beat * 16)
    buf = [0.0] * (total + SR)
    step = beat / 2
    pos = 0
    for root, ratios in chords:
        pad = _tone(root / 2, beat * 4, 0.07, "sine", 0.8)
        for i, s in enumerate(pad):
            buf[pos + i] += s
        # Soft sustained fifth plus a low pulse gives the loop a fuller bed.
        fifth = _tone(root * 1.5, beat * 4, 0.025, "sine", 1.5)
        for i, s in enumerate(fifth): buf[pos + i] += s
        for k in (0, 2):
            bass = _tone(root / 4, beat * 1.5, .06, "sine", 2.5)
            start = pos + int(SR * beat * k)
            for i, s in enumerate(bass): buf[start + i] += s
        for k, idx in enumerate(pattern):
            note = _tone(root * ratios[idx] * 2, 0.55, 0.12, "tri", 3.0)
            start = pos + int(SR * step * k)
            for i, s in enumerate(note):
                buf[start + i] += s
        pos += int(SR * beat * 4)
    for i in range(SR):                      # wrap the tail onto the start: seamless loop
        buf[i] += buf[total + i]
    return buf[:total]


def synth(name):
    """Return 16-bit mono PCM bytes for a named sound."""
    if name in ("meow", "woof", "squeak", "yip", "purr"):
        base, duration = {"meow": (520, .42), "woof": (160, .22), "squeak": (1150, .18),
                          "yip": (740, .24), "purr": (85, .65)}[name]
        s = []
        phase = 0.0
        for i in range(int(SR * duration)):
            t = i / SR
            u = t / duration
            phase += 2 * math.pi * base * (1 + .35 * math.sin(u * math.pi * 1.5)) / SR
            v = math.sin(phase) + .25 * math.sin(2 * phase)
            env = math.sin(math.pi * u) ** 1.5
            if name == "purr":
                env *= .5 + .5 * math.sin(2 * math.pi * 24 * t)
            s.append(v * env * .25)
    elif name == "coin":
        s = _tone(1320, .07, .2) + _tone(1760, .15, .2)
    elif name == "pop":
        s = _tone(360, .07, .25, "sine", 8)
    elif name == "click":
        s = _tone(1400, 0.045, 0.3, "square", 8)
    elif name == "walk":
        s = _noise(0.04, 0.18, 0.15, seed=3)
    elif name == "eat":
        s = []
        for k in range(3):
            s += _noise(0.055, 0.45, 0.5, seed=k + 5) + _silence(0.06)
    elif name == "happy":
        s = _tone(660, 0.09, 0.35, "tri", 3) + _tone(880, 0.16, 0.35, "tri", 4)
    elif name == "sleep":
        s = _tone(392, 0.35, 0.25, "sine", 3) + _tone(330, 0.5, 0.22, "sine", 4)
    elif name == "levelup":
        s = []
        for f, d in ((523, 0.11), (659, 0.11), (784, 0.11), (1047, 0.4)):
            s += _tone(f, d, 0.35, "tri", 3)
    elif name == "catch":
        s = _tone(880, 0.07, 0.35, "tri", 4) + _tone(1174, 0.12, 0.4, "sine", 5)
    elif name == "award":
        s = _tone(523, 0.09, 0.35, "tri", 3) + _tone(659, 0.09, 0.35, "tri", 3) + _tone(784, 0.09, 0.35, "tri", 3) + _tone(1046, 0.3, 0.4, "sine", 3)
    elif name == "music":
        s = _music()
    else:
        raise KeyError(name)
    return _pcm(s)


def write_wav(target, pcm):
    """Write 16-bit mono PCM to a path or file-like object as a WAV."""
    with wave.open(target, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)


def wav_file(name):
    """Synthesized sound as an in-memory WAV. Loading it through pygame lets
    SDL convert to whatever format the audio device actually opened with."""
    buf = io.BytesIO()
    write_wav(buf, synth(name))
    buf.seek(0)
    return buf


# ------------------------------------------------------------------ playback
class Audio:
    def __init__(self, settings):
        self.settings = settings
        self.ok = False
        self._snd = {}
        self._music = None
        self._music_playing = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(SR, -16, 1, 512)
            self.ok = True
        except (pygame.error, NotImplementedError, OSError):
            self.ok = False

    def _load(self, name):
        if name in self._snd:
            return self._snd[name]
        snd = None
        path = os.path.join(ASSET_DIR, "audio", name + ".wav")
        try:
            if os.path.isfile(path):
                snd = pygame.mixer.Sound(file=path)
        except (pygame.error, OSError):
            snd = None
        if snd is None:
            try:
                snd = pygame.mixer.Sound(file=wav_file(name))
            except (pygame.error, OSError, KeyError):
                snd = None
        self._snd[name] = snd
        return snd

    def play(self, name, vol=1.0):
        if not (self.ok and self.settings.sound) or getattr(self.settings, "quiet", False):
            return
        snd = self._load(name)
        if snd:
            snd.set_volume(max(0.0, min(1.0, vol * self.settings.volume / 100.0)))
            snd.play()

    def apply_settings(self):
        """Start/stop music and refresh volume after a settings change."""
        if not self.ok:
            return
        want = self.settings.music and not getattr(self.settings, "quiet", False)
        if want:
            if self._music is None:
                self._music = self._load("music")
            if self._music:
                self._music.set_volume(self.settings.volume / 100.0 * 0.3)
                if not self._music_playing:
                    self._music.play(loops=-1)
                    self._music_playing = True
        elif self._music and self._music_playing:
            self._music.stop()
            self._music_playing = False
