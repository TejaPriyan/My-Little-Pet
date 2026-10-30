"""Up to four named friends sharing one wallet and household progression."""
import math
import random
from pet import Pet
from save_system import default_data
from life import bond, bond_key, record_adventure

FIELDS = ("name", "species", "coat", "hunger", "happiness", "energy", "pet_id", "temperament", "personality")
REACTIONS = ("YOU'RE MY PERSON!", "TINY PAWS, BIG LOVE!", "ONE MORE CUDDLE?", "HI {owner}!", "HAPPY LITTLE WIGGLE!", "BEST FRIEND ALERT!")


def react(pet):
    lines = {"shy": ("A LITTLE HELLO...", "SAFE HERE WITH YOU."), "sleepy": ("FIVE MORE MINUTES?", "DREAMING OF SNACKS..."),
             "curious": ("WHAT'S OVER THERE?", "LET'S EXPLORE, {owner}!")}.get(pet.temperament, REACTIONS)
    pet.say(random.choice(lines).format(owner=pet.owner_name.upper()), 3)


def snapshot(pet):
    return {"pet_name": pet.name, "species": pet.species, "coat": pet.coat,
            "pet_id": pet.pet_id, "temperament": pet.temperament,
            "hunger": pet.hunger, "happiness": pet.happiness, "energy": pet.energy, "head": pet.accessory}


class Household:
    def __init__(self, game):
        self.game = game
        self.friends = []
        self.targets = {}
        self.activities = {}
        self.next_action = {}
        self.timer = 15.0
        self.social_left = 0
        self.reconcile = None
        self.last_greeting = {}
        for i, record in enumerate(game.pet.companions):
            data = default_data(record["pet_name"], game.pet.owner_name)
            data.update(record)
            data["equipped"] = {"head": record.get("head")}
            friend = Pet(game.assets, data)
            friend.x, friend.y = game.world.nearest_free(190 + i * 40, 190) or (240, 190)
            self.friends.append(friend)

    def save(self):
        self.game.pet.companions = [snapshot(p) for p in self.friends]

    def select(self, index):
        if not 0 <= index < len(self.friends): return False
        p, other = self.game.pet, self.friends[index]
        for key in FIELDS:
            value = getattr(p, key)
            setattr(p, key, getattr(other, key))
            setattr(other, key, value)
        p.equipped, other.equipped = other.equipped, p.equipped
        # Keep each identity at its visible location when changing the cared-for pet.
        p.x, other.x = other.x, p.x
        p.y, other.y = other.y, p.y
        p.set_look(p.species, p.coat)
        other.set_look(other.species, other.coat)
        for member in (p, other):
            member.hidden = member.on_bed = member.carried = False
            member.z = 0
            member.anim.play("idle")
        self.targets.clear()
        self.activities.clear()
        self.save()
        return True

    def interact(self, index):
        """A tap greets the existing friend; only Family changes selection."""
        if not 0 <= index < len(self.friends): return
        friend = self.friends[index]
        now = self.game.t
        if now - self.last_greeting.get(friend.pet_id, -10) < 2: return
        self.last_greeting[friend.pet_id] = now
        record_adventure(self.game.pet, "cuddle")
        self.activities[index] = {"kind": "wave", "left": 3, "path": []}
        self.targets.pop(index, None)
        friend.happiness = min(100, friend.happiness + 3)
        friend.anim.play("wave")
        react(friend)
        self.game.voice(friend.voice)

    def start_activity(self, index, kind, desktop=None):
        friend, world = self.friends[index], self.game.world
        target = None
        if kind in ("eat", "sleep", "play"):
            if desktop and not desktop.hidden:
                prop = {"eat": desktop.food, "sleep": desktop.home, "play": desktop.ball}[kind]
                target = desktop.clamp((prop.centerx + (index + 1) * 18, prop.bottom))
            elif not desktop:
                target = {"eat": world.anchors["food"], "sleep": world.anchors["bed_approach"], "play": world.toy_home}[kind]
                target = world.nearest_free(target[0] + index * 12, target[1])
        path = ([target] if desktop else world.find_path((friend.x, friend.y), target)) if target else []
        self.activities[index] = {"kind": kind, "left": 20 if kind == "sleep" else 4, "path": list(path or [])}
        self.targets.pop(index, None)
        friend.say({"eat": "SNACK BREAK!", "sleep": "COZY NAP...", "play": "MY TURN WITH THE BALL!", "dance": "TINY HAPPY DANCE!", "wave": "HI " + self.game.pet.owner_name.upper() + "!"}[kind])

    def add(self, species):
        p = self.game.pet
        if len(self.friends) + 1 >= p.pet_slots or species not in p.owned_species: return False
        from config import SPECIES
        data = default_data(SPECIES[species]["name"].title(), p.owner_name)
        data["species"] = species
        friend = Pet(self.game.assets, data)
        friend.x, friend.y = self.game.world.nearest_free(p.x + 30, p.y) or (p.x, p.y)
        self.friends.append(friend)
        p.solo = False
        self.save()
        return True

    def socialize(self, kind=None):
        p = self.game.pet
        if p.solo or not self.friends or p.hidden: return
        if self.social_left > 0 or self.game.settings.quiet: return
        candidates = [p] + [f for f in self.friends if not f.carried]
        if len(candidates) < 2: return
        p, friend = random.sample(candidates, 2)
        points = self.game.pet.bonds.get(bond_key(p, friend), {}).get("points", 0)
        kind = kind or random.choice(("chat", "dance", "wrestle", "snuggle") if points >= 25 else ("chat", "dance", "wrestle"))
        phrases = {"chat": ("SNACK BUDDIES?", "ALWAYS, BESTIE!"),
                   "dance": ("ONE, TWO, WIGGLE!", "OUR LITTLE DUET!"),
                   "snuggle": ("SAVE ME A COZY SPOT?", "ALWAYS ROOM FOR YOU!"),
                   "wrestle": ("PILLOW DUEL!", "YOU WIN! HUGS?")}
        a, b = phrases[kind]
        p.say(a, 4); friend.say(b, 4)
        pose = "dance" if kind == "dance" else "play" if kind == "wrestle" else "sleep" if kind == "snuggle" else "wave"
        for member in (p, friend):
            member.anim.play(pose)
            if member in self.friends:
                i = self.friends.index(member)
                self.activities[i] = {"kind": pose, "left": 5, "path": []}
        if kind == "snuggle":
            desk = self.game.desktop
            near = desk.clamp((p.x + 24, p.y)) if desk else self.game.world.nearest_free(p.x + 24, p.y)
            if friend in self.friends and near:
                self.activities[self.friends.index(friend)]["path"] = [near] if desk else (self.game.world.find_path((friend.x, friend.y), near) or [])
        bond(self.game.pet, p, friend)
        if kind == "wrestle": self.reconcile = (p, friend)
        self.social_left = 5
        self.timer = random.uniform(20, 40)

    def update(self, dt, desktop=None):
        p, g = self.game.pet, self.game
        if p.solo: return
        self.timer -= dt
        self.social_left = max(0, self.social_left - dt)
        if self.reconcile and not self.social_left:
            a, b = self.reconcile
            a.say("STILL BEST FRIENDS?"); b.say("ALWAYS. BIG HUG!")
            self.reconcile = None
        if self.timer <= 0:
            self.socialize()
        for i, friend in enumerate(self.friends):
            friend.owner_name = p.owner_name
            friend.update(dt)
            activity = self.activities.get(i)
            friend.tick_needs(dt, "sleep" if g.settings.quiet or (activity and activity["kind"] == "sleep" and not activity["path"]) else "idle", False)
            if desktop:
                friend.x, friend.y = desktop.clamp((friend.x, friend.y))
            if friend.carried: continue
            if g.settings.quiet:
                self.activities.pop(i, None)
                if desktop and not desktop.hidden:
                    target = desktop.clamp((desktop.home.right + 25 + i * 28, desktop.home.bottom))
                    dx, dy = target[0] - friend.x, target[1] - friend.y
                    distance = math.hypot(dx, dy)
                    if distance > 3:
                        step = min(distance, dt * 20)
                        friend.x += dx / distance * step; friend.y += dy / distance * step
                        friend.face_vector(dx, dy); friend.anim.play("walk_" + friend.facing)
                        continue
                friend.anim.play("sleep" if friend.energy < 60 else "sit")
                continue
            if activity:
                path = activity["path"]
                if path:
                    dx, dy = path[0][0] - friend.x, path[0][1] - friend.y
                    distance = math.hypot(dx, dy)
                    if distance < 3: path.pop(0)
                    else:
                        step = min(distance, dt * (18 if friend.temperament in ("shy", "sleepy") else 28))
                        nx, ny = friend.x + dx / distance * step, friend.y + dy / distance * step
                        if desktop or g.world.is_free(nx, ny): friend.x, friend.y = nx, ny
                        else: path.clear()
                        friend.face_vector(dx, dy); friend.anim.play("walk_" + friend.facing)
                else:
                    friend.anim.play(activity["kind"])
                    activity["left"] -= dt
                    if activity["left"] <= 0:
                        if activity["kind"] == "eat": friend.hunger = min(100, friend.hunger + 20)
                        if activity["kind"] in ("play", "dance"): friend.happiness = min(100, friend.happiness + 8)
                        self.activities.pop(i, None)
                        self.next_action[i] = random.uniform(8, 16)
                continue
            if self.social_left or friend.carried: continue
            self.next_action[i] = self.next_action.get(i, 5 + i * 3) - dt
            if self.next_action[i] <= 0 and not (desktop and desktop.follow):
                choices = {"playful": ("play", "play", "dance"), "shy": ("wave", "wave", "sleep"), "sleepy": ("sleep", "sleep", "wave"), "curious": ("play", "wave", "dance")}[friend.temperament]
                kind = "sleep" if friend.energy < 35 else "eat" if friend.hunger < 55 else random.choice(choices)
                self.start_activity(i, kind, desktop)
                if kind == "wave" and len(self.friends) > 1:
                    other = self.friends[(i + 1) % len(self.friends)]
                    friend.say("HI " + other.name.upper() + "!")
                    other.say("LET'S PLAY, " + friend.name.upper() + "!")
                continue
            target = self.targets.get(i)
            if desktop:
                if desktop.follow:
                    target = desktop.clamp((p.x - 25 * (i + 1), p.y + 8))
                elif not target or math.dist((friend.x, friend.y), target) < 3:
                    target = desktop.clamp((friend.x + random.uniform(-50, 50), friend.y + random.uniform(-25, 25)))
                friend.x, friend.y = desktop.clamp((friend.x, friend.y))
            elif not target or math.dist((friend.x, friend.y), target) < 3 or not g.world.is_free(*target):
                target = g.world.nearest_free(random.uniform(110, 400), random.uniform(135, 225)) or (p.x, p.y)
            self.targets[i] = target
            dx, dy = target[0] - friend.x, target[1] - friend.y
            distance = math.hypot(dx, dy)
            if distance > 3:
                step = min(distance, dt * (15 if friend.temperament in ("shy", "sleepy") else 24))
                nx, ny = friend.x + dx / distance * step, friend.y + dy / distance * step
                if desktop or g.world.is_free(nx, ny):
                    friend.x, friend.y = nx, ny
                else:
                    self.targets.pop(i, None)
                friend.face_vector(dx, dy)
                friend.anim.play("walk_" + friend.facing)
            else: friend.anim.play("idle")

    @property
    def visible(self):
        return [] if self.game.pet.solo else self.friends
