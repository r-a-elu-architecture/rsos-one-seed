"""MAP1 stage 2: the 15 layer-1 hosts, one per node, from the blue rows of map/MAP_VAKOG_V1.md, each a standard
textbook form of that process. Written after mechanisms.py was sealed (e68eec0) and before any run. Same interface
for every host: h = H(rng); y = h.observe(); harm = h.step(u). Objective per episode: mean(harm) + 0.2 * mean(u).
All constants fixed here; none tuned on any mechanism.
"""
import math
import random

T = 200
LAMBDA = 0.2


class H:
    def __init__(self, rng):
        self.r, self.t = rng, 0
        self.init()


class Genome(H):  # N1: mutation accumulation with exposure bursts; repair removes damage (DNA repair)
    def init(self):
        self.d = 0.02

    def observe(self):
        return self.d / 0.5

    def step(self, u):
        mu = 0.15 if self.r.random() < 0.05 else 0.02
        self.d = min(1.0, self.d + mu * (1 - self.d) - 0.3 * u * self.d)
        return self.d


class Reservoir(H):  # N2: a hard physical bound (dam level); spill above the bound is the violation
    def init(self):
        self.l = 0.5

    def observe(self):
        return self.l

    def step(self, u):
        inflow = 0.25 if self.r.random() < 0.08 else 0.03 * self.r.random()
        self.l = max(0.0, self.l + inflow - 0.15 * u - 0.02)
        spill = max(0.0, self.l - 1.0)
        self.l = min(self.l, 1.0)
        return spill * 5 + (1.0 if self.l >= 1.0 else 0.0)


class Membrane(H):  # N14: diffusion across a membrane; closing it lowers permeability; keep the inside in range
    def init(self):
        self.c, self.out = 0.5, 0.5

    def observe(self):
        return abs(self.c - 0.5) / 0.2

    def step(self, u):
        if self.r.random() < 0.05:
            self.out = self.r.choice([0.0, 1.0])
        else:
            self.out += 0.1 * (0.5 - self.out)
        self.c += 0.3 * (1 - 0.8 * u) * (self.out - self.c) + 0.01 * (0.5 - self.c)
        return max(0.0, abs(self.c - 0.5) - 0.2) * 5


class Sensor(H):  # N3: estimating a drifting signal from a sensor with occasional spikes (robust estimation)
    def init(self):
        self.s, self.est, self.x = 0.0, 0.0, 0.0

    def observe(self):
        self.x = self.s + self.r.gauss(0, 0.1) + (self.r.choice([-3, 3]) if self.r.random() < 0.06 else 0.0)
        return abs(self.x - self.est) / 0.5

    def step(self, u):
        self.est += 0.3 * (1 - u) * (self.x - self.est)
        self.s += self.r.gauss(0, 0.05)
        return abs(self.est - self.s)


class Epidemic(H):  # N4: SIR epidemic with importations; intervention lowers transmission
    def init(self):
        self.s, self.i = 0.99, 0.01

    def observe(self):
        return self.i * 10

    def step(self, u):
        beta = 0.3 * (1 - 0.7 * u)
        new = beta * self.s * self.i
        self.s, self.i = self.s - new, self.i + new - 0.1 * self.i
        if self.r.random() < 0.03:
            self.i += 0.01
            self.s = max(0.0, self.s - 0.01)
        self.s = min(1.0, self.s + 0.002)  # waning immunity
        return self.i * 10


class Thermo(H):  # N8: thermoregulation (Newton cooling toward a fluctuating environment; heating effort)
    def init(self):
        self.temp, self.env = 37.0, 30.0

    def observe(self):
        return max(0.0, 37.0 - self.temp) / 2.0

    def step(self, u):
        self.t += 1
        self.env = 30 + 5 * math.sin(self.t / 15) + (-8 if self.r.random() < 0.03 else 0)
        self.temp += -0.1 * (self.temp - self.env) + 1.2 * u
        return abs(self.temp - 37.0) / 2.0


class Reach(H):  # N12: reaching movement to a target that moves every 50 steps, with motor noise
    def init(self):
        self.x, self.g, self.dir = 0.0, 1.0, 1.0

    def observe(self):
        return abs(self.g - self.x)

    def step(self, u):
        self.t += 1
        if self.t % 50 == 0:
            self.g = self.r.uniform(-2, 2)
        self.x += 0.3 * u * (1 if self.g > self.x else -1) + self.r.gauss(0, 0.03)
        return abs(self.g - self.x)


class Energy(H):  # N5: energy balance (intake vs fluctuating expenditure); starvation and overeating both harm
    def init(self):
        self.e = 0.7

    def observe(self):
        return max(0.0, 0.6 - self.e) / 0.4

    def step(self, u):
        spend = 0.05 + (0.2 if self.r.random() < 0.05 else 0.0)
        self.e += 0.15 * u - spend
        return max(0.0, 0.2 - self.e) * 5 + max(0.0, self.e - 1.0)


class Recurring(H):  # N6: shocks that recur on a fixed pattern, each announced one step ahead by a precursor
    def init(self):
        self.pattern = [self.r.random() < 0.15 for _ in range(40)]
        self.prev_u = 0.0

    def observe(self):
        nxt = self.pattern[(self.t + 1) % 40]
        return (0.9 if nxt else 0.1) + self.r.gauss(0, 0.15)

    def step(self, u):
        shock = 1.0 if self.pattern[self.t % 40] else 0.0
        harm = shock * (1 - self.prev_u)
        self.prev_u = u
        self.t += 1
        return harm


class Channel(H):  # N7: acting on alarms received through a noisy channel (signal detection)
    def init(self):
        self.n = 0

    def observe(self):
        return self.n + self.r.gauss(0, 0.4)

    def step(self, u):
        harm = (1.0 if (self.n == 1 and u < 0.5) else 0.0) + (0.5 if (self.n == 0 and u >= 0.5) else 0.0)
        if self.r.random() < (0.1 if self.n == 0 else 0.2):
            self.n = 1 - self.n
        return harm


class Ecosystem(H):  # N13: Lotka-Volterra predator-prey; the intervention removes predators
    def init(self):
        self.x, self.z = 1.0, 0.5

    def observe(self):
        return abs(self.x - 1.0)

    def step(self, u):
        a, b, c, d, dt = 1.0, 1.0, 1.0, 1.0, 0.05
        self.x += dt * (a * self.x - b * self.x * self.z)
        self.z += dt * (c * self.x * self.z - d * self.z - 0.8 * u * self.z)
        if self.r.random() < 0.03:
            self.z *= 1.6
        self.x, self.z = max(0.01, self.x), max(0.01, self.z)
        return abs(self.x - 1.0)


class Oscillators(H):  # N11: two coupled oscillators (Kuramoto); the intervention is the coupling strength
    def init(self):
        self.p1, self.p2 = 0.0, self.r.uniform(0, 2 * math.pi)

    def observe(self):
        return (1 - math.cos(self.p1 - self.p2))

    def step(self, u):
        k = 0.5 * u
        d = self.p2 - self.p1
        self.p1 += 0.10 + k * math.sin(d)
        self.p2 += 0.16 - k * math.sin(d) + self.r.gauss(0, 0.02)
        return (1 - math.cos(self.p1 - self.p2)) / 2


class Pest(H):  # N9: a pest population across generations whose growth rate drifts; treatment at a threshold
    def init(self):
        self.p, self.g = 0.2, 0.08

    def observe(self):
        return self.p

    def step(self, u):
        self.t += 1
        if self.t % 25 == 0:
            self.g = max(0.0, min(0.25, self.g + self.r.gauss(0, 0.04)))
        self.p = max(0.0, self.p + self.g * self.p * (1 - self.p) - 0.25 * u * self.p)
        return self.p


class Growth(H):  # N10: logistic growth of an organism; nutrient raises the growth rate
    def init(self):
        self.n = 0.05

    def observe(self):
        return 1 - self.n

    def step(self, u):
        rate = 0.02 + 0.08 * u
        self.n += rate * self.n * (1 - self.n)
        if self.r.random() < 0.02:
            self.n *= 0.7
        return 1 - self.n


class Tissue(H):  # N15: random injuries, slow natural healing, repair effort speeds healing
    def init(self):
        self.dmg = 0.0

    def observe(self):
        return self.dmg

    def step(self, u):
        if self.r.random() < 0.05:
            self.dmg = min(1.5, self.dmg + 0.4)
        self.dmg = max(0.0, self.dmg - 0.02 * self.dmg - 0.15 * u * self.dmg)
        return self.dmg


HOSTS = {"N1": Genome, "N2": Reservoir, "N14": Membrane, "N3": Sensor, "N4": Epidemic, "N8": Thermo, "N12": Reach,
         "N5": Energy, "N6": Recurring, "N7": Channel, "N13": Ecosystem, "N11": Oscillators, "N9": Pest, "N10": Growth,
         "N15": Tissue}


def episode(host_cls, mech_cls, seed):
    rng = random.Random(seed)
    h = host_cls(rng)
    m = mech_cls()
    m.reset(random.Random(seed + 7))
    harms, us = [], []
    for _ in range(T):
        u = max(0.0, min(1.0, m.act(max(0.0, h.observe()))))
        harms.append(h.step(u))
        us.append(u)
    return sum(harms) / T + LAMBDA * sum(us) / T
