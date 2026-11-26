"""MAP1 stage 1: the 15 layer-2 mechanisms, one per node, taken from the A (signal -> protocol) and K (cascade)
columns of the turquoise rows of map/MAP_VAKOG_V1.md (sealed 21 Nov 2026 08:24). Written and pushed BEFORE any
layer-1 host exists. Every mechanism has the same interface, so any mechanism can be applied to any host:
    m.reset(); u = m.act(y)    y >= 0 = the host's tension signal (0 = no tension);  u in [0, 1] = intervention
No mechanism is tuned to any host: every constant below is fixed here, on the generic tension scale.
"""
import random


class M:
    def reset(self, rng=None):
        self.rng = rng or random.Random(0)
        self.t = 0
        self.u = 0.0
        self.init()

    def init(self):
        pass


class Restore(M):  # N1 seed: hash mismatch -> green-dot check, heal back to the sealed state
    def init(self):
        self.ref, self.seen, self.hold = 0.0, [], 0

    def act(self, y):
        self.t += 1
        if self.t <= 5:
            self.seen.append(y)
            self.ref = sum(self.seen) / len(self.seen)
            return 0.0
        if abs(y - self.ref) > 0.3:
            self.hold = 3
        self.hold -= 1
        return 1.0 if self.hold >= 0 else 0.0


class Clamp(M):  # N2 laws: violation -> constitution check, refuse (hard bound)
    def act(self, y):
        return 1.0 if y > 0.8 else 0.0


class Scope(M):  # N14 boundary: overflow -> compress the excess over capacity
    def act(self, y):
        return max(0.0, min(1.0, (y - 0.5) / 0.5))


class Quarantine(M):  # N3 sensing: anomaly -> blind, quarantine while anomalous
    def init(self):
        self.m, self.v = None, 0.05

    def act(self, y):
        if self.m is None:
            self.m = y
            return 0.0
        sd = self.v ** 0.5
        anomalous = (y - self.m) > 2.5 * sd
        if not anomalous:
            d = y - self.m
            self.m += 0.1 * d
            self.v = 0.9 * self.v + 0.1 * d * d
        return 1.0 if anomalous else 0.0


class Graded(M):  # N4 immune: danger -> graded response; memory lowers thresholds after first activation
    def init(self):
        self.mem = 0.0

    def act(self, y):
        a, b, c = 0.3 - self.mem, 0.6 - self.mem, 0.9 - self.mem
        u = 1.0 if y > c else (0.66 if y > b else (0.33 if y > a else 0.0))
        if u > 0:
            self.mem = 0.1
        return u


class PI(M):  # N8 control: mismatch -> re-derive (proportional + integral toward zero tension)
    def init(self):
        self.i = 0.0

    def act(self, y):
        self.i = 0.99 * self.i + 0.1 * y
        return max(0.0, min(1.0, 0.8 * y + 0.2 * self.i))


class ActCheck(M):  # N12 action: result -> continue if it helped, otherwise change course
    def init(self):
        self.prev, self.u = None, 0.5

    def act(self, y):
        if self.prev is not None and y > self.prev:
            self.u = 1.0 - self.u
        self.prev = y
        return self.u


class Budget(M):  # N5 metabolism: cost signal -> spend only when tension is high, within a fixed budget
    def init(self):
        self.left = 40.0  # per 200-step episode

    def act(self, y):
        if y > 0.7 and self.left >= 1.0:
            self.left -= 1.0
            return 1.0
        return 0.0


class Case(M):  # N6 memory: retrieval hit -> reuse the response that worked for this kind of tension before
    def init(self):
        self.table, self.last = {}, None

    def act(self, y):
        b = min(9, int(y * 5))
        if self.last is not None:
            lb, lu, ly = self.last
            s = self.table.setdefault(lb, {0.0: [0, 0.0], 1.0: [0, 0.0]})
            s[lu][0] += 1
            s[lu][1] += y - ly
        s = self.table.get(b)
        if s is None or s[0.0][0] == 0 or s[1.0][0] == 0:
            u = 1.0 if (s is None or s[1.0][0] == 0) else 0.0
        else:
            u = 1.0 if s[1.0][1] / s[1.0][0] < s[0.0][1] / s[0.0][0] else 0.0
        self.last = (b, u, y)
        return u


class Confirm(M):  # N7 communication: READY or failed proof -> adopt only after two confirmations
    def init(self):
        self.hi, self.lo, self.on = 0, 0, False

    def act(self, y):
        if y > 0.5:
            self.hi, self.lo = self.hi + 1, 0
        else:
            self.lo, self.hi = self.lo + 1, 0
        if self.hi >= 2:
            self.on = True
        if self.lo >= 2:
            self.on = False
        return 1.0 if self.on else 0.0


class Consensus(M):  # N13 relations: disagreement -> consensus of three agents
    def act(self, y):
        votes = (y > 0.3) + (y > 0.5) + (y > 0.7)
        return 1.0 if votes >= 2 else 0.0


class Echo(M):  # N11 mirror: re-entry steers: what re-enters is carried forward
    def act(self, y):
        self.u = max(0.0, min(1.0, 0.7 * self.u + 0.5 * y))
        return self.u


class Inherit(M):  # N9 lineage: inherit the threshold, mutate it each generation, keep what lowered tension
    def init(self):
        self.th, self.cand, self.prev_mean, self.buf = 0.5, None, None, []

    def act(self, y):
        self.t += 1
        self.buf.append(y)
        if self.t % 25 == 0:
            mean = sum(self.buf) / len(self.buf)
            self.buf = []
            if self.cand is not None and self.prev_mean is not None and mean > self.prev_mean:
                self.th = self.cand[0]  # revert to the parent
            self.prev_mean = mean
            parent = self.th
            self.th = max(0.05, min(1.5, self.th + self.rng.gauss(0, 0.1)))
            self.cand = (parent,)
        return 1.0 if y > self.th else 0.0


class Deficit(M):  # N10 growth: a deficit is heard -> land a particle sized to the deficit, then wait
    def act(self, y):
        self.t += 1
        return max(0.0, min(1.0, y)) if self.t % 5 == 0 else 0.0


class Repair(M):  # N15 heal and evolve: a failure is heard (sudden rise) -> repair pulse
    def init(self):
        self.prev, self.hold = None, 0

    def act(self, y):
        if self.prev is not None and y - self.prev > 0.3:
            self.hold = 5
        self.prev = y
        self.hold -= 1
        return 1.0 if self.hold >= 0 else 0.0


MECHANISMS = {"N1": Restore, "N2": Clamp, "N14": Scope, "N3": Quarantine, "N4": Graded, "N8": PI, "N12": ActCheck,
              "N5": Budget, "N6": Case, "N7": Confirm, "N13": Consensus, "N11": Echo, "N9": Inherit, "N10": Deficit,
              "N15": Repair}
