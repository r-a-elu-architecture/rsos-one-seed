"""A3c H-pred: the White Dragon's deterministic shared predictor (results/a3c_dragon_design.json), implemented
literally. IMPL = choice where the design is silent; DEV = deviation (both listed in the report).

Instruction + reject reasons: lexer -> skeleton PPM (orders 5..0, -1, PPMD escapes, full exclusion, update
exclusion, halving at 2^13) + entity rank coders over candidate lists from the snapshot book, the message so far
and the task history; all coded with the exact arithmetic coder (a3c_coder) into A0/A1 words.
Edits: NOPS + ranks in a candidate list parsed from the instruction (+ escapes) + chk6 -> words; forward = the same
words relayed; door approve '+'; heal = local snapshot restore (as A3b).

Model updates happen once per message, after it is decoded (the design's "both sides update after a message is
decoded"); the codec object is shared by both sides, so the update is applied exactly once.
"""

import copy
import re

import a1_agents as A
from a3b_hdragon import HDragon, chk6, sha8
from a3c_coder import Dec, Enc, Undecodable

SVCS = ["auth", "billing", "search", "cache", "gateway"]
FLDS = ["replicas", "timeout_ms", "retries", "owner", "region", "log_level", "max_conn", "tier"]
VALS = A.OWNERS + A.REGIONS + A.LEVELS
UNIV = [f"{s}.{f}" for s in SVCS for f in FLDS]
VTYPE = {"owner": A.OWNERS, "region": A.REGIONS, "log_level": A.LEVELS}

_SV, _FL, _VL = "|".join(SVCS), "|".join(FLDS), "|".join(VALS)
# IMPL: WORD restricted to ASCII ([A-Za-z_][A-Za-z0-9_]*), WS to [ \n\t\r]+, NUM to 1-7 digits; any other single
# character (Unicode letters, other whitespace) is a PUN unit. Concatenation of surfaces is exact by construction.
LEX = re.compile(
    rf"(?P<K>(?<![\w-])(?:{_SV})\.(?:{_FL})(?![\w-]))|(?P<S>(?<![\w-])(?:{_SV})(?![\w-]))|"
    rf"(?P<V>(?<![\w-])(?:{_VL})(?![\w-]))|(?P<F>(?<![\w-])(?:{_FL})(?!\w))|(?P<N>\d{{1,7}})|"
    rf"(?P<W>[A-Za-z_][A-Za-z0-9_]*)|(?P<WS>[ \n\t\r]+)|(?P<P>[\s\S])")
TAG = {c: "\x01" + c for c in "KSVFN"}
TAGC = {v: k for k, v in TAG.items()}
END, ESC, NOVEL = "\x03END", "\x05ESC", "\x05NOVEL"
START = {"I": "\x04I", "R": "\x04R"}
WCH = [chr(c) for c in range(ord("A"), ord("Z") + 1)] + [chr(c) for c in range(ord("a"), ord("z") + 1)] + ["_"]
WCH2 = WCH + [str(d) for d in range(10)]
WSCH = [" ", "\n", "\t", "\r"]
STOP = "\x06"
HALF = 1 << 13


def lex(text):
    out = []
    for m in LEX.finditer(text):
        out.append((m.lastgroup, m.group(0)))
    assert "".join(s for _, s in out) == text
    return out


def skel(u):
    c, s = u
    return TAG[c] if c in TAG else "\x02" + s


def halve(tab):
    for k in tab:
        tab[k] = (tab[k] + 1) // 2


class Model:
    """All adaptive state (integer counts in dicts, canonical insertion order)."""

    def __init__(self):
        self.ppm = {}                                   # ctx tuple -> {sym: count}
        self.vocab = [TAG[c] for c in "KSVFN"] + [END]
        self.vset = set(self.vocab)
        self.chars = {}                                 # (c1, c2) -> {ch: count}
        self.ranks = {}                                 # (cls, ctx) -> {rank|ESC: count}
        self.small = {}                                 # name -> {sym: count}

    def rank_tab(self, key):
        return self.ranks.setdefault(key, {})

    def halve_all(self):
        for d in (self.ppm, self.chars, self.ranks, self.small):
            for t in d.values():
                halve(t)


def bump(tab, sym, n=1):
    tab[sym] = tab.get(sym, 0) + n
    if sum(tab.values()) > HALF:
        halve(tab)


# ---------------------------------------------------------------- adaptive small tables (counts start at 1)

def code_small(cd, M, name, items, val, upd):
    tab = M.small.get(name, {})
    freqs = [tab.get(x, 0) + 1 for x in items]
    got = cd.sym(items, freqs, val)
    upd.append(("small", name, got))
    return got


def code_rank(cd, M, key, n, r, upd):
    """Rank r in [0, n) or ESC; table counts start at 1."""
    tab = M.ranks.get(key, {})
    items = list(range(n)) + [ESC]
    freqs = [tab.get(x, 0) + 1 for x in items]
    got = cd.sym(items, freqs, r)
    upd.append(("rank", key, got))
    return got


# ---------------------------------------------------------------- context for one message

class Ctx:
    def __init__(self, S, hist, changed, mode="I", extra_keys=(), extra_vals=()):
        self.S = S                                  # dict (ordered) snapshot
        self.Sk = list(S)
        self.svc_order = []
        for k in self.Sk:
            s = k.split(".")[0]
            if s not in self.svc_order:
                self.svc_order.append(s)
        self.hist = hist                            # list of unit lists (earlier instructions of this task)
        self.changed = changed                      # list of key lists, most recent last
        self.mode = mode
        self.extra_keys = list(extra_keys)
        self.extra_vals = list(extra_vals)
        self.U = []                                 # units so far


def dedup(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def prev_nonws(U):
    for c, s in reversed(U):
        if c != "WS":
            return c, s
    return None


def list_ctx(U):
    p = prev_nonws(U)
    return bool(p) and ((p[0] == "P" and p[1] in ",;(-") or (p[0] == "W" and p[1] in ("and", "or")))


def last_of(U, cls):
    for c, s in reversed(U):
        if c == cls:
            return s
    return None


def last_svc(U):
    for c, s in reversed(U):
        if c == "S":
            return s
        if c == "K":
            return s.split(".")[0]
    return None


def k_cands(cx):
    U, S = cx.U, cx.S
    lastK = last_of(U, "K")
    inU = [s for c, s in U if c == "K"]
    out = []
    if list_ctx(U) and lastK:
        sv = lastK.split(".")[0]
        if lastK in cx.Sk:
            i = cx.Sk.index(lastK)
            nxt = [k for k in cx.Sk[i + 1:] if k.split(".")[0] == sv and k not in inU]
            out += nxt[:1]
        if sv in cx.svc_order and cx.svc_order.index(sv) + 1 < len(cx.svc_order):
            k2 = cx.svc_order[cx.svc_order.index(sv) + 1] + "." + lastK.split(".")[1]
            if k2 in S:
                out.append(k2)
    out += inU[::-1]
    if cx.mode == "R":
        out += cx.extra_keys
    ls = last_svc(U)
    if ls:
        out += [k for k in cx.Sk if k.split(".")[0] == ls]
    for ks in cx.changed[-3:][::-1]:
        out += ks
    out += cx.Sk
    out += UNIV
    return dedup(out), (list_ctx(U), bool(inU))


def s_cands(cx):
    U = cx.U
    inU = [s for c, s in U if c == "S"]
    out = []
    lastS = last_of(U, "S")
    if lastS and lastS in cx.svc_order:
        out += [s for s in cx.svc_order[cx.svc_order.index(lastS) + 1:] if s not in inU][:1]
    elif not lastS:
        out += [s for s in cx.svc_order if s not in inU][:1]       # IMPL: no SVC yet -> first service of S
    lastK = last_of(U, "K")
    if lastK:
        out.append(lastK.split(".")[0])
    out += inU[::-1]
    out += SVCS
    return dedup(out), (list_ctx(U),)


def f_cands(cx):
    U = cx.U
    inU = [s for c, s in U if c == "F"]
    out = []
    lastK = last_of(U, "K")
    if lastK:
        sv, fd = lastK.split(".")
        fs = [k.split(".")[1] for k in cx.Sk if k.split(".")[0] == sv]
        if fd in fs:
            out += [f for f in fs[fs.index(fd) + 1:] if f not in inU][:1]
    out += inU[::-1]
    out += FLDS
    return dedup(out), ()


def ktype(k):
    return "V" if k and k.split(".")[1] in VTYPE else "N"


def fits(cls, v):
    return v in VALS if cls == "V" else bool(re.fullmatch(r"\d{1,7}", v))


def vn_cands(cx, cls, lastK=None, U=None):
    U = cx.U if U is None else U
    S = cx.S
    if lastK is None:
        lastK = last_of(U, "K")
    out = []
    if lastK and lastK in S and ktype(lastK) == cls and fits(cls, S[lastK]):
        out.append(S[lastK])
    out += [s for c, s in U if c == cls][::-1]
    if cx.mode == "R":
        out += [v for v in cx.extra_vals if fits(cls, v)]
    if cls == "N":
        ns = [int(s) for c, s in U if c == "N"]
        if len(ns) >= 2:
            a, b = ns[-2], ns[-1]
            ar = [a + b, a - b, b - a, a * b, a // b if b else None, 2 * a, a // 2, min(a + b, 9)]
            out += [str(x) for x in ar if x is not None and x >= 0]
    if lastK:
        fd = lastK.split(".")[1]
        out += [S[k] for k in cx.Sk if k.split(".")[1] == fd and k != lastK and fits(cls, S[k])]
    for h in cx.hist[-20:][::-1]:
        out += [s for c, s in h if c == cls][::-1]
    if cls == "V":
        if lastK and lastK.split(".")[1] in VTYPE:
            out += VTYPE[lastK.split(".")[1]]
        out += VALS
    out = [v for v in dedup(out) if fits(cls, v)]
    p = prev_nonws(U)
    ps = p[1] if p and p[0] in ("W", "P") else None
    bucket = ps if ps in ("=", "to", "from", "`", "(", "of") else "other"
    return out, (cls, bucket)


def code_num_escape(cd, M, v, upd):
    n = code_small(cd, M, "ndig", list(range(1, 8)), len(v) if v is not None else None, upd)
    out, prev = "", "^"
    for i in range(n):
        d = code_small(cd, M, "dig" + prev, list("0123456789"), v[i] if v is not None else None, upd)
        out += d; prev = d
    return out


def code_entity(cd, M, cx, cls, val, upd, ctxname=None):
    if cls == "K":
        cands, tctx = k_cands(cx)
    elif cls == "S":
        cands, tctx = s_cands(cx)
    elif cls == "F":
        cands, tctx = f_cands(cx)
    else:
        cands, tctx = vn_cands(cx, cls)
    key = (cls,) + tuple(tctx) if ctxname is None else (cls, ctxname) + tuple(tctx)
    r = (cands.index(val) if val in cands else ESC) if cd.enc else None
    got = code_rank(cd, M, key, len(cands), r, upd)
    if got != ESC:
        return cands[got]
    if cls == "N":
        return code_num_escape(cd, M, val, upd)
    raise Undecodable("entity escape " + cls)        # K/S/V/F lists contain the whole universe


# ---------------------------------------------------------------- novel literal spelling

def code_novel(cd, M, surface, upd):
    kind = None
    if cd.enc:
        kind = "w" if re.fullmatch(r"[A-Za-z_]\w*", surface) else "s" if re.fullmatch(r"[ \n\t\r]+", surface) else "p"
    kind = cd.sym(["w", "s", "p"], [1, 1, 1], kind)
    if kind == "p":
        return "\x02" + chr(cd.uni(0x110000, ord(surface) if cd.enc else None))
    out, i = "", 0
    while True:
        if kind == "w":
            items = WCH if i == 0 else WCH2 + [STOP]
            c2 = (out[-2:] if len(out) >= 2 else ("^" + out)[-2:] if out else "^^")
            tab = M.chars.get(c2, {})
            freqs = [tab.get(x, 0) + 1 for x in items]
        else:
            items = WSCH if i == 0 else WSCH + [STOP]      # IMPL: whitespace characters uniform
            freqs = [1] * len(items)
            c2 = None
        v = (surface[i] if i < len(surface) else STOP) if cd.enc else None
        ch = cd.sym(items, freqs, v)
        if kind == "w":
            upd.append(("char", c2, ch))
        if ch == STOP:
            break
        out += ch; i += 1
    return "\x02" + out


# ---------------------------------------------------------------- skeleton + message

def code_skel(cd, M, h, s, upd):
    excl = set()
    for o in range(5, -1, -1):
        if len(h) < o:
            continue
        ctx = tuple(h[len(h) - o:])
        tab = M.ppm.get(ctx)
        if not tab:
            continue
        cand = [(x, 2 * c - 1) for x, c in tab.items() if x not in excl and c > 0]
        if not cand:
            continue
        items = [x for x, _ in cand] + [ESC]
        freqs = [f for _, f in cand] + [len(cand)]
        v = (s if s in tab and s not in excl else ESC) if cd.enc else None
        got = cd.sym(items, freqs, v)
        if got != ESC:
            return got, o
        excl.update(items[:-1])
    items = [x for x in M.vocab if x not in excl] + [NOVEL]
    v = (s if s in M.vset and s not in excl else NOVEL) if cd.enc else None
    got = cd.sym(items, [1] * len(items), v)
    if got != NOVEL:
        return got, -1
    return None, -2


def code_message(cd, M, cx, units):
    """Encode (units given) or decode (units None) one message's symbol stream. Returns (units, updates)."""
    h = [START[cx.mode]]
    upd = []
    out = []
    i = 0
    while True:
        if cd.enc:
            s = skel(units[i]) if i < len(units) else END
        else:
            s = None
        got, o = code_skel(cd, M, h, s, upd)
        if o == -2:
            lit = code_novel(cd, M, units[i][1] if cd.enc else None, upd)
            got = lit
        upd.append(("ppm", tuple(h), got, o))
        if got == END:
            break
        if got in TAGC:
            cls = TAGC[got]
            val = code_entity(cd, M, cx, cls, units[i][1] if cd.enc else None, upd)
            u = (cls, val)
        else:
            sur = got[1:]
            u = ("WS" if re.fullmatch(r"[ \n\t\r]+", sur) else
                 "W" if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", sur) else "P", sur)
        if cd.enc and u != units[i]:
            raise ValueError("encoder desync")
        out.append(u)
        cx.U.append(u)
        h.append(got)
        i += 1
        if i > 5000:
            raise Undecodable("too long")
    return out, upd


def apply_updates(M, upd):
    for x in upd:
        if x[0] == "ppm":
            _, h, s, o = x
            lo = max(o, 0)
            for oo in range(lo, 6):
                if len(h) < oo:
                    continue
                ctx = tuple(h[len(h) - oo:])
                bump(M.ppm.setdefault(ctx, {}), s)
            if s not in M.vset:
                M.vocab.append(s); M.vset.add(s)
        elif x[0] == "char":
            bump(M.chars.setdefault(x[1], {}), x[2])
        elif x[0] == "rank":
            bump(M.ranks.setdefault(x[1], {}), x[2])
        elif x[0] == "small":
            bump(M.small.setdefault(x[1], {}), x[2])


# ---------------------------------------------------------------- edits

def edit_cands(units, S):
    """Candidate ops from the instruction units (design: edits edge, encode, steps 1-4)."""
    keys = dedup([s for c, s in units if c == "K"])
    pos = {}
    for i, (c, s) in enumerate(units):
        if c == "K" and s not in pos:
            pos[s] = i
    out = []
    for k in keys:
        if k not in S:
            cls = ktype(k)
            vs = [s for c, s in units[pos[k] + 1:] if c == cls or (k.endswith(".tier") and c == "W"
                                                                      and s in ("gold", "silver", "bronze"))]
            if vs:
                out.append(("add", k, vs[0]))
    txt = "".join(s for _, s in units)
    if re.search(r"Delete|delete|Remove|remove", txt):
        out += [("del", k, None) for k in keys if k in S]
    for k in keys:
        if k in S:
            cls = ktype(k)
            for c, s in units[pos[k] + 1:]:
                if (c == cls or (k.endswith(".tier") and c == "W")) and s != S[k]:
                    out.append(("set", k, s))
    return dedup(out)[:16]


def ops_between(old, new):
    """IMPL: canonical op order = sets in book order, deletes in book order, adds in new order."""
    ops = [("set", k, new[k]) for k in old if k in new and new[k] != old[k]]
    ops += [("del", k, None) for k in old if k not in new]
    ops += [("add", k, new[k]) for k in new if k not in old]
    return ops


def apply_ops(S, ops):
    s = dict(S)
    for t, k, v in ops:
        if t == "del":
            s.pop(k)
        else:
            s[k] = v
    return s


def code_value(cd, M, cx, k, v, upd):
    """VALUE: flag {model, raw} (IMPL), then the V/N rank model in context 'edit', or raw UTF-8 bytes."""
    cls = ktype(k)
    flag = ("m" if fits(cls, v) else "r") if cd.enc else None
    tab = M.small.get("vflag", {})
    flag = cd.sym(["m", "r"], [tab.get("m", 0) + 15, tab.get("r", 0) + 1], flag)
    upd.append(("small", "vflag", flag))
    if flag == "m":
        cands, tctx = vn_cands(cx, cls, lastK=k, U=cx.U)
        key = (cls, "edit")
        r = (cands.index(v) if v in cands else ESC) if cd.enc else None
        got = code_rank(cd, M, key, len(cands), r, upd)
        if got != ESC:
            return cands[got]
        if cls == "N":
            return code_num_escape(cd, M, v, upd)
        raise Undecodable("value escape")
    b = v.encode() if cd.enc else None
    n = cd.uni(64, len(b) - 1 if cd.enc else None) + 1
    bs = bytes(cd.uni(256, b[i] if cd.enc else None) for i in range(n))
    try:
        return bs.decode()
    except UnicodeDecodeError:
        raise Undecodable("raw value")


def code_edits(cd, M, instr_units, S, ops, chk):
    """Edits stream: NOPS, OP*, CHK6. Returns (ops, chk, updates)."""
    upd = []
    cx = Ctx(S, [], [], "I")
    cx.U = list(instr_units)
    n = code_small(cd, M, "nops", list(range(9)), len(ops) if cd.enc else None, upd)
    cur = dict(S)
    C = edit_cands(instr_units, S)
    got_ops = []
    for j in range(n):
        op = ops[j] if cd.enc else None
        r = (C.index(op) if op in C else ESC) if cd.enc else None
        g = code_rank(cd, M, ("edits",), len(C), r, upd)
        if g != ESC:
            o = C[g]
        else:
            t = cd.sym(["set", "del", "add"], [1, 1, 1], op[0] if cd.enc else None)
            lines = list(cur)
            if t in ("set", "del"):
                li = cd.uni(len(lines), lines.index(op[1]) if cd.enc else None) if lines else None
                if li is None:
                    raise Undecodable("empty state")
                k = lines[li]
            else:
                free = [x for x in UNIV if x not in cur]
                if not free:
                    raise Undecodable("no free key")
                k = free[cd.uni(len(free), free.index(op[1]) if cd.enc else None)]
            v = code_value(cd, M, cx, k, op[2] if cd.enc else None, upd) if t != "del" else None
            o = (t, k, v)
        if o[0] == "add" and o[1] in cur or o[0] != "add" and o[1] not in cur:
            raise Undecodable("invalid op")
        cur = apply_ops(cur, [o])
        got_ops.append(o)
        C = [c for c in C if c != o]
    c = cd.uni(10 ** 6, int(chk) if cd.enc else None)
    return got_ops, f"{c:06d}", upd


# ---------------------------------------------------------------- the codec

class HPred(HDragon):
    name = "Hp"
    primed = None          # frozen Model after priming (set by a3c_run.load_primed)

    def table_tok(self):
        return 0

    def new_task(self, init_text):
        HDragon.new_task(self, init_text)
        if not getattr(self, "persist", False):
            self.M = copy.deepcopy(self.primed) if self.primed is not None else Model()
        elif not hasattr(self, "M"):
            self.M = Model()
        self.hist, self.changed = [], []
        self.cur_units = []
        self.pending_edits = {}
        self.stats.update({"instr_bits": 0, "instr_chars": 0, "reason_bits": 0, "reason_chars": 0,
                           "n_instr": 0, "n_reason": 0, "edits_fallback": 0, "nak": 0})

    # --- prose
    def _ctx(self, S, mode, extra_keys=(), extra_vals=()):
        return Ctx(S, self.hist, self.changed, mode, extra_keys, extra_vals)

    def enc_prose(self, text, S, mode, extra=((), ())):
        cd = Enc()
        code_message(cd, self.M, self._ctx(S, mode, *extra), lex(text))
        return cd.words(), cd

    def dec_prose(self, msg, S, mode, extra=((), ())):
        cd = Dec(msg)
        units, upd = code_message(cd, self.M, self._ctx(S, mode, *extra), None)
        cd.check_canonical()
        return "".join(s for _, s in units), units, upd, cd

    def enc_instr(self, instr, planner_book):
        w, cd = self.enc_prose(instr, A.state_of_text(planner_book), "I")
        self._sent = instr
        return w

    def receive_instr(self, msg, work, snap, planner_book):
        if sha8(work) != sha8(snap):                      # mismatch repair from the snapshot: 0 tokens (A3b)
            work = snap
        S = A.state_of_text(work)
        t, units, upd, cd = self.dec_prose(msg, S, "I")
        self._commit_instr(t, units, upd, msg)
        return t, work, []

    def _commit_instr(self, t, units, upd, msg):
        apply_updates(self.M, upd)
        self.cur_units = units
        self.hist.append(units)
        self.stats["n_instr"] += 1
        self.stats["instr_chars"] += len(t)
        self.stats["instr_bits"] += bits_of(msg)

    # --- edits (worker -> checker; forward relays the same words)
    def enc_edits(self, old_text, new_text):
        old, new = A.state_of_text(old_text), A.state_of_text(new_text)
        ops = ops_between(old, new)
        if len(ops) > 8 or A.text_of(apply_ops(old, ops)) != new_text:
            self.stats["edits_fallback"] += 1             # DEV: A3b H-dragon format behind '~'
            self._last_base = old_text
            self._last_edits = "~" + HDragon.enc_edits(self, old_text, new_text)
            return self._last_edits
        self._last_base = old_text
        cd = Enc()
        try:
            code_edits(cd, self.M, self.cur_units, old, ops, chk6(new_text))
            w = cd.words()
        except (Undecodable, ValueError):
            self.stats["edits_fallback"] += 1
            w = "~" + HDragon.enc_edits(self, old_text, new_text)
        self._last_edits = w
        return w

    def dec_edits(self, msg, book_text):
        if msg.startswith("~"):
            return HDragon.dec_edits(self, msg[1:], book_text)
        book = A.state_of_text(book_text)
        cd = Dec(msg)
        ops, chk, upd = code_edits(cd, self.M, self.cur_units, book, None, None)
        cd.check_canonical()
        t = A.text_of(apply_ops(book, ops))
        if chk6(t) != chk:
            raise Undecodable("chk6")
        self.pending_edits[msg] = upd
        return t

    def approved(self, new_text):
        # the approved edits message's model updates are applied once (both sides hold the same words)
        if self._last_edits in self.pending_edits:
            apply_updates(self.M, self.pending_edits[self._last_edits])
        self.pending_edits = {}
        old = A.state_of_text(self._last_base)
        new = A.state_of_text(new_text)
        self.changed.append([k for k in dict.fromkeys(list(old) + list(new)) if old.get(k) != new.get(k)])

    # --- door
    def _reason_extra(self, base_text, attempted_text):
        units = self.cur_units
        old, new = A.state_of_text(base_text), A.state_of_text(attempted_text)
        ops = ops_between(old, new)
        ek = dedup([s for c, s in units if c == "K"] + [k for _, k, _ in ops])
        ev = dedup([s for c, s in units if c in ("V", "N")] + [v for _, _, v in ops if v])
        return ek, ev

    def enc_verdict(self, good, reason, base_text, attempted_text):
        if good:
            return "+"
        w, _ = self.enc_prose(reason, A.state_of_text(base_text), "R", self._reason_extra(base_text, attempted_text))
        return w

    def dec_verdict(self, msg, base_text, attempted_text):
        if msg == "+":
            return True, None
        t, units, upd, _ = self.dec_prose(msg, A.state_of_text(base_text), "R",
                                          self._reason_extra(base_text, attempted_text))
        apply_updates(self.M, upd)
        self.stats["n_reason"] += 1
        self.stats["reason_chars"] += len(t)
        self.stats["reason_bits"] += bits_of(msg)
        return False, t

    def do_forward(self, m_edits, approved_text, planner_book):
        msgs = [("checker", "planner", m_edits, "msg")]
        try:
            return self.dec_edits(m_edits, planner_book), msgs
        except Undecodable:
            healed, chan = self.chunk_heal(approved_text, planner_book)
            return approved_text, msgs + [("planner", "checker", x, "heal") for x in chan]


def bits_of(msg):
    from a3c_coder import B0, B1
    import math
    k = len(msg.split(" "))
    return math.log2(B0) + (k - 1) * math.log2(B1)
