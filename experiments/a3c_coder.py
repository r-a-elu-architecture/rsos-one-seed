"""A3c coder (design: results/a3c_dragon_design.json, `coder` + `packing`).

Exact big-integer arithmetic coder: state (L, W, D), interval [L/D, (L+W)/D); coding (cum, f, T):
L = L*T + W*cum, W = W*f, D = D*T. Termination: the smallest k >= 1 with an integer V, V/rB(k) in the interval,
rB(k) = B0 * B1^(k-1). Words: d1 = V // B1^(k-1) in A0, then base-B1 digits in A1, joined by single spaces.

Enc and Dec share one method, `sym`, so every model is written once and runs identically on both sides.
"""

import bisect
import re

try:
    import tiktoken
    _E = tiktoken.get_encoding("o200k_base")
except Exception:  # noqa: BLE001
    _E = None


class Undecodable(Exception):
    pass


def _alphabets():
    a1 = []
    for i in range(_E.n_vocab):
        try:
            s = _E.decode_single_token_bytes(i).decode()
        except Exception:  # noqa: BLE001
            continue
        if re.fullmatch(r" [a-z]{2,}", s):
            a1.append(s[1:])
    a1 = sorted(set(a1))
    a0 = [w for w in a1 if len(_E.encode(w)) == 1]
    return a0, a1


A0, A1 = _alphabets()
B0, B1 = len(A0), len(A1)
I0 = {w: i for i, w in enumerate(A0)}
I1 = {w: i for i, w in enumerate(A1)}


class Enc:
    enc = True

    def __init__(self):
        self.L, self.W, self.D = 0, 1, 1
        self.nsym = 0

    def put(self, cum, f, T):
        if f <= 0 or cum < 0 or cum + f > T:
            raise ValueError("bad symbol")
        self.L = self.L * T + self.W * cum
        self.W *= f
        self.D *= T
        self.nsym += 1

    def sym(self, items, freqs, val):
        """Code `val` (must be in items) with integer freqs; returns val."""
        i = items.index(val)
        self.put(sum(freqs[:i]), freqs[i], sum(freqs))
        return val

    def uni(self, n, v):
        if not 0 <= v < n:
            raise ValueError("uniform out of range")
        self.put(v, 1, n)
        return v

    def cumsym(self, cum, idx):
        """cum: inclusive cumulative list/array of ints (cum[-1] = T)."""
        lo = int(cum[idx - 1]) if idx else 0
        self.put(lo, int(cum[idx]) - lo, int(cum[-1]))
        return idx

    def words(self):
        return terminate(self.L, self.W, self.D)


class Dec:
    enc = False

    def __init__(self, msg):
        ws = msg.split(" ")
        if not ws or ws[0] not in I0 or any(w not in I1 for w in ws[1:]) or msg != " ".join(ws):
            raise Undecodable("alphabet")
        v = I0[ws[0]]
        for w in ws[1:]:
            v = v * B1 + I1[w]
        self.V, self.rB, self.k = v, B0 * B1 ** (len(ws) - 1), len(ws)
        self.msg = msg
        self.L, self.W, self.D = 0, 1, 1
        self.nsym = 0

    def target(self, T):
        t = (self.V * self.D * T - self.L * T * self.rB) // (self.W * self.rB)
        if not 0 <= t < T:
            raise Undecodable("target")
        return t

    def put(self, cum, f, T):
        self.L = self.L * T + self.W * cum
        self.W *= f
        self.D *= T
        self.nsym += 1
        if self.nsym > 20000:
            raise Undecodable("runaway")

    def sym(self, items, freqs, val=None):
        T = sum(freqs)
        t = self.target(T)
        c = 0
        for i, f in enumerate(freqs):
            if c <= t < c + f:
                self.put(c, f, T)
                return items[i]
            c += f
        raise Undecodable("sym")

    def uni(self, n, v=None):
        t = self.target(n)
        self.put(t, 1, n)
        return t

    def cumsym(self, cum, idx=None):
        T = int(cum[-1])
        t = self.target(T)
        i = bisect.bisect_right(cum, t) if isinstance(cum, list) else int(_np_search(cum, t))
        lo = int(cum[i - 1]) if i else 0
        self.put(lo, int(cum[i]) - lo, T)
        return i

    def check_canonical(self):
        """The decoded symbols must re-terminate to exactly the received words (rejects cut/padded codes)."""
        if terminate(self.L, self.W, self.D) != self.msg:
            raise Undecodable("canonical")


def _np_search(cum, t):
    import numpy as np
    return np.searchsorted(cum, t, side="right")


def terminate(L, W, D):
    k, rB = 1, B0
    while True:
        V = -(-L * rB // D)
        if V * D < (L + W) * rB:
            break
        k += 1
        rB *= B1
    digs = []
    for _ in range(k - 1):
        V, r = divmod(V, B1)
        digs.append(A1[r])
    if V >= B0:
        raise ValueError("termination")
    return " ".join([A0[V]] + digs[::-1])
