"""Pet brain: a lightweight state machine with personality-weighted randomness.

States: IDLE, WANDER, WALK_TO_OBJECT, EAT, PLAY, SLEEP, SIT, HAPPY, SAD,
FOLLOW_PLAYER (plus MANUAL for arrow-key control). The Brain owns all
behaviour; the Pet only holds data/animation and the Game only forwards input.
"""
import math
import random
from economy import meal
from playful import ToyMotion
from enum import Enum, auto

from config import (WALK_SPEED, RUN_SPEED, WALK_FPS, RUN_FPS, EXPLORE_DISTANCE, FEED_HUNGER,
                    FEED_HAPPY, PLAY_HAPPY, PLAY_ENERGY, PET_HAPPY, TREAT_BONUS, WAKE_ENERGY,
                    C_HAPPY, C_HUNGER, C_ENERGY, C_XP, GOLD,
                    AI_TIRED_THRESHOLD, AI_HUNGRY_BEG_THRESHOLD, AI_PLAY_ENERGY_MIN,
                    AI_REST_THRESHOLD, AI_NIGHT_SLEEP_THRESHOLD, AI_BORED_THRESHOLD,
                    AI_HUNGRY_CHAT, AI_TIRED_CHAT)
from utils import lerp as _lerp, clamp


class State(Enum):
    IDLE = auto()
    WANDER = auto()
    WALK_TO_OBJECT = auto()
    EAT = auto()
    PLAY = auto()
    SLEEP = auto()
    SIT = auto()
    HAPPY = auto()
    SAD = auto()
    FOLLOW_PLAYER = auto()
    MANUAL = auto()


MSG = {
    "hungry": ["FEED ME!", "I'M HUNGRY...", "PLEASE FEED!", "SO HUNGRY..."],
    "sleepy": ["I'M SLEEPY...", "ZZZ...", "SO TIRED..."],
    "bored": ["PLAY?", "PLAY WITH ME!", "I'M BORED..."],
    "hello": ["HELLO!", "HI HI!", "WHAT'S UP?", "LA LA LA"],
    "lonely": ["WHERE ARE YOU?", "HELLO?", "YOU THERE?"],
    "pet": ["YAY!", "HEHE!", "YOU'RE HERE!", "\u2665", "{name}!"],
    "yum": ["YUM!", "SO TASTY!", "NOM NOM!"],
    "play": ["WHEE!", "AGAIN!", "FUN!"],
    "wake": ["GOOD MORNING!", "*YAWN*", "I FEEL GREAT!"],
    "home": ["HOME SWEET HOME!", "COZY!"],
    "sad": ["I'M SAD...", "SNIFF..."],
    "drink": ["GLUG GLUG!", "REFRESHING!"],
}


class Brain:
    def __init__(self, pet, world, fx, emit, rng=None):
        self.pet, self.world, self.fx, self.emit = pet, world, fx, emit
        self.rng = rng or random.Random()
        self.state = State.IDLE
        self.t, self.dur, self.phase = 0.0, self.rng.uniform(2, 4), None
        self.path, self.goal, self.speed, self.stuck = [], None, WALK_SPEED, 0.0
        self.task, self.pending = None, None
        self.follow = False
        self.night = False
        self.clock = 0.0
        self.bubble_cd = 4.0
        self.last_beg = -999.0
        self.last_pet_reward = -999.0
        self.explore_acc = 0.0
        self.explore_cd = {}
        self.look_queue = []
        self.hop = None
        self.auto = False
        self.visit_name = None
        self.eat_which = "food"
        self.repath_t = 0.0
        self.replans = 0
        self.abandoned = False
        self.mouse = None
        # play state
        self.ball_anim = None
        self.toy_motion = None
        self.ball_cd = 0.0
        self.crumb_cd = 0.0
        self.zcd = 0.0
        self.sleep_t = 0.0

    # ================================================================ helpers
    @property
    def activity(self):
        if self.state == State.SLEEP and self.phase == "asleep":
            return "sleep"
        if self.pet.moving:
            return "run" if self.pet.running else "walk"
        return "idle"

    def _enter(self, state, dur=0.0):
        old = self.state
        if old == State.PLAY and state != State.PLAY:
            self.toy_motion = None
            self._throw_ball(self.world.toy_home)
        self.state, self.t, self.dur, self.phase = state, 0.0, dur, None
        if state == State.HAPPY:
            self.emit("happy")

    def _to_idle(self, wait=None):
        if wait is None:
            wait = self.rng.uniform(2.0, 5.0) * (1.35 - 0.6 * self.pet.personality["curiosity"])
        self.path = []
        self.pet.moving = False
        self.auto = False
        self._enter(State.IDLE, wait)

    def _say(self, key, dur=2.6):
        msg = self.rng.choice(MSG[key]).replace("{name}", self.pet.name.upper())
        self.pet.say(msg, dur)

    def _mood_bubble(self):
        if self.bubble_cd > 0:
            return
        p = self.pet
        if p.hunger < AI_HUNGRY_CHAT:
            key = "hungry"
        elif p.energy < AI_TIRED_CHAT:
            key = "sleepy"
        elif p.happiness < AI_BORED_THRESHOLD:
            key = "bored"
        else:
            key = "hello"
        self._say(key)
        self.bubble_cd = self.rng.uniform(10, 18)

    def _reward(self, kind):
        p = self.pet
        from config import XP_REWARDS
        levels = p.gain(kind)
        self.fx.text(p.x, p.y - 44, "+%d XP" % XP_REWARDS[kind], C_XP)
        self.emit("reward", kind=kind)
        if levels:
            self.emit("levelup", level=p.level)

    def _plan(self, goal, fresh=True):
        path = self.world.find_path((self.pet.x, self.pet.y), goal)
        if not path:
            return False
        self.path, self.goal = path, goal
        if fresh:
            self.stuck, self.replans, self.abandoned = 0.0, 0, False
        return True

    def _walk_to(self, point, task, run=None):
        if not self._plan(point):
            self._to_idle(1.0)
            return False
        if run is None:
            run = math.hypot(point[0] - self.pet.x, point[1] - self.pet.y) > 170
        self.speed = RUN_SPEED if run else WALK_SPEED
        self.task = task
        self._enter(State.WALK_TO_OBJECT)
        return True

    def _follow_path(self, dt):
        """Advance along self.path. Returns True when the path is finished."""
        p = self.pet
        if not self.path:
            return True
        tx, ty = self.path[0]
        dx, dy = tx - p.x, ty - p.y
        dist = math.hypot(dx, dy)
        step = (max(self.speed, RUN_SPEED) if p.zoomies > 0 else self.speed) * dt
        if dist <= step + 0.01:
            p.x, p.y = tx, ty
            self.path.pop(0)
            self._travel(dist)
            return not self.path
        ux, uy = dx / dist, dy / dist
        nx, ny = p.x + ux * step, p.y + uy * step
        if self.world.is_free(nx, ny) or not self.world.is_free(p.x, p.y):
            p.x, p.y = nx, ny
            self.stuck = 0.0
        else:
            sx, sy = self.world.try_move(p.x, p.y, ux * step, uy * step)   # slide along the edge
            if (sx, sy) != (p.x, p.y):
                p.x, p.y = sx, sy
                self.stuck = 0.0
            else:
                self.stuck += dt
                if self.stuck > 0.2 and self.replans < 3 and self.goal:
                    self.replans += 1
                    self._plan(self.goal, fresh=False)
                elif self.stuck > 1.0 or self.replans >= 3:
                    self.path, self.abandoned = [], True       # give up gracefully
                    return True
                return False
        p.moving = True
        p.running = self.speed >= RUN_SPEED - 0.1
        p.face_vector(ux, uy)
        self._travel(step)
        return False

    def _travel(self, d):
        self.explore_acc += d
        self.pet.stats["distance_walked"] += d
        if self.explore_acc >= EXPLORE_DISTANCE:
            self.explore_acc = 0.0
            self._reward("explore")
            self.emit("explore")

    # ================================================================ commands
    def command(self, cmd, **kw):
        """Player commands: feed, play, sleep, home, visit, goto, drink, manual, idle."""
        if cmd == "pet":
            return self._do_pet(kw.get("look_at"))
        s = self.state
        if (cmd == "feed" and s == State.EAT and self.eat_which == "food") or \
           (cmd == "play" and s == State.PLAY) or \
           (cmd == "sleep" and s == State.SLEEP):
            return
        self.pending = (cmd, kw)
        self.look_queue = []
        if s == State.SLEEP:
            if self.phase == "asleep":
                self._begin_hop_off()
            return                                # hop phases hand over when done
        self._start_pending()

    def set_follow(self, on):
        self.follow = on
        if on:
            if self.state == State.SLEEP:
                self.pending = ("idle", {})
                if self.phase == "asleep":
                    self._begin_hop_off()
            elif self.state in (State.IDLE, State.WANDER, State.SIT, State.SAD, State.HAPPY):
                self.path = []
                self._enter(State.FOLLOW_PLAYER)
        elif self.state == State.FOLLOW_PLAYER:
            self._to_idle(1.5)

    def _start_pending(self):
        if not self.pending:
            return
        cmd, kw = self.pending
        self.pending = None
        p, w = self.pet, self.world
        self.path, self.auto = [], False
        # Explicit care takes the necessary item back out of storage.
        item = {'feed': 'food', 'drink': 'water', 'play': 'toy'}.get(cmd)
        if item in getattr(p, 'room_hidden', []):
            p.room_hidden.remove(item)
            from decorating import apply_layout
            apply_layout(w, p)
        if cmd == "feed":
            w.bowl_full, w.bowl_timer = True, 30.0
            self._walk_to(w.anchors["food"], "eat")
        elif cmd == "play":
            stand = w.toy_stand()
            if stand:
                self._walk_to(stand, "play", run=True)
        elif cmd == "sleep":
            self._walk_to(w.anchors["bed_approach"], "sleep", run=False)
        elif cmd == "home":
            self._walk_to(w.anchors["bed_approach"], "home", run=False)
        elif cmd == "drink":
            self._walk_to(w.anchors["water"], "drink")
        elif cmd == "visit":
            self.visit_name = kw.get("name")
            self._walk_to(kw["point"], "visit", run=False)
        elif cmd == "goto":
            self._walk_to(kw["point"], "goto")
        elif cmd == "manual":
            self._enter(State.MANUAL)
        else:
            self._to_idle(1.5)

    def _do_pet(self, look_at):
        p = self.pet
        p.stats["total_pettings"] += 1
        if self.state == State.SLEEP:                # gentle: don't wake the pet
            self.fx.hearts(p.x, p.y - 14, 2)
            p.say("ZZZ... HEHE", 2.0)
            p.happiness = min(100, p.happiness + 2)
            self.emit("petted")
            return
        if look_at:
            p.face_vector(look_at[0] - p.x, look_at[1] - p.y)
        p.happiness = min(100, p.happiness + PET_HAPPY)
        self.fx.hearts(p.x, p.y - 18, 3)
        self._say("pet", 2.0)
        if self.clock - self.last_pet_reward > 1.5:
            self.last_pet_reward = self.clock
            self._reward("pet")
        self.emit("petted")
        if self.state in (State.EAT, State.PLAY):
            return                                   # stay busy, just enjoy the pat
        self.path, self.pending = [], None
        p.moving = False
        self._enter(State.HAPPY, 1.8)

    # ================================================================ main update
    def update(self, dt, inp=(0, 0, False, False), follow_target=None, mouse=None):
        p = self.pet
        self.clock += dt
        self.t += dt
        self.bubble_cd = max(0.0, self.bubble_cd - dt)
        self.mouse = mouse
        p.moving = p.running = False
        dx, dy, run, fresh = inp
        if (dx or dy) and (self.state == State.MANUAL or fresh):
            if self.state == State.SLEEP:
                self.command("manual")
            elif self.state != State.MANUAL:
                self.pending = None
                self.look_queue = []
                self._enter(State.MANUAL)
        self._update_ball(dt)
        if self.state in (State.WANDER, State.WALK_TO_OBJECT) and self.t > 45.0:
            self._to_idle(1.0)                  # watchdog: never get stuck walking

        s = self.state
        if s == State.MANUAL:
            self._u_manual(dt, dx, dy, run)
        elif s == State.IDLE:
            self._u_idle(follow_target)
        elif s == State.WANDER:
            if self._follow_path(dt):
                self._start_sit() if self.rng.random() < 0.35 else self._to_idle()
        elif s == State.WALK_TO_OBJECT:
            if self._follow_path(dt):
                self._arrive()
        elif s == State.EAT:
            self._u_eat(dt)
        elif s == State.PLAY:
            self._u_play(dt)
        elif s == State.SLEEP:
            self._u_sleep(dt)
        elif s in (State.SIT, State.HAPPY, State.SAD):
            if self.t >= self.dur:
                self._to_idle(1.0 if s != State.SIT else None)
        elif s == State.FOLLOW_PLAYER:
            self._u_follow(dt, follow_target)
        self._animate()

    def _animate(self):
        p, s = self.pet, self.state
        if p.moving:
            p.anim.play("walk_" + p.facing, RUN_FPS / WALK_FPS if p.running else 1.0)
        elif s == State.SIT:
            p.anim.play("sit")
        elif s == State.EAT:
            p.anim.play("eat")
        elif s == State.PLAY:
            p.anim.play("play")
        elif s == State.HAPPY:
            p.anim.play("happy")
        elif s == State.SAD:
            p.anim.play("sad")
        elif s == State.SLEEP:
            p.anim.play("sleep" if self.phase == "asleep" else "happy")
        else:
            p.anim.play("idle" if p.facing == "down" else "stand_" + p.facing)

    # ================================================================ state handlers
    def _u_manual(self, dt, dx, dy, run):
        p = self.pet
        if not (dx or dy):
            if self.t > 0.12:
                self._to_idle(self.rng.uniform(4.0, 7.0))
            return
        self.t = 0.0
        n = math.hypot(dx, dy)
        speed = RUN_SPEED if run or p.zoomies > 0 else WALK_SPEED
        vx, vy = dx / n * speed, dy / n * speed
        nx, ny = self.world.try_move(p.x, p.y, vx * dt, vy * dt)
        moved = math.hypot(nx - p.x, ny - p.y)
        p.x, p.y = nx, ny
        if moved > 0.01:
            p.moving, p.running = True, run
            p.face_vector(dx, dy)
            self._travel(moved)
        else:
            p.face_vector(dx, dy)

    def _u_idle(self, follow_target):
        if self.follow and follow_target is not None:
            self._enter(State.FOLLOW_PLAYER)
            return
        if self.t < self.dur:
            return
        if self.look_queue:
            facing, dur = self.look_queue.pop(0)
            self.pet.facing = facing
            self.t, self.dur = 0.0, dur
            return
        self._choose_next()

    def _u_follow(self, dt, target):
        p = self.pet
        if not self.follow or target is None:
            self._to_idle(1.0)
            return
        tx, ty = target
        dist = math.hypot(tx - p.x, ty - p.y)
        keep = 26.0
        if dist > keep + 8 or (self.path and dist > keep):
            self.repath_t -= dt
            if self.repath_t <= 0 or not self.path:
                ux, uy = (p.x - tx) / max(dist, 1), (p.y - ty) / max(dist, 1)
                gx, gy = tx + ux * keep, ty + uy * keep
                if not self.world.is_free(gx, gy):
                    near = self.world.nearest_free(gx, gy)
                    gx, gy = near if near else (p.x, p.y)
                if not self._plan((gx, gy)):
                    self.path = []
                self.repath_t = 0.35
            self.speed = RUN_SPEED if dist > 120 else WALK_SPEED
            self._follow_path(dt)
        else:
            self.path = []
            p.face_vector(tx - p.x, ty - p.y)

    # ---------------------------------------------------------------- arrivals
    def _arrive(self):
        p, w, task = self.pet, self.world, self.task
        self.task = None
        if self.abandoned:                     # couldn't reach it: don't act out the task here
            self.abandoned, self.auto = False, False
            return self._to_idle(1.5)
        if task == "eat":
            self._start_eat("food")
        elif task == "drink":
            self._start_eat("water")
        elif task == "play":
            self._start_play()
        elif task == "sleep":
            self._begin_hop_on()
        elif task == "beg":
            p.facing = "right"
            self._enter(State.SIT, 8.0)
            self._say("hungry", 3.5)
            self.bubble_cd = 10.0
            self.emit("bang", x=p.x, y=p.y - 28)
        elif task == "home":
            self._say("home", 3.0)
            self._begin_hop_on()
        elif task == "visit":
            self._finish_visit()
        else:
            self._to_idle(2.0)

    def _finish_visit(self):
        p, name = self.pet, self.visit_name
        facing = {"plant": "right", "cushion": "down"}.get(name, "up")
        p.facing = facing
        comments = self.world.landmarks.get(name, (None, ["?"]))[1]
        p.say(self.rng.choice(comments), 2.4)
        if self.clock - self.explore_cd.get(name, -999.0) > 40.0 and not self.auto:
            self.explore_cd[name] = self.clock
            self._reward("explore")
            self.emit("explore")
        self.auto = False
        self._enter(State.IDLE, 2.4)

    # ---------------------------------------------------------------- eating
    def _start_eat(self, which):
        p = self.pet
        self.eat_which = which
        p.facing = "right" if which == "food" else "left"
        if which == "food":
            self.world.bowl_full, self.world.bowl_timer = True, 30.0
        self._enter(State.EAT, 3.4)
        self.crumb_cd = 0.4
        self.emit("eat_start")

    def _u_eat(self, dt):
        p = self.pet
        self.crumb_cd -= dt
        if self.crumb_cd <= 0:
            sign = 1 if p.facing == "right" else -1
            if self.eat_which == "food":
                self.fx.crumbs(p.x + 11 * sign, p.y - 7, p.selected_food)
            else:
                self.fx.sparkles(p.x + 11 * sign, p.y - 6, 1, 3)
            self.emit("munch")
            self.crumb_cd = 0.55
        if self.t >= self.dur:
            self._finish_eat()

    def _finish_eat(self):
        p = self.pet
        if self.eat_which == "food":
            p.stats["total_feeds"] += 1
            gain = meal(p)
            self.fx.text(p.x, p.y - 34, "HUNGER +%d" % gain, C_HUNGER)
            self.world.bowl_full = False
            self._say("yum", 2.2)
            self._reward("feed")
            self.emit("fed")
        else:
            p.stats["total_drinks"] += 1
            p.happiness = min(100, p.happiness + 3)
            self.fx.text(p.x, p.y - 34, "HAPPY +3", C_HAPPY)
            self._say("drink", 2.0)
            self.emit("drank")
        self._enter(State.HAPPY, 1.4)

    # ---------------------------------------------------------------- playing
    def _throw_ball(self, target, dur=0.8):
        w = self.world
        self.ball_anim = {"a": (w.toy[0], w.toy[1]), "b": target, "t": 0.0, "d": dur}

    def _update_ball(self, dt):
        b = self.ball_anim
        if not b:
            return
        b["t"] += dt
        f = min(1.0, b["t"] / b["d"])
        w = self.world
        w.toy[0] = _lerp(b["a"][0], b["b"][0], f)
        w.toy[1] = _lerp(b["a"][1], b["b"][1], f)
        w.toy_z = math.sin(f * math.pi) * 14
        if f >= 1.0:
            w.toy_z = 0.0
            self.ball_anim = None
            self.ball_cd = self.rng.uniform(0.35, 0.8)

    def _start_play(self, auto=None):
        if auto is not None:
            self.auto = auto
        self.pet.facing = "right"
        self._enter(State.PLAY, 10.0)
        self.ball_anim = None
        self.toy_motion = ToyMotion(self.pet.selected_toy, (35, 160, 445, 231), self.world.toy, self.rng)
        self.toy_route_cd = 0
        self.path = []
        self.ball_cd = 0.3
        self.emit("play_start")

    def _u_play(self, dt):
        p, w = self.pet, self.world
        self.ball_cd -= dt
        if self.toy_motion:
            m = self.toy_motion
            m.update(dt)
            free = w.nearest_free(m.x, m.y)
            if free: w.toy[:] = free
            w.toy_z = m.z
            if math.hypot(p.x-w.toy[0], p.y-w.toy[1]) < 30 and self.ball_cd <= 0:
                m.bat(); self.ball_cd = 1.2; self.emit('bounce')
        # chase: stay just left or right of the ball and hop along
        side = -18 if p.x <= w.toy[0] else 18
        self.toy_route_cd -= dt
        if self.toy_route_cd <= 0:
            self.toy_route_cd = .6
            goal = w.nearest_free(w.toy[0] + side, w.toy[1] + 4)
            self.path = w.find_path((p.x,p.y),goal) if goal else []
        while self.path and math.dist((p.x,p.y),self.path[0]) < 3:
            self.path.pop(0)
        gx, gy = self.path[0] if self.path else (p.x,p.y)
        dx, dy = gx - p.x, gy - p.y
        d = math.hypot(dx, dy)
        if d > 4:
            step = min(d, RUN_SPEED * dt)
            nx, ny = w.try_move(p.x, p.y, dx / d * step, dy / d * step)
            p.x, p.y = nx, ny
            p.moving = True
            p.running = True
        p.facing = "right" if w.toy[0] >= p.x else "left"
        if self.t >= self.dur:
            self._finish_play()

    def _finish_play(self):
        p = self.pet
        p.stats["total_plays"] += 1
        bonus = 5 if p.inventory.get("squeaky", 0) > 0 else 0
        if self.auto:
            gh, ge = 8, 4
        else:
            gh, ge = PLAY_HAPPY + bonus, PLAY_ENERGY
        p.happiness = min(100, p.happiness + gh)
        p.energy = max(0, p.energy - ge)
        self.fx.text(p.x, p.y - 34, "HAPPY +%d" % gh, C_HAPPY)
        self.fx.text(p.x, p.y - 22, "ENERGY -%d" % ge, C_ENERGY)
        self.fx.sparkles(p.x, p.y - 14, 5)
        self._say("play", 2.0)
        if not self.auto:
            self._reward("play")
        self.emit("played")
        self.auto = False
        self._enter(State.HAPPY, 1.4)

    # ---------------------------------------------------------------- sleeping
    def _begin_hop_on(self):
        p = self.pet
        p.stats["total_sleeps"] += 1
        self._enter(State.SLEEP)
        self.phase = "hop_on"
        self.hop = {"a": (p.x, p.y), "b": self.world.anchors["bed_spot"], "t": 0.0, "d": 0.7, "h": 10}
        p.on_bed = self.world.bed.visible
        p.facing = "down"
        self.emit("hop")

    def _begin_hop_off(self, natural=False):
        p = self.pet
        self.phase = "hop_off"
        self.hop = {"a": (p.x, p.y), "b": self.world.anchors["bed_approach"], "t": 0.0,
                    "d": 0.6, "h": 8}
        self.natural_wake = natural
        self.emit("hop")

    def _u_sleep(self, dt):
        p = self.pet
        if self.phase in ("hop_on", "hop_off"):
            h = self.hop
            h["t"] += dt
            f = min(1.0, h["t"] / h["d"])
            p.x = _lerp(h["a"][0], h["b"][0], f)
            p.y = _lerp(h["a"][1], h["b"][1], f)
            p.z = math.sin(f * math.pi) * h["h"]
            if f < 1.0:
                return
            p.z = 0.0
            if self.phase == "hop_on":
                self.phase, self.sleep_t, self.zcd = "asleep", 0.0, 0.6
                self.emit("sleep_start")
                if self.pending:
                    self._begin_hop_off()
            else:
                p.on_bed = False
                if self.pending:
                    self._start_pending()
                else:
                    self._to_idle(2.0)
            return
        # asleep
        self.sleep_t += dt
        self.zcd -= dt
        if self.zcd <= 0:
            self.fx.zzz(p.x + 5, p.y - 18)
            self.zcd = 1.3
        if p.energy >= WAKE_ENERGY and self.sleep_t >= 5.0:
            if self.sleep_t >= 8.0 or self.auto:
                self._reward("sleep")
            self._say("wake", 3.0)
            self.emit("slept")
            self._begin_hop_off(natural=True)

    # ---------------------------------------------------------------- autonomous choices
    def _choose_next(self):
        p, r = self.pet, self.rng
        pers = p.personality
        if p.energy < AI_TIRED_THRESHOLD and r.random() < 0.8:
            return self._auto_sleep()
        if p.hunger < AI_HUNGRY_BEG_THRESHOLD and self.clock - self.last_beg > 45:
            self.last_beg = self.clock
            return self._auto_walk(self.world.anchors["food"], "beg")
        if p.mood == "sad" and r.random() < 0.35:
            self._enter(State.SAD, 3.5)
            self._say("sad", 3.0)
            return
        opts = [
            ((2.2 + 3.0 * pers["curiosity"]) * (0.6 if self.night else 1.0), self._start_wander),
            (1.3, self._start_sit),
            (1.4, self._start_look),
            ((0.6 + 3.0 * pers["playfulness"]) if p.energy > AI_PLAY_ENERGY_MIN else 0.2, self._auto_play),
            (0.7 + 1.2 * pers["curiosity"], self._auto_explore),
            (0.5 if p.hunger < 70 else 0.15, lambda: self._auto_walk(self.world.anchors["water"], "drink")),
            (0.9 * pers["friendliness"], self._greet),
        ]
        sleep_w = 0.0
        if self.night and p.energy < AI_NIGHT_SLEEP_THRESHOLD:
            sleep_w = 3.0 + 5.0 * pers["sleepiness"]
        elif p.energy < AI_REST_THRESHOLD:
            sleep_w = 1.5 + 3.0 * pers["sleepiness"]
        if sleep_w:
            opts.append((sleep_w, self._auto_sleep))
        total = sum(w for w, _ in opts)
        pick = r.uniform(0, total)
        for w, fn in opts:
            pick -= w
            if pick <= 0:
                fn()
                break
        if r.random() < 0.18:
            self._mood_bubble()

    def _auto_walk(self, point, task):
        self.auto = True
        self._walk_to(point, task, run=False)

    def _auto_sleep(self):
        self._auto_walk(self.world.anchors["bed_approach"], "sleep")

    def _auto_play(self):
        if not self.world.toy_visible:
            self._start_sit()
            return
        stand = self.world.toy_stand()
        if stand:
            self.auto = True
            self._walk_to(stand, "play", run=self.rng.random() < 0.5)
        else:
            self._to_idle()

    def _auto_explore(self):
        names = [name for name in self.world.landmarks if getattr(getattr(self.world, name, None), 'visible', True)]
        if not names: return self._start_wander()
        name = self.rng.choice(names)
        self.visit_name = name
        self._auto_walk(self.world.landmarks[name][0], "visit")

    def _start_wander(self):
        p, r = self.pet, self.rng
        near = (p.x, p.y) if r.random() < 0.5 else None
        goal = self.world.random_free_point(r, near=near, radius=110)
        if goal and self._plan(goal):
            self.speed = RUN_SPEED if r.random() < 0.2 * p.personality["playfulness"] else WALK_SPEED
            self._enter(State.WANDER)
        else:
            self._to_idle()

    def _start_sit(self):
        self.pet.facing = "down"
        self._enter(State.SIT, self.rng.uniform(3.0, 7.0))

    def _start_look(self):
        r = self.rng
        seq = [r.choice(["left", "right", "up", "down"]) for _ in range(r.randint(2, 3))]
        seq.append("down")
        self.pet.facing = seq[0]
        self.look_queue = [(f, r.uniform(0.7, 1.2)) for f in seq[1:]]
        self._enter(State.IDLE, r.uniform(0.7, 1.2))

    def _greet(self):
        p = self.pet
        if self.mouse:
            p.face_vector(self.mouse[0] - p.x, self.mouse[1] - p.y)
        if self.bubble_cd <= 0:
            self._say("hello" if p.mood != "sad" else "lonely", 2.2)
            self.bubble_cd = self.rng.uniform(8, 14)
        self._enter(State.IDLE, 2.5)
