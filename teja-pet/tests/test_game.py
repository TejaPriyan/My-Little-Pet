"""Headless end-to-end tests for TEJA PET.

Uses real pygame when installed, otherwise the PIL-backed stand-in in
fake_pygame.py (input is injected through its harness). Run:

    python tests/test_game.py
"""
import json
import math
import os
import sys
import tempfile
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
try:
    import pygame                         # noqa: F401
    H = None
    raise ImportError                     # force the stub: tests need input injection
except ImportError:
    import fake_pygame
    pg = fake_pygame.install()
    H = pg._harness

import config                             # noqa: E402

SHOTS = os.environ.get("TEJA_SHOTS", os.path.join(tempfile.gettempdir(), "teja_shots"))
os.makedirs(SHOTS, exist_ok=True)


class Sim:
    """Boots a Game against a throw-away save folder and drives it frame by frame."""

    def __init__(self, save=None, raw_save=None, settings=None):
        self.tmp = tempfile.mkdtemp()
        config.SAVE_DIR = self.tmp
        config.SAVE_PATH = os.path.join(self.tmp, "save_data.json")
        config.SETTINGS_PATH = os.path.join(self.tmp, "settings.json")
        import save_system, settings as st
        save_system.SAVE_DIR, save_system.SAVE_PATH = self.tmp, config.SAVE_PATH
        st.SAVE_DIR, st.SETTINGS_PATH = self.tmp, config.SETTINGS_PATH
        if save is not None:
            with open(config.SAVE_PATH, "w") as f:
                json.dump(save, f)
        if raw_save is not None:
            with open(config.SAVE_PATH, "w") as f:
                f.write(raw_save)
        if settings:
            with open(config.SETTINGS_PATH, "w") as f:
                json.dump(settings, f)
        import game
        self.game_mod = game
        game.SaveSystem.__init__.__defaults__ = (config.SAVE_PATH,)
        H.pressed.clear()
        H.events.clear()
        H.mods = 0
        H.mouse = (0, 0)
        self.g = game.Game()

    # ---- driving
    def step(self, n=1, ms=16, draw=True):
        H.frame_ms = ms
        g = self.g
        for _ in range(n):
            g.handle_events()
            g.update(ms / 1000.0)
            if draw:
                g.draw()
                g.display.present(g.canvas)

    def until(self, cond, max_s=60, ms=33, draw=False):
        n = int(max_s * 1000 / ms)
        for i in range(n):
            self.step(1, ms, draw)
            if cond():
                return i * ms / 1000.0
        raise AssertionError("timed out after %ss" % max_s)

    def key(self, k, uni=""):
        H.events.append(pg.Event(pg.KEYDOWN, key=k, unicode=uni))

    def hold(self, *ks):
        for k in ks:
            H.pressed.add(k)
            H.events.append(pg.Event(pg.KEYDOWN, key=k, unicode=""))

    def release(self, *ks):
        for k in ks:
            H.pressed.discard(k)

    def click(self, x, y):
        s = self.g.display.scale
        H.events.append(pg.Event(pg.MOUSEBUTTONDOWN, button=1, pos=(x * s, y * s)))

    def mouse_to(self, x, y):
        s = self.g.display.scale
        H.mouse = (x * s, y * s)

    def start_new(self, name="Teja"):
        self.step(5)
        for ch in name:
            self.key(ord(ch.lower()), ch)
        self.step(2)
        self.key(pg.K_RETURN, "\r")
        self.until(lambda: self.g.session and not self.g.fade.busy, 5, 16)
        if type(self.g.overlay).__name__ == "Tutorial":
            self.g._finish_help()
        self.quiet()

    def quiet(self):
        """Wait for the intro to finish, then stop autonomous wandering."""
        self.until(lambda: self.g.brain.state.name == "IDLE", 10)
        self.g.brain.dur = 1e9

    def shot(self, name):
        self.g.canvas.im.resize((960, 540)).save(os.path.join(SHOTS, name + ".png"))

    @property
    def pet(self):
        return self.g.pet

    @property
    def brain(self):
        return self.g.brain

    @property
    def world(self):
        return self.g.world


def free_every_frame(sim, frames, ms=16):
    for _ in range(frames):
        sim.step(1, ms, draw=False)
        assert sim.world.is_free(sim.pet.x, sim.pet.y) or sim.pet.on_bed, \
            "pet entered an obstacle at %.1f,%.1f" % (sim.pet.x, sim.pet.y)


def track_jumps(sim, cond, max_s, max_speed=90.0, ms=33):
    """Run until cond(); assert the pet never moves faster than running speed."""
    last = (sim.pet.x, sim.pet.y)
    for _ in range(int(max_s * 1000 / ms)):
        sim.step(1, ms, draw=False)
        d = math.hypot(sim.pet.x - last[0], sim.pet.y - last[1])
        if sim.brain.state.name != "SLEEP":
            assert d <= max_speed * ms / 1000.0 * 1.15 + 0.5, "teleport of %.1fpx" % d
        last = (sim.pet.x, sim.pet.y)
        if cond():
            return
    raise AssertionError("timed out")


# ------------------------------------------------------------------ tests
def test_first_launch_and_save():
    s = Sim()
    s.step(5)
    assert s.g.overlay is not None and not s.g.session, "name screen should show"
    s.shot("01_name_screen")
    s.start_new("Teja")
    assert s.pet.name == "Teja"
    assert os.path.isfile(config.SAVE_PATH), "save file created on start"
    assert json.load(open(config.SAVE_PATH))["pet_name"] == "Teja"


def test_movement_and_animation():
    s = Sim(); s.start_new()
    s.pet.x, s.pet.y = 300.0, 190.0
    x0 = s.pet.x
    s.hold(pg.K_RIGHT); s.step(50, 16, False)
    assert s.pet.x > x0 + 20, "moved right"
    assert s.pet.facing == "right" and s.pet.anim.name == "walk_right"
    s.release(pg.K_RIGHT); s.step(30, 16, False)
    assert s.pet.anim.name in ("idle", "stand_right"), s.pet.anim.name
    y0 = s.pet.y
    s.hold(pg.K_UP); s.step(30, 16, False)
    assert s.pet.y < y0 and s.pet.anim.name == "walk_up"
    s.release(pg.K_UP)
    for k, face in ((pg.K_DOWN, "down"), (pg.K_LEFT, "left")):
        s.hold(k); s.step(20, 16, False)
        assert s.pet.anim.name == "walk_" + face, s.pet.anim.name
        s.release(k); s.step(30, 16, False)
    # diagonal movement is normalised (not faster)
    s.pet.x, s.pet.y = 240.0, 190.0
    s.hold(pg.K_RIGHT, pg.K_DOWN); s.step(60, 16, False)
    dist = math.hypot(s.pet.x - 240, s.pet.y - 190)
    assert 30 < dist < 40, "diagonal speed ~36px/s, got %.1f" % dist
    s.release(pg.K_RIGHT, pg.K_DOWN)
    # shift = run
    s.pet.x, s.pet.y = 100.0, 200.0
    H.mods = 3; s.hold(pg.K_RIGHT); s.step(60, 16, False)
    assert s.pet.x - 100 > 60, "running is faster"
    H.mods = 0; s.release(pg.K_RIGHT)


def test_collision_and_bounds():
    s = Sim(); s.start_new()
    s.pet.x, s.pet.y = 343.0, 170.0                      # below the table
    s.hold(pg.K_UP); free_every_frame(s, 200)
    assert s.pet.y >= 144 - 0.5, "stopped by table (y=%.1f)" % s.pet.y
    s.release(pg.K_UP)
    s.pet.x, s.pet.y = 100.0, 200.0
    s.hold(pg.K_LEFT); free_every_frame(s, 400)
    assert s.pet.x >= 15, "left wall"
    s.hold(pg.K_UP); free_every_frame(s, 300)             # the bed is in the way up here
    assert s.pet.y >= 146 - 0.5, "bed blocks the pet (y=%.1f)" % s.pet.y
    s.release(pg.K_LEFT, pg.K_UP)
    s.pet.x, s.pet.y = 200.0, 200.0
    s.hold(pg.K_UP); free_every_frame(s, 300)
    assert s.pet.y >= 106 - 0.5, "back wall"
    s.release(pg.K_UP)
    s.pet.x, s.pet.y = 300.0, 230.0
    s.hold(pg.K_RIGHT, pg.K_DOWN); free_every_frame(s, 600)
    assert s.pet.x <= 464 and s.pet.y <= 238, "right/bottom wall"
    s.release(pg.K_RIGHT, pg.K_DOWN)


def test_feeding():
    s = Sim(); s.start_new()
    s.pet.x, s.pet.y = 150.0, 180.0
    p = s.pet; p.hunger, p.happiness = 40.0, 50.0
    xp0, coins0 = p.xp, p.coins
    seen = set()
    s.key(pg.K_f)
    track_jumps(s, lambda: (seen.add(s.brain.state.name), s.brain.state.name == "IDLE" and "EAT" in seen)[1], 60)
    assert "WALK_TO_OBJECT" in seen and "EAT" in seen
    assert 58 < p.hunger < 62, "hunger +20 (got %.1f)" % p.hunger
    assert p.happiness > 54, "happiness +5 (got %.1f)" % p.happiness
    assert p.xp - xp0 == 5 and p.coins - coins0 == 12  # action + first-meal achievement
    assert abs(p.x - 386) < 6 and abs(p.y - 222) < 6, "ate at the bowl"
    assert os.path.isfile(config.SAVE_PATH)


def test_playing():
    s = Sim(); s.start_new()
    s.pet.x, s.pet.y = 120.0, 180.0
    p = s.pet; p.happiness, p.energy = 50.0, 80.0
    xp0 = p.xp
    seen = set()
    s.key(pg.K_p)
    track_jumps(s, lambda: (seen.add(s.brain.state.name), s.brain.state.name == "IDLE" and "PLAY" in seen)[1], 60)
    assert p.happiness > 66, "happiness +20 (got %.1f)" % p.happiness
    assert 68 < p.energy < 71, "energy -10 (got %.1f)" % p.energy
    assert p.xp - xp0 == 10
    assert math.hypot(s.world.toy[0] - s.world.toy_home[0], s.world.toy[1] - s.world.toy_home[1]) < 2, \
        "ball returns to its home spot"


def test_sleeping():
    s = Sim(); s.start_new()
    p = s.pet; p.energy = 35.0; p.x, p.y = 200.0, 190.0
    xp0 = p.xp
    s.key(pg.K_s)
    trace, phases = [], set()

    def cond():
        if s.brain.state.name == "SLEEP":
            phases.add(s.brain.phase)
            if s.brain.phase == "asleep":
                trace.append(p.energy)
        return "asleep" in phases and s.brain.state.name != "SLEEP"
    track_jumps(s, cond, 120)
    assert {"hop_on", "asleep", "hop_off"} <= phases, phases
    assert trace[0] < 50 and trace[-1] >= 90, "energy climbs 35 -> 90+ (%.0f -> %.0f)" % (trace[0], trace[-1])
    assert all(b >= a for a, b in zip(trace, trace[1:])), "energy monotonic while asleep"
    assert not p.on_bed and p.z == 0
    assert p.xp - xp0 == 5


def test_sleep_particles_and_wake_on_key():
    s = Sim(); s.start_new()
    s.pet.energy = 30.0
    s.key(pg.K_s)
    s.until(lambda: s.brain.state.name == "SLEEP" and s.brain.phase == "asleep", 40)
    s.step(60, 33, False)
    assert any(pt.kind == "z" for pt in s.g.fx.parts), "Z particles while asleep"
    s.step(1, 33); s.shot("sleeping")
    s.hold(pg.K_LEFT); s.step(60, 33, False); s.release(pg.K_LEFT)
    assert s.brain.state.name != "SLEEP", "arrow key wakes the pet"


def test_home_navigation():
    s = Sim(); s.start_new()
    s.pet.x, s.pet.y = 440.0, 150.0
    s.key(pg.K_h)
    track_jumps(s, lambda: s.brain.state.name == "SLEEP", 60, 50)
    s.until(lambda: s.brain.phase == "asleep", 10)
    assert s.pet.on_bed, "Home navigates to the bed and sleeps"


def test_pathfinding_avoids_furniture():
    s = Sim(); s.start_new()
    w = s.world
    for a, b in (((100, 200), (440, 150)), ((60, 160), (343, 120)), ((390, 230), (50, 150)),
                 ((340, 150), (340, 125))):
        path = w.find_path(a, b)
        assert path, (a, b)
        pts = [a] + path
        for i in range(len(pts) - 1):
            assert w.segment_free(pts[i], pts[i + 1]), "path segment crosses furniture"


def test_navigation_never_stalls():
    """Regression: paths grazing furniture corners used to freeze the pet forever."""
    import random
    s = Sim(); s.start_new()
    w, b = s.world, s.brain
    rng = random.Random(5)
    targets = {k: v[0] for k, v in w.landmarks.items()}
    targets.update(food=w.anchors["food"], water=w.anchors["water"], bed=w.anchors["bed_approach"])
    # the exact start/goal pairs that used to freeze
    cases = [((153, 155), targets["plant"]), ((428, 143), targets["clock"]), ((434, 154), targets["shelf"])]
    cases += [(w.random_free_point(rng), targets[rng.choice(list(targets))]) for _ in range(150)]
    for start, goal in cases:
        s.pet.x, s.pet.y = float(start[0]), float(start[1])
        b.pending = None; b._to_idle(1e9); b.dur = 1e9
        b.command("goto", point=goal)
        for _ in range(int(40 / 0.033)):
            s.step(1, 33, False)
            if b.state.name != "WALK_TO_OBJECT":
                break
        assert b.state.name != "WALK_TO_OBJECT", ("stalled", start, goal, s.pet.x, s.pet.y)
        assert math.hypot(s.pet.x - goal[0], s.pet.y - goal[1]) < 8, ("did not arrive", start, goal)


def test_stall_watchdog():
    s = Sim(); s.start_new()
    b = s.brain
    b.path = [(300.0, 190.0)]
    b._enter(type(b.state).WALK_TO_OBJECT)
    b.speed = 0.0                                   # simulate a pet that can never arrive
    b.task = "goto"
    for _ in range(int(50 / 0.1)):
        s.step(1, 100, False)
        if b.state.name != "WALK_TO_OBJECT":
            break
    assert b.state.name != "WALK_TO_OBJECT", "watchdog frees a stuck walker"


def test_pet_interaction():
    s = Sim(); s.start_new()
    p = s.pet; p.happiness = 50.0
    xp0 = p.xp
    s.mouse_to(300, 150)
    s.key(pg.K_e); s.step(3, 16, False)
    assert s.brain.state.name == "HAPPY" and p.happiness >= 53.9
    assert p.xp - xp0 == 3 and p.bubble_text
    assert any(pt.kind == "heart" for pt in s.g.fx.parts)
    assert p.facing == "right", "looks toward the player"
    # clicking the pet works too
    s.step(80, 33, False)
    h0 = p.happiness
    s.click(p.x, p.y - 8); s.step(3, 16, False)
    assert p.happiness > h0


def test_follow_mode():
    s = Sim(); s.start_new()
    s.pet.x, s.pet.y = 60.0, 200.0
    s.key(pg.K_c); s.step(2, 16, False)
    assert s.brain.follow and s.g.ui.button("follow").active
    s.mouse_to(380, 190)
    for _ in range(40):
        s.step(20, 33, False)
        assert s.world.is_free(s.pet.x, s.pet.y)
    d = math.hypot(s.pet.x - 380, s.pet.y - 190)
    assert 12 < d < 40, "keeps a small distance (%.1f)" % d
    s.shot("follow")
    s.key(pg.K_c); s.step(5, 33, False)
    assert not s.brain.follow
    s.mouse_to(100, 200); s.step(60, 33, False)
    assert math.hypot(s.pet.x - 100, s.pet.y - 200) > 100, "stops following when off"


def test_autonomous_behavior_and_stats():
    s = Sim(); s.start_new()
    s.brain.dur = 1.0
    states, start = set(), (s.pet.x, s.pet.y)
    dist, last = 0.0, start
    for _ in range(int(240 / 0.05)):                    # 4 minutes of pet time
        s.step(1, 50, False)
        states.add(s.brain.state.name)
        dist += math.hypot(s.pet.x - last[0], s.pet.y - last[1])
        last = (s.pet.x, s.pet.y)
        assert 0 <= s.pet.hunger <= 100 and 0 <= s.pet.happiness <= 100 and 0 <= s.pet.energy <= 100
        assert s.world.is_free(s.pet.x, s.pet.y) or s.pet.on_bed
    assert dist > 150, "pet wandered on its own (%.0fpx)" % dist
    assert len(states) >= 4, states
    assert {"IDLE", "WANDER"} <= states
    # needs fall slowly (check a quiet pet: no actions)
    s2 = Sim(); s2.start_new()
    h0, a0 = s2.pet.hunger, s2.pet.happiness
    for _ in range(int(600 / 0.05)):
        s2.pet.tick_needs(0.05, "idle", False)
    assert 30 < h0 - s2.pet.hunger < 40, "hunger drop over 10 min = %.1f" % (h0 - s2.pet.hunger)
    assert 10 < a0 - s2.pet.happiness < 25


def test_hungry_pet_begs_and_sleepy_pet_sleeps():
    s = Sim(); s.start_new()
    s.pet.hunger = 20.0
    s.brain.last_beg = -999
    s.brain.dur = 0.1
    seen = []
    s.until(lambda: (seen.append(s.pet.bubble_text), "FEED" in s.pet.bubble_text.upper() or "HUNGRY" in s.pet.bubble_text.upper())[1], 40)
    s2 = Sim(); s2.start_new()
    s2.pet.energy = 10.0
    s2.brain.dur = 0.1
    s2.until(lambda: s2.brain.state.name == "SLEEP", 40)


def test_level_up():
    s = Sim(); s.start_new()
    p = s.pet
    p.xp = p.xp_needed - 2
    c0, lv0 = p.coins, p.level
    s.brain._reward("feed")
    s.step(3, 16, False)
    assert p.level == lv0 + 1 and p.coins - c0 == 2 + 20
    assert s.g.ui.banner and s.g.ui.banner["level"] == lv0 + 1
    assert any(pt.kind in ("px", "spark") for pt in s.g.fx.parts)
    s.step(20, 16)
    s.shot("levelup")
    assert json.load(open(config.SAVE_PATH))["level"] == lv0 + 1, "saved on level-up"


def test_save_and_reload_with_offline_time():
    s = Sim(); s.start_new("Mochi")
    p = s.pet
    p.level, p.xp, p.coins, p.hunger, p.happiness, p.energy = 4, 17, 133, 72.0, 86.0, 91.0
    p.x, p.y = 222.0, 176.0
    p.inventory["treat"] = 2
    s.g.save_now()
    s.g.shutdown() if False else None
    path = config.SAVE_PATH
    data = json.load(open(path))
    data["last_saved_time"] = time.time() - 3600           # closed for an hour
    json.dump(data, open(path, "w"))
    s2 = Sim.__new__(Sim); s2.tmp = s.tmp
    import game
    H.pressed.clear(); H.events.clear()
    s2.g = game.Game()
    q = s2.g.pet
    assert (q.name, q.level, q.xp, q.coins) == ("Mochi", 4, 17, 133)
    assert abs(q.x - 222) < 1 and abs(q.y - 176) < 1
    assert q.inventory["treat"] == 2
    assert 45 < q.hunger < 56, "slow offline hunger loss (%.1f)" % q.hunger
    assert q.energy > 91 and q.happiness < 86
    assert q.bubble_text, "welcome-back bubble"
    # extreme absence is capped and floored
    data["last_saved_time"] = time.time() - 60 * 86400
    json.dump(data, open(path, "w"))
    s3 = Sim.__new__(Sim); s3.tmp = s.tmp
    s3.g = game.Game()
    assert s3.g.pet.hunger >= 15 and s3.g.pet.happiness >= 25


def test_saved_position_inside_furniture_is_fixed():
    import save_system
    d = save_system.default_data("Bed")
    d["position_x"], d["position_y"] = 40.0, 130.0        # inside the bed
    s = Sim(save=d)
    assert s.world.is_free(s.pet.x, s.pet.y)


def test_corrupted_saves():
    for raw in ("{not json", "[1,2,3]", '{"pet_name": 5, "hunger": "abc", "level": -4, "energy": 1e99}', ""):
        s = Sim(raw_save=raw)
        s.step(3)
        if raw.startswith('{"pet_name"'):
            assert s.g.session, "partially valid save is repaired"
            assert 0 <= s.pet.energy <= 100 and s.pet.level >= 1
        else:
            assert not s.g.session and s.g.overlay is not None, "falls back to name screen"
            assert os.path.isfile(config.SAVE_PATH + ".corrupt")


def test_ui_buttons_and_shortcuts():
    s = Sim(); s.start_new()
    btn = {b.key: b for b in s.g.ui.buttons}
    # hover effect
    c = btn["feed"].rect.center
    s.mouse_to(*c); s.step(10, 16)
    assert btn["feed"].hovered
    s.shot("hover_button")
    s.mouse_to(5, 5)
    s.pet.hunger = 50
    s.click(*btn["feed"].rect.center); s.step(3, 16, False)
    assert s.brain.state.name == "WALK_TO_OBJECT" and s.brain.task == "eat"
    s.until(lambda: s.brain.state.name == "IDLE", 40)
    s.brain.dur = 1e9
    for key, expect_task in (("home", "home"), ("sleep", "sleep"), ("play", "play")):
        s.pet.energy = 50
        s.click(*btn[key].rect.center); s.step(3, 16, False)
        assert s.brain.task == expect_task, (key, s.brain.task)
        s.step(3, 16, False)
        s.brain.pending = None
        s.brain._to_idle(1e9); s.brain.dur = 1e9
    s.click(*btn["pet"].rect.center); s.step(3, 16, False)
    assert s.brain.state.name == "HAPPY"
    s.click(*btn["shop"].rect.center); s.step(3, 16, False)
    assert type(s.g.overlay).__name__ == "ShopMenu"
    s.key(pg.K_ESCAPE); s.step(2, 16, False)
    assert s.g.overlay is None
    s.click(*btn["menu"].rect.center); s.step(3, 16, False)
    assert type(s.g.overlay).__name__ == "SettingsMenu"
    s.key(pg.K_ESCAPE); s.step(2, 16, False)
    # keyboard shortcuts
    s.brain.pending = None; s.brain._to_idle(1e9); s.brain.dur = 1e9
    for k, task in ((pg.K_h, "home"), (pg.K_f, "eat"), (pg.K_p, "play"), (pg.K_s, "sleep")):
        s.pet.energy = 50; s.pet.hunger = 50
        s.key(k); s.step(3, 16, False)
        assert s.brain.task == task, (k, s.brain.task)
        s.brain.pending = None; s.brain._to_idle(1e9); s.brain.dur = 1e9


def test_click_to_move_and_objects():
    s = Sim(); s.start_new()
    s.pet.x, s.pet.y = 100.0, 200.0
    s.click(300, 160); s.step(3, 16, False)
    assert s.brain.task == "goto"
    track_jumps(s, lambda: s.brain.state.name == "IDLE", 30, 90)
    assert math.hypot(s.pet.x - 300, s.pet.y - 160) < 6
    s.brain.dur = 1e9
    s.click(407, 218); s.step(3, 16, False)               # food bowl
    assert s.brain.task == "eat"


def test_shop():
    s = Sim(); s.start_new()
    s.pet.coins = 55
    s.key(pg.K_b); s.step(2, 16)
    s.shot("shop")
    s.g._buy("treat"); s.g._buy("squeaky"); s.g._buy("squeaky")
    assert s.pet.coins == 5 and s.pet.inventory == {"treat": 1, "squeaky": 1}
    s.g._buy("treat")
    assert s.pet.coins == 5, "cannot overspend"
    s.key(pg.K_ESCAPE); s.step(2, 16, False)
    s.pet.hunger = 40.0
    s.key(pg.K_f)
    s.until(lambda: s.brain.state.name == "IDLE", 40)
    assert s.pet.hunger > 70, "treat gives bonus (%.1f)" % s.pet.hunger
    assert s.pet.inventory["treat"] == 0


def test_settings_and_reset():
    s = Sim(); s.start_new()
    s.key(pg.K_ESCAPE); s.step(3, 16)
    s.shot("settings")
    m = s.g.overlay
    assert type(m).__name__ == "SettingsMenu"
    s.key(pg.K_RETURN); s.step(1, 16, False)               # SOUND toggle
    assert s.g.settings.sound is False
    s.key(pg.K_DOWN); s.key(pg.K_DOWN); s.key(pg.K_LEFT); s.step(2, 16, False)   # volume -10
    assert s.g.settings.volume == 60
    s.key(pg.K_DOWN); s.key(pg.K_RIGHT); s.step(2, 16, False)                    # fps 60 -> 120
    assert s.g.settings.fps == 120
    s.key(pg.K_DOWN); s.key(pg.K_RETURN); s.step(2, 16, False)                   # fullscreen
    assert s.g.display.fullscreen
    s.key(pg.K_RETURN); s.step(2, 16, False)
    assert not s.g.display.fullscreen
    s.key(pg.K_DOWN); s.key(pg.K_RIGHT); s.step(2, 16, False)                    # time of day
    assert s.g.settings.time_mode == "fast"
    s.key(pg.K_DOWN); s.key(pg.K_RETURN); s.step(3, 16)                          # RESET PET
    assert type(s.g.overlay).__name__ == "ConfirmDialog"
    s.shot("reset_confirm")
    s.key(pg.K_n); s.step(2, 16, False)
    assert type(s.g.overlay).__name__ == "SettingsMenu", "NO returns to settings"
    assert s.g.overlay.sel == 6, "cursor stays on RESET PET"
    s.key(pg.K_RETURN); s.step(2, 16, False)
    assert type(s.g.overlay).__name__ == "ConfirmDialog"
    s.key(pg.K_y); s.step(60, 16)
    assert not s.g.session and type(s.g.overlay).__name__ == "NameScreen"
    assert not os.path.isfile(config.SAVE_PATH), "save deleted"
    assert json.load(open(config.SETTINGS_PATH))["volume"] == 60, "settings persisted"


def test_close_and_reopen_keeps_pet():
    s = Sim(); s.start_new("Kiwi")
    s.pet.coins = 77; s.pet.x, s.pet.y = 260.0, 180.0
    H.events.append(pg.Event(pg.QUIT))
    s.g.handle_events()
    assert not s.g.running
    s.g.save_now()
    import game
    g2 = game.Game()
    assert g2.pet.name == "Kiwi" and g2.pet.coins == 77


def test_missing_assets_fallback():
    import assets
    old = assets.ASSET_DIR
    assets.ASSET_DIR = tempfile.mkdtemp()                   # empty folder
    try:
        s = Sim(); s.start_new()
        assert len(s.g.assets.fallbacks) == len(s.g.assets.specs), "everything procedurally generated"
        s.step(30)
        s.shot("fallback_assets")
    finally:
        assets.ASSET_DIR = old
    # and with corrupt PNGs on disk
    junk = tempfile.mkdtemp(); os.makedirs(os.path.join(junk, "sprites", "pet", "cat"))
    open(os.path.join(junk, "sprites", "pet", "cat", "idle.png"), "wb").write(b"not a png")
    assets.ASSET_DIR = junk
    try:
        a = assets.Assets()
        assert "sprites/pet/cat/idle.png" in a.fallbacks
    finally:
        assets.ASSET_DIR = old


def test_shipped_assets_load_from_disk():
    s = Sim(); s.start_new()
    assert s.g.assets.fallbacks == [], "all shipped PNGs found: %s" % s.g.assets.fallbacks
    import audio
    buf = audio.wav_file("click")
    assert buf.read(4) == b"RIFF"


def test_fuzz_soak_no_crashes():
    """Random keys/clicks for ~4 simulated minutes: nothing may crash or break invariants."""
    import random
    rng = random.Random(1234)
    s = Sim(); s.start_new()
    keys = [pg.K_h, pg.K_f, pg.K_p, pg.K_s, pg.K_e, pg.K_c, pg.K_b, pg.K_ESCAPE, pg.K_n,
            pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT, pg.K_RETURN, pg.K_SPACE, pg.K_y]
    arrows = [pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT]
    for frame in range(5000):
        r = rng.random()
        if r < 0.03:
            k = rng.choice(keys)
            s.hold(k) if k in arrows else s.key(k, "")
            if k in arrows and rng.random() < 0.7:
                pass
        elif r < 0.05:
            s.release(*arrows)
        elif r < 0.07:
            s.click(rng.uniform(0, 480), rng.uniform(0, 270))
        elif r < 0.09:
            s.mouse_to(rng.uniform(0, 480), rng.uniform(0, 270))
        H.mods = 3 if rng.random() < 0.2 else 0
        s.step(1, rng.choice([16, 33, 50]), draw=(frame % 7 == 0))
        if s.g.session:
            p = s.pet
            assert 0 <= p.hunger <= 100 and 0 <= p.happiness <= 100 and 0 <= p.energy <= 100
            assert s.world.is_free(p.x, p.y) or p.on_bed or s.brain.state.name == "SLEEP", \
                (frame, p.x, p.y, s.brain.state)
            assert p.level >= 1 and p.coins >= 0 and p.xp >= 0
            assert s.world.BOUNDS.inflate(4, 4).collidepoint((p.x, p.y)) or p.on_bed
        if s.g.overlay and type(s.g.overlay).__name__ == "NameScreen":
            s.key(pg.K_RETURN, "\r")
    assert s.g.running


def test_day_night_and_screenshots():
    s = Sim(); s.start_new()
    s.pet.x, s.pet.y = 250.0, 195.0
    for mode in ("day", "night"):
        s.g.settings.time_mode = mode
        s.g._settings_changed()
        s.step(150, 16)
        s.shot("mode_" + mode)
    dn = s.g.daynight
    assert dn.darkness > 0.9
    s.g.settings.time_mode = "fast"; s.g._settings_changed()
    dn.hour = 18.4
    s.step(5, 16); s.shot("dusk")
    s.g.settings.time_mode = "day"; s.g._settings_changed()
    s.step(120, 16)
    assert dn.daylight > 0.9
    s.brain.night = True
    # states screenshots
    s.pet.hunger = 40; s.key(pg.K_f)
    s.until(lambda: s.brain.state.name == "EAT", 40); s.step(40, 33); s.shot("eating")
    s.until(lambda: s.brain.state.name == "IDLE", 40); s.brain.dur = 1e9
    s.key(pg.K_p)
    s.until(lambda: s.brain.state.name == "PLAY", 40); s.step(50, 33); s.shot("playing")


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
ORDER = ["test_first_launch_and_save", "test_movement_and_animation", "test_collision_and_bounds"]

if __name__ == "__main__":
    only = sys.argv[1:]
    failed = 0
    for fn in TESTS:
        if only and fn.__name__ not in only:
            continue
        t0 = time.time()
        try:
            fn()
            print("PASS  %-52s %.1fs" % (fn.__name__, time.time() - t0))
        except Exception:
            failed += 1
            print("FAIL  %s" % fn.__name__)
            traceback.print_exc()
    print("\n%d failed" % failed if failed else "\nALL TESTS PASSED")
    sys.exit(1 if failed else 0)
