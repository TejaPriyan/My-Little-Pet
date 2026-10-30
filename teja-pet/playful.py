"""Bounded toy physics and gentle desktop surprises. No coins for autoplay."""
import math
import random


class ToyMotion:
    def __init__(self, kind, bounds, origin, rng=None):
        self.kind, self.bounds = kind, tuple(bounds)
        self.rng = rng or random.Random()
        self.x, self.y = origin
        self.vx = self.rng.choice((-1, 1)) * (100 if kind == 'ball' else 65)
        self.vy = self.rng.uniform(-45, 45)
        self.age, self.turn, self.z = 0., 0., 0.
        self.impulse_age = 0.
        self.bound()

    def bound(self):
        left, top, right, bottom = self.bounds
        if self.x < left or self.x > right:
            self.x = max(left, min(right, self.x)); self.vx *= -1
        if self.y < top or self.y > bottom:
            self.y = max(top, min(bottom, self.y)); self.vy *= -1

    def update(self, dt):
        dt = max(0., min(.1, dt)); self.age += dt; self.turn -= dt
        self.impulse_age += dt
        if self.turn <= 0:
            self.turn = self.rng.uniform(.3, .8) if self.kind == 'butterfly' else self.rng.uniform(.7, 1.5)
            if self.kind in ('mouse', 'butterfly', 'feather'):
                angle = self.rng.uniform(0, math.tau)
                speed = 110 if self.kind == 'butterfly' else 90 if self.kind == 'mouse' else 52
                self.vx, self.vy = math.cos(angle)*speed, math.sin(angle)*speed
        if self.kind == 'yarn':
            self.vx *= math.exp(-.8*dt); self.vy *= math.exp(-.8*dt)
            self.z = 0
        elif self.kind == 'ball':
            self.vx *= math.exp(-.85*dt); self.vy *= math.exp(-.85*dt)
            self.z = abs(math.sin(self.impulse_age*5)) * 16 * math.exp(-1.1*self.impulse_age)
            if self.impulse_age > 4:
                self.vx = self.vy = self.z = 0.
        elif self.kind == 'spring':
            self.z = abs(math.sin(self.age*7))*27
        elif self.kind == 'mouse':
            self.z = abs(math.sin(self.age*14))*1.5
        elif self.kind == 'butterfly':
            self.z = 18 + math.sin(self.age*9)*12
        else:
            self.z = 10 + math.sin(self.age*5)*7
            self.vy += math.sin(self.age*7)*dt*20
        self.x += self.vx*dt; self.y += self.vy*dt; self.bound()

    def bat(self):
        self.impulse_age = 0.
        angle = self.rng.uniform(0, math.tau)
        speed = 120 if self.kind == 'ball' else 75
        self.vx, self.vy = math.cos(angle)*speed, math.sin(angle)*speed


class DesktopFun:
    def __init__(self, desktop, rng=None):
        self.d = desktop
        self.rng = rng or random.Random()
        self.mode = None; self.motion = None; self.elapsed = 0.; self.catch_cd = 0.
        self.next_surprise = self.rng.uniform(12, 22)
        self.next_chat = self.rng.uniform(45, 80)
        self.home = None; self.catch_count = 0; self.goal = None
        self.automatic = False; self.engaged = False; self.arrived = 0.; self.play_hold = 0.

    def stop(self):
        if self.home is not None:
            self.d.ball.topleft = self.home
        self.mode = self.motion = self.home = None
        self.d.pet.z = 0
        self.d.pet.x, self.d.pet.y = self.d.clamp((self.d.pet.x, self.d.pet.y))

    def start(self, mode, automatic=False):
        d, p = self.d, self.d.pet
        self.stop()
        if d.pets_hidden or d.game.settings.quiet or p.energy < 12:
            p.say('A LITTLE REST FIRST.'); return False
        if mode in ('toy', 'mouse') and d.items_hidden:
            self.next_surprise = self.rng.uniform(60, 100)
            p.say('SHOW ITEMS TO PLAY!'); return False
        self.mode, self.elapsed, self.catch_cd, self.catch_count = mode, 0., 1., 0
        self.automatic = automatic; self.engaged = False; self.arrived = 0.; self.play_hold = 0.
        d.follow = False; d.target = None; d.wake()
        self.next_surprise = self.rng.uniform(22, 40)
        if mode in ('toy', 'mouse'):
            self.home = d.ball.topleft
            kind = 'mouse' if mode == 'mouse' else p.selected_toy
            origin = (d.w-22, self.rng.uniform(48, d.h-25)) if mode == 'mouse' else d.ball.center
            self.motion = ToyMotion(kind, (18, 40, d.w-18, d.h-18), origin, self.rng)
            if mode == 'toy': d.put_away.discard('ball')
            p.say('A TINY VISITOR! TAG, YOU ARE IT!' if mode == 'mouse' else 'LET THE TOY ADVENTURE BEGIN!')
        elif mode in ('peek', 'perch'):
            edge = 1 if mode == 'peek' else 22
            self.goal = self.rng.choice(((edge, 48), (d.w-edge, 48), (edge, d.h-16), (d.w-edge, d.h-16)))
            p.say('I KNOW A LITTLE HIDING SPOT!' if mode == 'peek' else 'MY LITTLE COZY CORNER.')
        else:
            self.goal = (d.w/2, d.h/2)
            p.say('CATCH ME WITH YOUR CURSOR!')
        return True

    def found(self):
        found = self.mode in ('peek', 'chase')
        if found:
            self.stop(); self.d.pet.say('OOPS! YOU FOUND ME! HEHE!', 4)
        return found

    def approach(self, target, dt, speed=86):
        p, d = self.d.pet, self.d
        dx, dy = target[0]-p.x, target[1]-p.y
        dist = math.hypot(dx, dy)
        if dist > 2:
            step = min(dist, speed*dt)
            point = (p.x + dx/dist*step, p.y + dy/dist*step)
            p.x, p.y = point if self.mode == 'peek' else d.clamp(point)
            if abs(dx) > 4 or abs(dy) > 4: p.face_vector(dx, dy)
            p.anim.play('walk_'+p.facing)
        else: p.anim.play('sit')
        return dist

    def update(self, dt):
        d, p, g = self.d, self.d.pet, self.d.game
        if g.settings.quiet or d.pets_hidden or (d.items_hidden and self.mode in ('toy', 'mouse')):
            self.stop(); return False
        if d.drag_start or d.menu: return False
        if not self.mode:
            if not getattr(g.settings, 'surprises', True): return False
            if d.follow or d.state not in ('idle', 'walk', 'sit') or d.after: return False
            self.next_surprise -= dt; self.next_chat -= dt
            if self.next_chat <= 0:
                self.next_chat = self.rng.uniform(65, 110)
                p.say(self.rng.choice(('WHAT ARE YOU UP TO?', 'DID YOU MISS ME?', 'YOUR TINY BREAK BUDDY!', 'ONE STRETCH. ONE BIG SMILE!', 'I SAVED YOU A COZY SPOT!')), 4)
            if self.next_surprise <= 0 and p.energy > 28:
                choices = ['peek', 'perch', 'perch', 'chase']
                if not d.items_hidden: choices += ['mouse', 'toy', 'toy']
                self.start(self.rng.choice(choices), automatic=True)
            return False
        self.elapsed += dt; self.catch_cd -= dt
        if self.play_hold > 0:
            self.play_hold -= dt; p.anim.play('play'); return True
        if self.mode in ('toy', 'mouse'):
            m = self.motion
            if self.mode == 'mouse' or self.engaged: m.update(dt)
            if self.mode == 'toy': d.ball.center = (m.x, m.y-m.z)
            distance = self.approach((m.x, m.y), dt)
            if distance < 18 and self.catch_cd <= 0:
                self.engaged = True; self.play_hold = .65
                self.catch_count += 1; self.catch_cd = 2.2; m.bat()
                p.anim.play('play'); p.say('BOOP! YOUR TURN!' if self.mode == 'mouse' else 'GOT IT! AGAIN!')
                if self.mode == 'mouse' and self.catch_count >= 2:
                    self.stop(); p.say('TAG! LITTLE MOUSE, SEE YOU SOON!', 4); return True
        elif self.mode in ('peek', 'perch'):
            if self.approach(self.goal, dt) < 3:
                p.anim.play('sit')
                if self.arrived == 0 and self.mode == 'peek': p.say('DID YOU FIND ME? TAP ME!', 4)
                self.arrived += dt
        elif self.mode == 'chase':
            cursor = d.window.mouse()
            dx, dy = p.x-cursor[0], p.y-cursor[1]
            distance = math.hypot(dx, dy)
            if distance < 90:
                if distance < 1: dx, dy, distance = 1, 1, math.sqrt(2)
                self.goal = d.clamp((p.x+dx/distance*85, p.y+dy/distance*85))
                if math.dist(self.goal, (p.x, p.y)) < 10:
                    self.goal = (d.w-p.x, d.h-p.y)
            self.approach(self.goal, dt, 65)
        if self.elapsed >= (24 if self.mode in ('toy', 'mouse') else 38):
            was_toy = self.mode == 'toy'
            self.stop(); d.wake()
            if was_toy and not self.automatic:
                p.happiness = min(100, p.happiness+12); p.energy = max(0, p.energy-4)
                p.stats['total_plays'] += 1; g.daily_event('play'); d.reward('play')
            p.say('THAT WAS A LITTLE ADVENTURE!')
        return True

    def draw(self, canvas):
        if self.mode == 'mouse' and self.motion and not self.d.items_hidden and not self.d.pets_hidden:
            m = self.motion
            canvas.blit(self.d.game.assets.toys['mouse'], (int(m.x)-8, int(m.y-m.z)-8))
