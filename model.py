"""Deterministic game simulation, independent of the display and sound system."""

from dataclasses import dataclass
import math
import random


FANS = ((290, 512), (409, 455), (787, 455), (923, 514), (831, 600), (364, 601))
TARGET = (600, 501)
ITEMS = ("Бумажный мяч", "Стаканчик", "Губка")
@dataclass(frozen=True)
class Club:
    name: str
    badge: str
    primary: tuple[int, int, int]
    secondary: tuple[int, int, int]


CLUBS = (
    Club("Барселона", "FCB", (54, 90, 153), (167, 52, 83)),
    Club("Реал Мадрид", "RM", (250, 250, 244), (168, 151, 205)),
    Club("Атлетико Мадрид", "ATM", (225, 58, 65), (250, 250, 244)),
    Club("Севилья", "SEV", (250, 250, 244), (206, 45, 58)),
    Club("Реал Бетис", "BET", (36, 151, 91), (250, 250, 244)),
    Club("Валенсия", "VAL", (250, 250, 244), (235, 130, 47)),
    Club("Вильярреал", "VIL", (246, 216, 62), (62, 92, 158)),
    Club("Атлетик Бильбао", "ATH", (212, 52, 59), (250, 250, 244)),
    Club("Реал Сосьедад", "RSO", (54, 111, 186), (250, 250, 244)),
    Club("Жирона", "GIR", (218, 53, 65), (250, 250, 244)),
)
TAUNTS = (
    "Эй, лови стакан!",
    "{target}, где твоя защита?",
    "Эй, растяпа, лови!",
    "{throwers} передаёт привет!",
    "Шарф крутой. Счёт — не очень!",
    "До встречи на поле!",
)
REPLIES = ("Наши ещё покажут!", "Судья! Это фол!", "Я вообще-то на матч!", "Ещё увидимся на поле!")


@dataclass
class Projectile:
    start: tuple[float, float]
    end: tuple[float, float]
    kind: int
    duration: float = 0.8
    age: float = 0.0

    @property
    def progress(self):
        return min(1.0, max(0.0, self.age / self.duration))

    @property
    def position(self):
        t = self.progress
        return (
            self.start[0] + (self.end[0] - self.start[0]) * t,
            self.start[1] + (self.end[1] - self.start[1]) * t - 145 * 4 * t * (1 - t),
        )


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]


class GameState:
    cooldown_seconds = 0.25

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.throwers = 0
        self.target = 1
        self.reset()

    def reset(self):
        self.time = 0.0
        self.selected = 0
        self.throws = 0
        self.hits = 0
        self.cooldown = 0.0
        self.reaction = 0.0
        self.projectiles = []
        self.particles = []
        self.poses = [0.0] * len(FANS)
        self.speaker = 0
        self.bubble = ""
        self.bubble_time = 0.0
        self.reply = ""
        self.reply_time = 0.0
        self.last_kind = 0

    def choose_club(self, role, index):
        """Change a side, swapping opponents if necessary, and start a fresh round."""
        if role not in ("throwers", "target") or index not in range(len(CLUBS)):
            return False
        if getattr(self, role) == index:
            return False
        other = "target" if role == "throwers" else "throwers"
        if getattr(self, other) == index:
            setattr(self, other, getattr(self, role))
        setattr(self, role, index)
        self.reset()
        return True

    def select(self, kind):
        if kind in range(len(ITEMS)):
            self.selected = kind

    def throw(self):
        """Return whether a new throw was accepted (rapid presses have a cooldown)."""
        if self.cooldown > 1e-9:
            return False
        self.speaker = self.throws % len(FANS)
        x, y = FANS[self.speaker]
        direction = 1 if x < TARGET[0] else -1
        self.projectiles.append(Projectile(
            (x + direction * 29, y - 88),
            (TARGET[0] + self.rng.uniform(-15, 15), TARGET[1] + self.rng.uniform(-10, 10)),
            self.selected,
        ))
        self.poses[self.speaker] = 0.5
        self.bubble = TAUNTS[0] if self.selected == 1 else self.rng.choice(TAUNTS[1:])
        self.bubble = self.bubble.format(target=CLUBS[self.target].name, throwers=CLUBS[self.throwers].name)
        self.bubble_time = 2.4
        self.throws += 1
        self.cooldown = self.cooldown_seconds
        return True

    def update(self, dt):
        """Advance elapsed seconds and return the number of new impacts."""
        if not math.isfinite(dt) or dt < 0:
            raise ValueError("dt must be a finite, nonnegative number")
        self.time += dt
        for name in ("cooldown", "reaction", "bubble_time", "reply_time"):
            setattr(self, name, max(0.0, getattr(self, name) - dt))
        self.poses = [max(0.0, pose - dt) for pose in self.poses]
        for particle in self.particles:
            particle.life -= dt
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += 460 * dt
        self.particles = [p for p in self.particles if p.life > 0]
        impacts = 0
        pending = []
        for projectile in self.projectiles:
            projectile.age += dt
            if projectile.progress < 1:
                pending.append(projectile)
                continue
            impacts += 1
            self.hits += 1
            self.reaction = 0.65
            self.last_kind = projectile.kind
            self.reply = self.rng.choice(REPLIES)
            self.reply_time = 1.8
            palette = (
                ((248, 245, 223), (211, 218, 227)),
                ((92, 184, 229), (164, 220, 243)),
                ((246, 196, 81), (131, 202, 183)),
            )[projectile.kind]
            for _ in range(15):
                angle = self.rng.uniform(-math.pi, 0)
                speed = self.rng.uniform(65, 240)
                self.particles.append(Particle(
                    *projectile.end, math.cos(angle) * speed, math.sin(angle) * speed,
                    self.rng.uniform(0.3, 0.7), self.rng.choice(palette),
                ))
        self.projectiles = pending
        return impacts
