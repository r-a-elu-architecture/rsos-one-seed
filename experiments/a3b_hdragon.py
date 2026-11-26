"""A3b H-dragon: the White Dragon's hologram palace, implemented from results/a3b_dragon_design.json.

Implemented literally; implementation choices where the design is silent are marked IMPL, deviations DEV
(both listed in the report).

Landings: heal = local mismatch repair from SNAP (0 tokens); walls = chained chk6; edits = word ops + terminal
chk6; door = '+' / '-' + coded reason; forward = predictive (chk6 only, F_final predicted by the planner's codec);
instruction = holographic templates over the shared book + § macros + adaptive dictionary.
"""

import hashlib
import re

import a1_agents as A
from a3b_hologram import Undecodable, bpe  # noqa: F401

SVC = {"auth": "a", "billing": "b", "search": "s", "cache": "c", "gateway": "g"}
FLD = {"replicas": "r", "timeout_ms": "t", "retries": "y", "owner": "o", "region": "g", "log_level": "l",
       "max_conn": "m", "tier": "e"}
KC = {f"{s}.{f}": SVC[s] + FLD[f] for s in SVC for f in FLD}
KEY = {v: k for k, v in KC.items()}
SNAME = {v: k for k, v in SVC.items()}
REG = {"eu-west": "euw", "us-east": "use", "ap-south": "aps", "sa-east": "sae"}
REGI = {v: k for k, v in REG.items()}
KEYPAT = r"[a-z]+\.[a-z_]+"
TABLES = ("T0 a=auth b=billing s=search c=cache g=gateway\nT1 r=replicas t=timeout_ms y=retries o=owner g=region "
          "l=log_level m=max_conn e=tier\nT3 euw=eu-west use=us-east aps=ap-south sae=sa-east\n"
          "T5 1 `k = v` , | 2 k = v nl | 3 - k = v nl | 4 - `k = v` nl | 5 k = v ,\n"
          "T6 S K V Set `K` to `V`. ; R K This is the value of `K`. ; N Change no other key. ; B S The resulting `S` "
          "block is: blk(S,F,1). ; X K Delete the key `K` (its line, currently `C[K]`) from the state. ; L Leave "
          "every other key unchanged, with these final values:nlnl all(F,2) ; A K V Add the key `K` with value `V`. ; "
          "U Leave every other key unchanged. ; Q S n blk ; W n all ; E K `K = F[K]` ; H K V hidden set ; Z K hidden "
          "delete\nT7 §k §K §v §V §c §C §s §S §§ »»\nT8 D1..D99 adaptive")


def sha8(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def chk6(text):
    return f"{int(sha8(text), 16) % 1000000:06d}"


def vin(v):
    return REG.get(v, v)


def vout(w):
    return REGI.get(w, w)


# ---------------------------------------------------------------- rendering (the decoder is the definition)

def fmt(pairs, n):
    if n == 1:
        return ", ".join(f"`{k} = {v}`" for k, v in pairs)
    if n == 2:
        return "\n".join(f"{k} = {v}" for k, v in pairs)
    if n == 3:
        return "\n".join(f"- {k} = {v}" for k, v in pairs)
    if n == 4:
        return "\n".join(f"- `{k} = {v}`" for k, v in pairs)
    return ", ".join(f"{k} = {v}" for k, v in pairs)


def blk(s, F, n):
    return fmt([(k, v) for k, v in F.items() if k.split(".")[0] == SNAME[s]], n)


def allF(F, n):
    return fmt(list(F.items()), n)


SLOTS = {"S": "KV", "R": "K", "N": "", "B": "S", "X": "K", "L": "", "A": "KV", "U": "", "Q": "Sn", "W": "n",
         "E": "K", "H": "KV", "Z": "K"}


def render_tpl(tid, args, C, F):
    """Returns (text, newF). Raises Undecodable on bad slots."""
    F = dict(F)

    def key(a):
        if a not in KEY:
            raise Undecodable("kc " + a)
        return KEY[a]

    if tid == "S":
        k, v = key(args[0]), vout(args[1]); F[k] = v
        return f"Set `{k}` to `{v}`.", F
    if tid == "R":
        return f"This is the value of `{key(args[0])}`.", F
    if tid == "N":
        return "Change no other key.", F
    if tid == "B":
        if args[0] not in SNAME:
            raise Undecodable("svc")
        return f"The resulting `{SNAME[args[0]]}` block is: {blk(args[0], F, 1)}.", F
    if tid == "X":
        k = key(args[0])
        if k not in C or k not in F:
            raise Undecodable("X missing")
        t = f"Delete the key `{k}` (its line, currently `{C[k]}`) from the state."
        del F[k]
        return t, F
    if tid == "L":
        return "Leave every other key unchanged, with these final values:\n\n" + allF(F, 2), F
    if tid == "A":
        k, v = key(args[0]), vout(args[1]); F[k] = v
        return f"Add the key `{k}` with value `{v}`.", F
    if tid == "U":
        return "Leave every other key unchanged.", F
    if tid == "Q":
        if args[0] not in SNAME or args[1] not in "12345":
            raise Undecodable("Q")
        return blk(args[0], F, int(args[1])), F
    if tid == "W":
        if args[0] not in "12345":
            raise Undecodable("W")
        return allF(F, int(args[0])), F
    if tid == "E":
        k = key(args[0])
        if k not in F:
            raise Undecodable("E")
        return f"`{k} = {F[k]}`", F
    if tid == "H":
        F[key(args[0])] = vout(args[1])
        return "", F
    if tid == "Z":
        k = key(args[0])
        if k not in F:
            raise Undecodable("Z")
        del F[k]
        return "", F
    raise Undecodable("tid " + tid)


MACRO = re.compile(r"§(§|[kKvVcC][a-z]{2}|[sS][a-z])")


def render_lit(content, C, F):
    def sub(m):
        g = m.group(1)
        if g == "§":
            return "§"
        t, a = g[0], g[1:]
        if t in "sS":
            if a not in SNAME:
                raise Undecodable("svc")
            return f"`{SNAME[a]}`" if t == "s" else SNAME[a]
        if a not in KEY:
            raise Undecodable("kc")
        k = KEY[a]
        if t in "kK":
            return f"`{k}`" if t == "k" else k
        src = F if t in "vV" else C
        if k not in src:
            raise Undecodable("val")
        return f"`{src[k]}`" if t in "vc" else src[k]
    if re.search(r"§(?!§|[kKvVcC][a-z]{2}|[sS][a-z])", content.replace("§§", "")):
        raise Undecodable("bad macro")
    return MACRO.sub(sub, content)


def lit_args(content):
    return [m.group(1)[1:] for m in MACRO.finditer(content) if m.group(1) != "§"]


def lit_with_args(content, args):
    it = iter(args)
    return MACRO.sub(lambda m: "§§" if m.group(1) == "§" else "§" + m.group(1)[0] + next(it), content)


def parse_items(msg):
    """Wire -> list of items: ('T', tid, args) | ('D', n, args) | ('L', content) | ('^',) | ('/',)."""
    items, i, n = [], 0, len(msg)
    words = []
    while i < n:
        if msg[i].isspace():
            i += 1; continue
        if msg[i] == "«":
            j, buf = i + 1, []
            while True:
                if j >= n:
                    raise Undecodable("open literal")
                if msg[j] == "»":
                    if j + 1 < n and msg[j + 1] == "»":
                        buf.append("»"); j += 2; continue
                    break
                buf.append(msg[j]); j += 1
            words.append(("lit", "".join(buf))); i = j + 1
        else:
            j = i
            while j < n and not msg[j].isspace():
                j += 1
            words.append(("w", msg[i:j])); i = j
    k = 0
    return words, k


def decode_items(msg, dic):
    words, _ = parse_items(msg)
    items, k = [], 0
    while k < len(words):
        kind, w = words[k]
        if kind == "lit":
            items.append(("L", w)); k += 1; continue
        if w in ("^", "/"):
            items.append((w,)); k += 1; continue
        if re.fullmatch(r"D\d+", w):
            idx = int(w[1:])
            if not 1 <= idx <= len(dic):
                raise Undecodable("D index")
            na = len(lit_args(dic[idx - 1]))
            args = [x for _, x in words[k + 1:k + 1 + na]]
            if len(args) != na or any(t != "w" for t, _ in words[k + 1:k + 1 + na]):
                raise Undecodable("D args")
            items.append(("D", idx, args)); k += 1 + na; continue
        if len(w) == 1 and w in SLOTS:
            na = len(SLOTS[w])
            args = [x for _, x in words[k + 1:k + 1 + na]]
            if len(args) != na or any(t != "w" for t, _ in words[k + 1:k + 1 + na]):
                raise Undecodable("slots")
            items.append(("T", w, args)); k += 1 + na; continue
        raise Undecodable("word " + w)
    return items


def render(items, C, F, dic):
    """Joiner rule: ' ' between two consecutive rendering template items; nothing next to literals / D; H, Z
    transparent; '^' suppresses the next joiner; '/' emits '\\n' and suppresses the default joiner."""
    out, prev_tpl, suppress = [], False, False
    F = dict(F)
    new_lits = []
    for it in items:
        if it[0] == "^":
            suppress = True; continue
        if it[0] == "/":
            out.append("\n"); prev_tpl = False; continue
        if it[0] == "T":
            t, F = render_tpl(it[1], it[2], C, F)
            if it[1] in "HZ":
                continue
            if prev_tpl and not suppress:
                out.append(" ")
            out.append(t); prev_tpl, suppress = True, False
        elif it[0] == "D":
            out.append(render_lit(lit_with_args(dic[it[1] - 1], it[2]), C, F)); prev_tpl, suppress = False, False
        else:
            out.append(render_lit(it[1], C, F)); prev_tpl, suppress = False, False
            new_lits.append(it[1])
    return "".join(out), F, new_lits


def wire_of(items):
    parts = []
    for it in items:
        if it[0] in "^/":
            parts.append(it[0])
        elif it[0] == "T":
            parts.append(" ".join([it[1]] + list(it[2])))
        elif it[0] == "D":
            parts.append(" ".join([f"D{it[1]}"] + list(it[2])))
        else:
            parts.append("«" + it[1].replace("»", "»»") + "»")
    return " ".join(parts)


# ---------------------------------------------------------------- the greedy encoder

def parse_list(text, p, n):
    """Pairs of a style-n list starting at p (as long as possible). Returns [(k, v)], end."""
    if n in (1, 5):
        pat = r"`(%s) = ([^`\s]+)`" % KEYPAT if n == 1 else r"(%s) = ([^\s,]+)" % KEYPAT
        sep = ", "
    else:
        pat = {2: r"(%s) = (\S+)", 3: r"- (%s) = (\S+)", 4: r"- `(%s) = ([^`\s]+)`"}[n] % KEYPAT
        sep = "\n"
    pairs, q = [], p
    while True:
        m = re.compile(pat).match(text, q)
        if not m:
            break
        pairs.append((m.group(1), m.group(2))); q = m.end()
        if text.startswith(sep, q) and re.compile(pat).match(text, q + len(sep)):
            q += len(sep)
        else:
            break
    return pairs, q


def sync_items(F, target, scope=None):
    """H/Z items turning F into `target` (restricted to keys of service `scope` if given); None if impossible."""
    items, G = [], dict(F)
    keys = [k for k in F if scope is None or k.split(".")[0] == scope]
    tk = dict(target)
    for k in keys:
        if k not in tk:
            if k not in KC:
                return None
            items.append(("T", "Z", [KC[k]])); del G[k]
    for k, v in target:
        if G.get(k) != v:
            if k not in KC or re.search(r"\s", v) or not v:
                return None
            items.append(("T", "H", [KC[k], vin(v)])); G[k] = v
    return items, G


def tpl_candidates(text, p, C, F):
    """All template matches at p: (items, rendered_len, newF)."""
    out = []

    def add(items, F0):
        try:
            t, F1, _ = render(items, C, F0, [])
        except Undecodable:
            return
        hidden = [x for x in items if x[0] == "T" and x[1] in "HZ"]
        # IMPL cost guard: a match that needs hidden H/Z items is taken only if cheaper than the literal
        if hidden and A.ntok(wire_of(items)) >= A.ntok(make_literal(t, C, F0)) + 2:
            return
        if t and text.startswith(t, p):
            out.append((items, len(t), F1))

    m = re.compile(r"Set `(%s)` to `([^`\s]+)`\." % KEYPAT).match(text, p)
    if m and m.group(1) in KC:
        add([("T", "S", [KC[m.group(1)], vin(m.group(2))])], F)
    m = re.compile(r"This is the value of `(%s)`\." % KEYPAT).match(text, p)
    if m and m.group(1) in KC:
        add([("T", "R", [KC[m.group(1)]])], F)
    for tid in "NU":
        add([("T", tid, [])], F)
    m = re.compile(r"Delete the key `(%s)` \(its line" % KEYPAT).match(text, p)
    if m and m.group(1) in KC:
        add([("T", "X", [KC[m.group(1)]])], F)
    m = re.compile(r"Add the key `(%s)` with value `([^`\s]+)`\." % KEYPAT).match(text, p)
    if m and m.group(1) in KC:
        add([("T", "A", [KC[m.group(1)], vin(m.group(2))])], F)
    m = re.compile(r"`(%s) = ([^`\s]+)`" % KEYPAT).match(text, p)
    if m and m.group(1) in KC:
        add([("T", "E", [KC[m.group(1)]])], F)
    # B, L, Q, W: direct, or after H/Z items that make them match
    m = re.compile(r"The resulting `([a-z]+)` block is: ").match(text, p)
    if m and m.group(1) in SVC:
        s = SVC[m.group(1)]
        add([("T", "B", [s])], F)
        pairs, _ = parse_list(text, m.end(), 1)
        sy = sync_items(F, pairs, m.group(1)) if pairs else None
        if sy and sy[0]:
            add(sy[0] + [("T", "B", [s])], F)
    pre = "Leave every other key unchanged, with these final values:\n\n"
    if text.startswith(pre, p):
        add([("T", "L", [])], F)
        pairs, _ = parse_list(text, p + len(pre), 2)
        sy = sync_items(F, pairs) if pairs else None
        if sy and sy[0]:
            add(sy[0] + [("T", "L", [])], F)
    for n in "12345":
        add([("T", "W", [n])], F)
        for s in SVC.values():
            add([("T", "Q", [s, n])], F)
        pairs, _ = parse_list(text, p, int(n))
        if len(pairs) >= 2:
            svcs = {k.split(".")[0] for k, _ in pairs}
            if len(svcs) == 1:
                sv = svcs.pop()
                if sv in SVC:
                    sy = sync_items(F, pairs, sv)
                    if sy and sy[0]:
                        add(sy[0] + [("T", "Q", [SVC[sv], n])], F)
            sy = sync_items(F, pairs)
            if sy and sy[0]:
                add(sy[0] + [("T", "W", [n])], F)
    return out


def d_candidates(text, p, C, F, dic):
    out = []
    for idx, content in enumerate(dic, 1):
        na = len(lit_args(content))
        rx = ""
        pos = 0
        for m in MACRO.finditer(content):
            rx += re.escape(content[pos:m.start()].replace("§§", "§"))
            g = m.group(1)
            if g == "§":
                rx += re.escape("§")
            elif g[0] == "k":
                rx += r"`(%s)`" % KEYPAT
            elif g[0] == "K":
                rx += r"(%s)" % KEYPAT
            elif g[0] == "s":
                rx += r"`([a-z]+)`"
            elif g[0] == "S":
                rx += r"([a-z]+)"
            elif g[0] in "vc":
                rx += r"`([^`\s]+)`"
            else:
                rx += r"([^\s`(),;]+?)"
            pos = m.end()
        rx += re.escape(content[pos:].replace("§§", "§"))
        m = re.compile(rx).match(text, p)
        if not m:
            continue
        kinds = [g.group(1)[0] for g in MACRO.finditer(content) if g.group(1) != "§"]
        args, last_key, okk = [], None, True
        for kd, val in zip(kinds, m.groups()):
            if kd in "kK":
                if val not in KC:
                    okk = False; break
                args.append(KC[val]); last_key = val
            elif kd in "sS":
                if val not in SVC:
                    okk = False; break
                args.append(SVC[val])
            else:
                src = F if kd in "vV" else C
                kk = last_key if last_key in src and src.get(last_key) == val else \
                    next((k for k in src if src[k] == val and k in KC), None)
                if kk is None:
                    okk = False; break
                args.append(KC[kk])
        if not okk or len(args) != na:
            continue
        try:
            t, _, _ = render([("D", idx, args)], C, F, dic)
        except Undecodable:
            continue
        if text.startswith(t, p) and t:
            out.append(([("D", idx, args)], len(t), F))
    return out


VAL_AFTER = re.compile(r"(`?)(%s)(`?)(\s*(?:=|to|\(|:)\s*)(`?)([^\s`(),;]+?)(`?)(?=[\s`(),;.]|$)" % KEYPAT)


def make_literal(s, C, F):
    """Literal content for text s: keys, services and their values as § macros (IMPL: which spans become macros)."""
    s2 = s.replace("§", "§§")
    out, pos = [], 0
    for m in VAL_AFTER.finditer(s2):
        k = m.group(2)
        if k not in KC:
            continue
        b1, b2, v, c1, c2 = m.group(1), m.group(3), m.group(6), m.group(5), m.group(7)
        if b1 != b2 or c1 != c2:
            continue
        mk = ("§k" if b1 else "§K") + KC[k]
        if F.get(k) == v:
            mv = ("§v" if c1 else "§V") + KC[k]
        elif C.get(k) == v:
            mv = ("§c" if c1 else "§C") + KC[k]
        else:
            mv = c1 + v + c2
        out.append(s2[pos:m.start()]); out.append(mk + m.group(4) + mv); pos = m.end()
    out.append(s2[pos:])
    s3 = "".join(out)

    def keysub(m):
        k = m.group(2)
        if k not in KC:
            return m.group(0)
        return ("§k" if m.group(1) else "§K") + KC[k] if m.group(1) == m.group(3) else m.group(0)
    s3 = re.sub(r"(?<![§\w])(`?)(%s)(`?)(?!\w|\.\w)" % KEYPAT, keysub, s3)

    def svcsub(m):
        return ("§s" if m.group(1) else "§S") + SVC[m.group(2)] if m.group(1) == m.group(3) else m.group(0)
    s3 = re.sub(r"(?<![§\w.])(`?)(%s)(`?)(?![\w.\-])" % "|".join(SVC), svcsub, s3)
    return s3


def encode_text(text, C, F, dic):
    """Greedy longest match (templates, then D entries, then a literal). Returns (items, F_final)."""
    items, p, n, prev_tpl = [], 0, len(text), False
    F = dict(F)

    def best_at(q, joined):
        c = tpl_candidates(text, q, C, F)
        if c:
            return max(c, key=lambda x: x[1]), "T"
        if not joined:
            d = d_candidates(text, q, C, F, dic)
            if d:
                return max(d, key=lambda x: x[1]), "D"
        return None, None

    while p < n:
        pre, q = [], p
        if prev_tpl:
            if text[p] == " ":
                q = p + 1
            elif text[p] == "\n":
                while q < n and text[q] == "\n":
                    pre.append(("/",)); q += 1
            else:
                pre.append(("^",))
        b, kind = best_at(q, False)
        if b and kind == "T":
            items += pre + b[0]; F = b[2]; p = q + b[1]; prev_tpl = True; continue
        if b and kind == "D" and not prev_tpl:
            items += b[0]; p = q + b[1]; prev_tpl = False; continue
        # literal from p to the next position where a template or D entry matches (word starts only)
        r = p + 1
        while r < n:
            if text[r - 1] in " \n" and (tpl_candidates(text, r, C, F) or d_candidates(text, r, C, F, dic)):
                break
            r += 1
        items.append(("L", make_literal(text[p:r], C, F))); p = r; prev_tpl = False
    return items, F


# ---------------------------------------------------------------- the codec

class HDragon:
    name = "Hd"

    def table_tok(self):
        return A.ntok(TABLES)

    def new_task(self, init_text):
        self.dic = []
        self.F_final = None
        self.stats = {"instr_fallback": 0, "edits_fallback": 0, "forward_hit": 0, "forward_miss": 0}

    def _register(self, lits):
        for c in lits:
            if A.ntok(c) >= 4 and len(self.dic) < 99:
                self.dic.append(c)

    def _enc(self, text, C, F):
        try:
            items, Ff = encode_text(text, C, F, self.dic)
            w = wire_of(items)
            got, _, _ = render(decode_items(w, self.dic), C, F, self.dic)
            if got == text:
                return w, Ff
        except Undecodable:
            pass
        self.stats["instr_fallback"] += 1                 # IMPL: whole text as one literal (no macros)
        return "«" + text.replace("§", "§§").replace("»", "»»") + "»", dict(F)

    def _dec(self, w, C, F):
        t, F1, lits = render(decode_items(w, self.dic), C, F, self.dic)
        self._register(lits)
        return t, F1

    # instruction: planner encodes with C = its book; worker heals locally, then renders with C = WORK
    def enc_instr(self, instr, planner_book):
        C = A.state_of_text(planner_book)
        w, Ff = self._enc(instr, C, C)
        self.F_final = Ff
        return w

    def receive_instr(self, msg, work, snap, planner_book):
        heal = []
        if sha8(work) != sha8(snap):                      # mismatch repair from the parental strand: 0 tokens
            work = snap
        C = A.state_of_text(work)
        t, _ = self._dec(msg, C, C)
        return t, work, heal

    # edits: word ops + terminal chk6
    def enc_edits(self, old_text, new_text):
        old, new = A.state_of_text(old_text), A.state_of_text(new_text)
        lines = list(old)
        ops = []
        try:
            for i, k in enumerate(lines):
                if k in new and new[k] != old[k]:
                    ops.append((i, 0, f"{i} {self._val(new[k])}"))
            for i, k in enumerate(lines):
                if k not in new:
                    ops.append((i, 1, f"x{i}"))
            for k in new:
                if k not in old:
                    if k not in KC:
                        raise ValueError(k)
                    ops.append((10 ** 6, 2, f"a{KC[k]} {self._val(new[k])}"))
        except ValueError:
            self.stats["edits_fallback"] += 1             # DEV: H-copy format behind '~' for unencodable edits
            ed = A.edits_between(old, new)
            return "~" + " ".join([A.d_payload(ed), chk6(new_text)]).strip()
        ops.sort(key=lambda x: (x[0], x[1]))
        return " ".join([o for _, _, o in ops] + [chk6(new_text)])

    @staticmethod
    def _val(v):
        w = vin(v)
        if re.fullmatch(r"\d{5,}", w) or not w or re.search(r"\s", w) or w in REGI and w != vin(v):
            raise ValueError(v)
        return w

    def dec_edits(self, msg, book_text):
        if msg.startswith("~"):
            items = msg[1:].split(" ")
            ed = []
            for it in items[:-1]:
                if it.startswith("-"):
                    ed.append((A.OF_ANCHOR.get(it[1:], it[1:]), None))
                else:
                    a, eq, v = it.partition("=")
                    if not eq:
                        raise Undecodable(it)
                    ed.append((A.OF_ANCHOR.get(a, a), A.OF_ANCHOR.get(v, v)))
            chk = items[-1]
        else:
            words = msg.split(" ")
            chk = words[-1]
            ed = None
        if not re.fullmatch(r"\d{6}", chk):
            raise Undecodable("chk")
        book = A.state_of_text(book_text)
        lines = list(book)
        if ed is None:
            ch, dl, ap = {}, [], []
            k = 0
            body = words[:-1]
            while k < len(body):
                w = body[k]
                if re.fullmatch(r"[1-9]?\d", w):
                    if k + 1 >= len(body):
                        raise Undecodable("val")
                    i = int(w)
                    if i >= len(lines):
                        raise Undecodable("line")
                    ch[lines[i]] = vout(body[k + 1]); k += 2
                elif re.fullmatch(r"x[1-9]?\d", w):
                    i = int(w[1:])
                    if i >= len(lines):
                        raise Undecodable("line")
                    dl.append(lines[i]); k += 1
                elif re.fullmatch(r"a[a-z]{2}", w) and w[1:] in KEY:
                    if k + 1 >= len(body):
                        raise Undecodable("val")
                    ap.append((KEY[w[1:]], vout(body[k + 1]))); k += 2
                else:
                    raise Undecodable("op " + w)
            new = dict(book)
            for kk, v in ch.items():
                new[kk] = v
            for kk in dl:
                new.pop(kk, None)
            for kk, v in ap:
                new[kk] = v
        else:
            new = A.apply_ed(book, ed)
        t = A.text_of(new)
        if chk6(t) != chk:
            raise Undecodable("chk mismatch")
        return t

    # door
    def enc_verdict(self, good, reason, base_text, attempted_text):
        if good:
            return "+"
        w, _ = self._enc(reason, A.state_of_text(base_text), A.state_of_text(attempted_text))
        return "-" + w

    def dec_verdict(self, msg, base_text, attempted_text):
        if msg == "+":
            return True, None
        if not msg.startswith("-"):
            raise Undecodable("door")
        t, _ = self._dec(msg[1:], A.state_of_text(base_text), A.state_of_text(attempted_text))
        return False, t

    # forward: predictive; chk6 only, '?' + edits on a miss
    def do_forward(self, m_edits, approved_text, planner_book):
        c = chk6(approved_text)
        msgs = [("checker", "planner", c, "msg")]
        if self.F_final is not None and chk6(A.text_of(self.F_final)) == c:
            self.stats["forward_hit"] += 1
            return A.text_of(self.F_final), msgs
        self.stats["forward_miss"] += 1
        msgs += [("planner", "checker", "?", "msg"), ("checker", "planner", m_edits, "msg")]
        return self.dec_edits(m_edits, planner_book), msgs

    # fallback heal (design's chunk format); used live only after a failed strict decode
    @staticmethod
    def chunk_heal(sender_text, receiver_text):
        s, r = sender_text.split("\n"), receiver_text.split("\n")

        def h2(lines):
            return f"{int(sha8(chr(10).join(lines)), 16) % 100:02d}"
        req = "? " + " ".join(h2(r[j:j + 4]) for j in range(0, len(r), 4))
        if len(s) != len(r):
            return sender_text, [req, sender_text]          # 'W 2': the full state list
        groups = []
        for j in range(0, len(s), 4):
            if h2(s[j:j + 4]) != h2(r[j:j + 4]):
                rows = [ln.split(" = ") for ln in s[j:j + 4]]
                if any(k not in KC for k, _ in rows):
                    return sender_text, [req, sender_text]
                groups.append(f"c{j // 4} " + " ".join(f"{KC[k]} {vin(v)}" for k, v in rows))
        healed = list(r)
        for g in groups:
            j = int(g.split(" ")[0][1:])
            healed[j * 4:j * 4 + 4] = s[j * 4:j * 4 + 4]
        healed = "\n".join(healed)
        if healed != sender_text:
            return sender_text, [req, " ".join(groups + [chk6(sender_text)]), sender_text]
        return healed, [req, " ".join(groups + [chk6(sender_text)])]

    def checker_heal(self, sender_text, checker_book):
        healed, chan = self.chunk_heal(sender_text, checker_book)
        return healed, [("checker", "worker", "!", "heal"), ("checker", "worker", chan[0], "heal")] + \
            [("worker", "checker", x, "heal") for x in chan[1:]]

    def heal_fallback_tok(self, planner_book, work):
        return sum(A.ntok(x) for x in self.chunk_heal(planner_book, work)[1])
