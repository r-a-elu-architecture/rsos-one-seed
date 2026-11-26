"""REAL1 row 2 "ai_ai": two real models solve a split-information task over a limited message channel.

TASK (one per cell, generated from the cell number)
  A small company world: 12 people, 6 teams, 6 offices, 8 cities. Facts (one sentence each): manager(p) -> person,
  mentor(p) -> person, team(p) -> team, home(p) -> city, office(team) -> office, city(office) -> city: 60 facts.
  Question (4 hops): "In which city is the office of the team of the manager of X?"  The facts are split at random
  between agent A and agent B (each about half; the 4 chain facts are never all on one side).
CHANNEL / ROUNDS
  Each round: A sends a message of at most K = 2 facts (the unit = one fact, sent verbatim), then B sends at most K = 2
  facts (B sees A's message of this round). Then both models are asked the question with their own half + everything
  received, and answer "ANSWER: <city>" or "CONTINUE". The first round with an answer ends the episode (B's answer if
  B answered, else A's). At most T = 6 rounds.
  Real models: A = model 1, B = model 2 (experiments/agents/llm.py; keys only from the environment). Laptop ids:
  openrouter:openai/gpt-oss-20b (A) and openrouter:meta-llama/llama-3.1-8b-instruct (B) (env REAL1_AIAI_MODELS, comma).
  mock:0 path (interface check only, never for results): the answer call is replaced by the host's rule resolver
  (follows the 4 hops in the agent's view; answers iff complete); tokens are the estimate below.
WHAT THE SEED CONTROLS: A's message (which of A's own unsent facts to send now). B always runs the standard method.
  Every decision uses only A's knowledge (its own half, the question, the messages exchanged), as the standard does.
STANDARD (default, both agents): "send a full summary of one's half each round", made as strong as a careful
  summariser under the budget: each round the agent sends its K most relevant unsent facts, ordered by (a) the fact's
  subject is the person the question names; (b) relevance 2 = its subject is named in the question or in any message
  exchanged so far, 1 = its subject is the object of an own fact of relevance 2 (one hop of the agent's own chain),
  0 = the rest; (c) its relation word appears in the question (manager / team / office / city); ties in the half's
  fixed order. (A first version without (a) and (c) sent "mentor of X" before "manager of X"; strengthened before any
  comparison was read, rule 1.) The budget is always used
  (a summary of the half is never empty while facts are unsent). Rule-based (not written by the LLM) so that the
  standard and the seed share one action space and the model of the receiver can run it; disclosed as a proxy for an
  LLM-written summary.
BRANCHES (A, same budget K): focus_<rel> for each relation present among A's unsent relevant facts (only that relation,
  by relevance, up to K: concentrated on one part; filled up to K by valid()); ctx (only relevance-2 facts); coupled
  "chain" = A's own linked facts (a fact whose object is the subject of another own fact) starting from the context,
  sent together. At most 6 (relations ranked by their best relevance).
OWN FUTURE (fork) = the receiver's predicted use. A knows which facts exist (every person/team/office has each relation)
  and which are B's (not in A's half), but not their values unless received. The fork samples B's unknown values
  uniformly from each relation's domain with a fresh generator seeded (cell, t, j, 7311): never the real half, never the
  real models. In the fork B runs the standard method and both agents answer by the rule resolver (B's resolver on the
  sampled half); tokens are the estimate.
TOKENS (resource): message tokens = ceil(chars / 4) of the facts sent (estimate; messages are not model outputs); answer
  calls = the real prompt + completion tokens returned by the API (real step) or the estimate ceil(chars / 4) of the
  prompt + 4 output tokens (fork and mock).
REPORT: result = 1 if the answer given is correct else 0; resource = tokens. OBJECTIVE = the result only (rule 4 as
  changed 13:45; tokens are the constraint: valid() keeps A's message within K facts and fills it up to K with the
  standard's next facts, so every branch spends the same per-round message budget as the standard; a branch = "these
  facts first"). Pass rule per cell: Pareto win over the standard (result >= and tokens <=, one strictly).
EPISODE SIZE: T = 6 rounds, horizon = 6 (the whole episode), samples = 6 forks per decision: about 25 rollouts x 6
  samples x <= 6 rounds of pure-python simulation per decision; the quick test runs 4 cells x 2 modes in seconds with
  mock:0 and makes <= 2 x 6 model calls per episode on the laptop (forks never call a model).

REAL2 ADDITIONS (24 Nov, brief A and C)
A. LAW 4 LANDINGS. The budget unit = ONE FACT IN A'S MESSAGE (a message holds at most K = 2 facts).
     landings(st, a)        the facts of A's message
     without(st, a, L)      the message without fact L: L's slot is HELD (the marker HOLD in the action; valid() keeps it
                            and does not fill that slot with the standard's next fact; step() sends nothing for it, so
                            the round costs fewer message tokens and B's answer prompt is shorter)
     targets(st, a, L)      up to 3 of A's other unsent facts, highest need first = the standard's own relevance order
                            from A's state (subject = the person asked about, relevance 2/1/0 from the question and the
                            messages so far, relation word in the question)
     retarget(st, a, L, T)  the message with fact T in L's place (same number of facts)
   The landing test runs in A's own futures (fork: B's unknown values sampled; rule resolver; no model call).
   REAL1's behaviour is unchanged when no HOLD is present (seed_noland and default never produce one).
C. STRONGEST METHOD: the current standard is the strongest available for this channel. The protocol is push-only (A
   sends up to K facts per round; B runs the standard); the standard is a relevance-ranked greedy summary of one's half
   that was already strengthened before any comparison (the asked person's facts first, one-hop chain relevance from the
   question and every message so far, the question's relation words first). A request-driven protocol (B asks for what
   it misses) would change the channel for both agents, not A's policy within it, so it is not a stronger standard of
   this row.

REAL3 ADDITIONS (24 Nov, brief REAL3; seed3.py binding; REAL1/REAL2 modes give identical numbers: none of the actions
below is produced by them, and every new path is keyed on a marker those modes never emit)
FRAME LEVER = HOLOGRAM MESSAGE (layer 2): A sends STRUCTURE, not sentences.
  - compact fact  "rel(subject)=object" (e.g. "manager(Ava)=Ben", 4 tokens vs "The manager of Ava is Ben." 7 tokens): the
    message tokens are counted on the compact text, and the receiver's answer prompt lists a fact received this way in
    the same compact form (the receiver resolves the hops itself; no legend line is added, so nothing hidden is paid).
  - key           "?rel(subject)" = the FRONTIER of A's own chain (the first hop of the question path that A cannot
    resolve from its half + what it received; always a hop B holds). A key names its subject in the message, so under
    the STANDARD's own rule (relevance 2 = subject named in any message exchanged) B's unchanged summariser ranks B's
    facts about that subject first: the receiver computes what to send. A key occupies one message slot.
  - shared trace  the digest sent with a key is only A's UNSENT path hops (never what B holds or already received).
  Frame candidates: holo-std / holo-path / holo-vote (the standard's, the path's, the P8-voted facts as structure),
  holokey (frontier key + A's unsent path hops), holopack (voted, path, then standard facts, token parity).
  Actions: [HOLO, facts..] (K facts, compact), [HOLO, key, facts..] (key + K-1 facts), and [PACK, ...] = compact facts
  packed into the token count of the standard's own sentence message of this round (token parity: the message never
  costs more tokens than the standard's; it may then carry more than K facts). PACK relaxes the "K facts per message"
  count to token parity; disable it with env REAL3_AIAI_PACK=0 (the lead decides whether it is in the sealed run).
  B always runs the standard method and writes sentences; only A's message format/content is the seed's.
PRIMITIVES (map Part I.2 bound to A's message):
  P1 counter-shift   A's unsent path hops nearest the frontier first (the unresolved part pulls the slots)
  P2 price on harm   the standard's facts with every relevance-0 slot HELD (a fact nobody can use only costs tokens)
  P3 part repair     only A's unsent path hops (the missing parts of the chain), the rest of the message held
  P8 vote of futures the K facts most often on the chain across 8 own futures (fork samples of B's unknown values)
  P4P5 joint choice  the PAIR of facts with the highest joint value over the same futures, counted in path order (a hop
                     is worth something only if every earlier A-held hop is covered: value carried back along the chain)
  (P6 and P7 live in seed3 itself: pool ordering and apoptosis.)
COUPLED: True when A holds >= 2 unsent hops of the resolved question path (they only work together; seed3 lands the
  message as a whole, no per-fact landing).
REAL3 v2 (25 Nov; seed operators, real/HOST_INTERFACE_REAL3v2.md; REAL1/REAL2 modes and seed3v1 byte-identical on
  mock cells 1-4). PARTS = the 4 hops of the question path (manager, team, office, city); A's facts belong to the part of
  their relation (mentor / home facts: no part, standard order). merge = per named hop its facts / key first, the
  standard elsewhere, a hologram mark on any named action = a hologram message. part_objective = share of A's 8 own
  futures in which B holds that hop. focus = the message on one hop (focus_<rel>). joint = CHAIN. map_part = the r-th
  fact of hop pf -> the r-th fact of hop pt. shape = (round, path pattern in A's view, frontier key sent). op_of:
  F:holo / F:holokey / F:holopack -> compress, chain -> fuse. CARRY not bound: the channel is K facts per round (fixed
  budget for both agents); carrying a slot would change the channel. No sub-parts (ENTER depth 1). PACK stays off by
  default (REAL3_AIAI_PACK=0); every model call counted in tokens. Model calls bounded (llm_bounded; failed calls
  counted in report()["failed_calls"]).
"""
import os, sys, math, random, itertools
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "experiments", "agents"))

PEOPLE = ["Ava", "Ben", "Cleo", "Dan", "Eli", "Fay", "Gus", "Hana", "Ivo", "Jun", "Kai", "Lena"]
TEAMS = ["Kilo", "Lima", "Oscar", "Romeo", "Sierra", "Tango"]
OFFICES = ["office 1", "office 2", "office 3", "office 4", "office 5", "office 6"]
CITIES = ["Lisbon", "Oslo", "Riga", "Tallinn", "Vienna", "Porto", "Turku", "Ghent"]
RELS = {"manager": (PEOPLE, PEOPLE), "mentor": (PEOPLE, PEOPLE), "team": (PEOPLE, TEAMS), "home": (PEOPLE, CITIES),
        "office": (TEAMS, OFFICES), "city": (OFFICES, CITIES)}
PATH = ["manager", "team", "office", "city"]
K = 2; T = 6
HOLD = ("-", "-")   # REAL2 landing marker: a message slot held (no fact sent in it)
HOLO = ("#", "H")   # REAL3 hologram message: compact facts (+ optional key), K slots
PACK = ("#", "P")   # REAL3 hologram message packed to the standard message's token count
MARKS = (HOLD, HOLO, PACK)
USE_PACK = os.environ.get("REAL3_AIAI_PACK", "0") != "0"
SYSTEM = ("You and a partner each hold half of a set of facts about a company; you exchange a few facts per round. "
          "Answer only if the facts you hold or received fully determine the answer. Reply with exactly one line: "
          "'ANSWER: <city>' or 'CONTINUE'.")

def text(rel, subj, obj):
    return {"manager": f"The manager of {subj} is {obj}.", "mentor": f"The mentor of {subj} is {obj}.",
            "team": f"{subj} works in team {obj}.", "home": f"{subj} lives in {obj}.",
            "office": f"Team {subj} sits in {obj}.", "city": f"{subj.capitalize()} is in {obj}."}[rel]

def ctext(rel, subj, obj): return f"{rel}({subj})={obj}"      # REAL3 compact fact (hologram message)

def ktext(rel, subj): return f"?{rel}({subj})"                  # REAL3 key: the hop A asks the receiver to resolve

def iskey(k): return len(k) == 3 and k[0] == "?"

def tok(s): return int(math.ceil(len(s) / 4))

def resolve(view, x):
    """Rule resolver: follow the 4 hops in a view {(rel, subj): obj}; the answer or None."""
    e = x
    for r in PATH:
        e = view.get((r, e))
        if e is None: return None
    return e

def make_world(cell):
    rng = random.Random(cell * 7919 + 17)
    facts = []
    for rel, (dom, rng_) in RELS.items():
        for sj in dom:
            choices = [o for o in rng_ if o != sj]
            facts.append((rel, sj, rng.choice(choices)))
    rng.shuffle(facts)
    x = rng.choice(PEOPLE); truth = {(r, s): o for r, s, o in facts}
    chain, e = [], x
    for r in PATH: chain.append((r, e)); e = truth[(r, e)]
    answer = e
    while True:
        owner = {(r, s): rng.choice("AB") for r, s, o in facts}
        sides = {owner[k] for k in chain}
        if len(sides) == 2: break
    return facts, owner, x, answer

class AiAi:
    horizon = T; samples = 6

    def __init__(s, models=None):
        m = models or os.environ.get("REAL1_AIAI_MODELS", "mock:0,mock:0")
        m = [x.strip() for x in m.split(",")]; s.models = (m[0], m[1] if len(m) > 1 else m[0])

    # ---- episode ----
    def reset(s, cell):
        facts, owner, x, answer = make_world(cell)
        q = f"In which city is the office of the team of the manager of {x}?"
        return {"t": 0, "cell": cell, "x": x, "answer": answer, "question": q,
                "order": [(r, sj) for r, sj, o in facts],              # the halves' fixed order
                "owner": owner, "val": {(r, sj): o for r, sj, o in facts},   # real values (fork: A's view + samples)
                "sent": {"A": [], "B": []},                            # facts sent so far, in order
                "tokens": 0, "msg_tokens": 0, "calls": 0, "held": 0, "result": 0.0, "answered": None, "over": False,
                "model": False, "log": []}

    def done(s, st): return st["over"] or st["t"] >= T

    def _view(s, st, who):
        other = "B" if who == "A" else "A"
        v = {k: st["val"][k] for k in st["order"] if st["owner"][k] == who}
        for k in st["sent"][other]: v[k] = st["val"][k]
        return v

    def _ctx(s, st):
        ents = {st["x"]}
        for who in "AB":
            for k in st["sent"][who]: ents.add(k[1]); ents.add(st["val"][k])
        for k in st.get("asked", ()): ents.add(k[2])                   # REAL3: a key names its subject in a message
        return ents

    def _ranked(s, st, who):
        own = [k for k in st["order"] if st["owner"][k] == who and k not in st["sent"][who]]
        ctx = s._ctx(st)
        rel2 = {st["val"][k] for k in st["order"] if st["owner"][k] == who and k[1] in ctx}
        qwords = set(st["question"].lower().replace("?", "").split())
        def score(k): return 2 if k[1] in ctx else (1 if k[1] in rel2 else 0)
        def key(k): return (-(k[1] == st["x"]), -score(k), -(k[0] in qwords))
        return sorted(own, key=key), score

    def _standard(s, st, who):
        r, _ = s._ranked(st, who); return r[:K]

    def default(s, st): return [] if s.done(st) else s._standard(st, "A")

    def branches(s, st):
        if s.done(st): return []
        ranked, score = s._ranked(st, "A"); out = []
        rel_best = {}
        for k in ranked:
            if score(k) > 0: rel_best.setdefault(k[0], score(k))
        for rel in sorted(rel_best, key=lambda r: -rel_best[r])[:4]:
            out.append((f"focus_{rel}", [k for k in ranked if k[0] == rel and score(k) > 0][:K]))
        ctx = [k for k in ranked if score(k) == 2][:K]
        if ctx: out.append(("ctx", ctx))
        subj = {k[1]: k for k in ranked}
        chain = []
        for k in ranked:
            if score(k) == 2:
                nxt = subj.get(st["val"][k])
                if nxt is not None and nxt != k: chain = [k, nxt]; break
        if chain: out.append(("chain", chain[:K]))
        return out[:6]

    def valid(s, st, a):
        own = {k for k in st["order"] if st["owner"][k] == "A"} - set(st["sent"]["A"])
        a = [tuple(x) for x in a]
        if any(x in (HOLO, PACK) or iskey(x) for x in a): return s._valid_holo(st, a, own)   # REAL3 only
        hold = min(K, sum(1 for x in a if x == HOLD))   # REAL2: held slots are not refilled
        out = []
        for k in [x for x in a if x != HOLD] + s._standard(st, "A"):   # the action first, then filled up with the
            if k in own and k not in out: out.append(k)                # standard's next facts (no round's budget left
        return out[:K - hold] + [HOLD] * hold                          # unused by a stale or narrow branch: rule 4)

    def _valid_holo(s, st, a, own):
        """REAL3 hologram message: [mark] + keys (<= 1, a hop A lacks) + compact facts + held slots."""
        mark = PACK if PACK in a else HOLO
        hold = min(K, sum(1 for x in a if x == HOLD))
        mineA = {k for k in st["order"] if st["owner"][k] == "A"}
        asked = set(st.get("asked", ())); got = set(st["sent"]["B"])
        keys = [x for x in a if iskey(x) and x not in asked and x[1:] not in mineA and x[1:] not in got][:1]
        facts = []
        for k in [x for x in a if len(x) == 2 and x not in MARKS] + s._standard(st, "A"):
            if k in own and k not in facts: facts.append(k)
        if mark == HOLO:
            keys = keys[:K]; facts = facts[:max(0, K - len(keys) - hold)]
        else:   # token parity with the standard's own sentence message of this round
            budget = sum(tok(text(r, sj, st["val"][(r, sj)])) for r, sj in s._standard(st, "A"))
            used = sum(tok(ktext(*k[1:])) for k in keys)
            if used > budget: keys, used = [], 0
            out = []
            for k in facts:
                c = tok(ctext(k[0], k[1], st["val"][k]))
                if used + c > budget: break
                out.append(k); used += c
            facts = out[:max(0, len(out) - hold)]
        return [mark] + keys + facts + [HOLD] * hold

    # ---- REAL2 A: Law 4 landings (one fact in A's message) ----
    def landings(s, st, a): return [tuple(k) for k in a if tuple(k) not in MARKS]

    def without(s, st, a, L): return [tuple(k) for k in a if tuple(k) != L] + [HOLD]

    def targets(s, st, a, L):
        cur = {tuple(k) for k in a}; ranked, _ = s._ranked(st, "A")
        return [k for k in ranked if k not in cur][:3]

    def retarget(s, st, a, L, T): return [T if tuple(k) == L else tuple(k) for k in a]

    def _answer(s, st, who, spec):
        view = s._view(st, who)
        own = [text(r, sj, view[(r, sj)]) for (r, sj) in st["order"] if st["owner"][(r, sj)] == who]
        other = "B" if who == "A" else "A"
        holo = st.get("holo", ())                                       # REAL3: facts received as structure
        got = [(ctext if (r, sj) in holo else text)(r, sj, st["val"][(r, sj)]) for (r, sj) in st["sent"][other]]
        user = (f"Question: {st['question']}\nYour facts:\n" + "\n".join(own) + "\nFacts received from your partner:\n"
                + ("\n".join(got) if got else "(none yet)") + "\nReply with 'ANSWER: <city>' or 'CONTINUE'.")
        if st["model"] or spec.startswith("mock"):
            a = resolve(view, st["x"]); return a, tok(SYSTEM) + tok(user) + 4
        import llm_bounded as LB
        for k in range(2):   # robust (24 Nov; bounded 25 Nov): log, retry once if worthwhile; failure = no answer (CONTINUE)
            try:
                txt, ti, to = LB.chat(spec, SYSTEM, [{"role": "user", "content": user}], max_tokens=400, temperature=0.0)
                break
            except Exception as e:     # noqa: BLE001
                note = f"[ai_ai {spec} cell {st['cell']} round {st['t']} agent {who} try {k + 1}/2] {type(e).__name__}: {str(e)[:300]}"
                st["errors"] = st.get("errors", []) + [note]; print(note, file=sys.stderr, flush=True)
                if not LB.retry_worthwhile(e): st["failed_calls"] = st.get("failed_calls", 0) + 1; return None, 0
        else:
            st["failed_calls"] = st.get("failed_calls", 0) + 1
            return None, 0
        txt = txt or ""; st["calls"] += 1
        line = [l for l in txt.strip().splitlines() if l.strip().upper().startswith("ANSWER:")]
        a = line[-1].split(":", 1)[1].strip().strip(".").strip() if line else None
        return (a or None), ti + to

    def step(s, st, a):
        n_hold = sum(1 for k in a if tuple(k) == HOLD)
        mark = any(tuple(k) in (HOLO, PACK) for k in a)                # REAL3 hologram message
        keys = [tuple(k) for k in a if iskey(tuple(k))]
        a = [tuple(k) for k in a if tuple(k) not in MARKS and not iskey(tuple(k))]   # held slots send nothing
        st = dict(st); st["sent"] = {"A": list(st["sent"]["A"]) + list(a), "B": list(st["sent"]["B"])}
        st["held"] = st.get("held", 0) + n_hold
        st["log"] = list(st["log"])
        if mark or keys:
            st["holo"] = frozenset(st.get("holo", frozenset()) | (set(a) if mark else set()))
            st["asked"] = tuple(st.get("asked", ())) + tuple(keys)
            st["holo_msgs"] = st.get("holo_msgs", 0) + 1; st["keys_sent"] = st.get("keys_sent", 0) + len(keys)
            mA = sum(tok((ctext if mark else text)(r, sj, st["val"][(r, sj)])) for r, sj in a) + sum(tok(ktext(*k[1:])) for k in keys)
        else:
            mA = sum(tok(text(r, sj, st["val"][(r, sj)])) for r, sj in a)
        b = s._standard(st, "B"); st["sent"]["B"] += b
        mB = sum(tok(text(r, sj, st["val"][(r, sj)])) for r, sj in b)
        st["msg_tokens"] += mA + mB; st["tokens"] += mA + mB
        ansA, tA = s._answer(st, "A", s.models[0]); ansB, tB = s._answer(st, "B", s.models[1])
        st["tokens"] += tA + tB
        ans = ansB if ansB is not None else ansA
        if ans is not None:
            st["over"] = True; st["answered"] = ans
            st["result"] = 1.0 if ans.strip().lower() == st["answer"].lower() else 0.0
        if not st["model"]: st["log"].append((st["t"], [list(k) for k in a], [list(k) for k in b], ansA, ansB))
        st["t"] += 1
        return st

    def fork(s, st, j):
        """A's own model of the receiver: B's unknown values sampled from each relation's domain (fresh generator)."""
        rng = np.random.default_rng([st["cell"], st["t"], j, 7311])
        f = dict(st); f["model"] = True; f["sent"] = {"A": list(st["sent"]["A"]), "B": list(st["sent"]["B"])}
        known = set(st["sent"]["B"]); val = {}
        for k in st["order"]:
            if st["owner"][k] == "A" or k in known: val[k] = st["val"][k]
            else:
                dom = [o for o in RELS[k[0]][1] if o != k[1]]; val[k] = dom[int(rng.integers(len(dom)))]
        f["val"] = val; f["answer"] = resolve(val, st["x"]); f["log"] = []
        return f

    # ---- REAL3: primitives, frame levers, coupling (seed3.py) ----
    def _path(s, st, val=None):
        """The question path in A's view (own half + received; or a sampled full world `val`): resolved hops, frontier."""
        view = s._view(st, "A") if val is None else val
        e, hops = st["x"], []
        for r in PATH:
            k = (r, e)
            if k not in view: return hops, k
            hops.append(k); e = view[k]
        return hops, None

    def _mine(s, st, keys):
        return [k for k in keys if st["owner"][k] == "A" and k not in st["sent"]["A"]]

    def _votes(s, st):
        """P8 / P4P5: A's unsent chain hops in each of the own futures (fork samples, never the real half)."""
        out = []
        for j in range(max(8, s.samples)):
            f = s.fork(st, j); hops, _ = s._path(st, f["val"]); out.append(s._mine(st, hops))
        return out

    def coupled(s, st):
        return not s.done(st) and len(s._mine(st, s._path(st)[0])) >= 2

    def primitives(s, st):
        if s.done(st): return []
        ranked, score = s._ranked(st, "A"); std = s._standard(st, "A")
        mine = s._mine(st, s._path(st)[0]); out = []
        if mine:
            out.append(("P1", "P1-frontier", list(reversed(mine))[:K]))
            out.append(("P3", "P3-repair", mine[:K] + [HOLD] * max(0, K - len(mine))))
        p2 = [k if score(k) > 0 else HOLD for k in std]
        if p2 != std: out.append(("P2", "P2-price", p2))
        fut = s._votes(st); votes = {}
        for hops in fut:
            for k in hops: votes[k] = votes.get(k, 0) + 1
        order = {k: i for i, k in enumerate(ranked)}
        vk = sorted(votes, key=lambda k: (-votes[k], order.get(k, 99)))
        if vk: out.append(("P8", "P8-vote", vk[:K]))
        pool = list(dict.fromkeys(vk[:6] + ranked[:4]))
        def joint(pair):
            v = 0
            for hops in fut:
                for k in hops:
                    if k not in pair: break
                    v += 1
            return v
        if len(pool) >= 2:
            best = max(itertools.combinations(pool, 2), key=lambda p: (joint(p), -order.get(p[0], 99) - order.get(p[1], 99)))
            if joint(best) > 0: out.append(("P4P5", "P4P5-joint", list(best)))
        return out

    def frame(s, st):
        if s.done(st): return []
        std = s._standard(st, "A"); hops, front = s._path(st); mine = s._mine(st, hops)
        out = [("F:holo", "F:holo-std", [HOLO] + std)]
        if mine: out.append(("F:holo", "F:holo-path", [HOLO] + mine[:K]))
        votes = {}
        for hops in s._votes(st):
            for k in hops: votes[k] = votes.get(k, 0) + 1
        order = {k: i for i, k in enumerate(s._ranked(st, "A")[0])}
        vk = sorted(votes, key=lambda k: (-votes[k], order.get(k, 99)))
        if vk: out.append(("F:holo", "F:holo-vote", [HOLO] + vk[:K]))
        if front is not None and st["owner"][front] == "B" and ("?",) + front not in st.get("asked", ()):
            out.append(("F:holokey", "F:holokey", [HOLO, ("?",) + front] + mine))
        if USE_PACK: out.append(("F:holopack", "F:holopack", [PACK] + vk + mine + std))
        return out

    # ---- REAL3 v2: seed operator hooks (real/HOST_INTERFACE_REAL3v2.md) ----
    # PARTS = the hops of the question path (manager, team, office, city): a fact of A's belongs to the part of its
    # relation; facts of other relations (mentor, home) belong to no part (they take the standard's order). The step's
    # resource = the K message slots of A's message. Every hook reads A's knowledge only (own half, the question, the
    # messages, the own futures of fork()).
    def parts(s, st): return list(PATH)

    def _split(s, a):
        a = [tuple(x) for x in a]
        return ([x for x in a if x in (HOLO, PACK)], [x for x in a if iskey(x)], [x for x in a if x == HOLD],
                [x for x in a if len(x) == 2 and x not in MARKS])

    def merge(s, st, d):
        """A's message: per named part (dict order) the facts / key of its action on that relation first, then the
        standard's facts on the parts not named (valid() fills to K). A hologram mark on any named action makes the
        whole message a hologram message (the format is the message's); held slots of a named action are kept."""
        marks, keys, holds, facts = [], [], [], []
        named = set(d)
        for rel, a in d.items():
            m, k, h, f = s._split(a or [])
            marks += m; holds += h
            keys += [x for x in k if x[1] == rel]; facts += [x for x in f if x[0] == rel]
        facts += [x for x in s._standard(st, "A") if x[0] not in named]
        mark = [PACK] if PACK in marks else ([HOLO] if marks or keys else [])
        return mark + keys[:1] + list(dict.fromkeys(facts)) + holds[:K]

    def part_objective(s, st, rel):
        """The hop's own value now: the share of A's own futures (8 forks, B's unknown values sampled) in which the
        receiver B holds this hop of the question path (B's own fact or sent by A). Higher = the receiver can resolve it."""
        key = (st["cell"], st["t"], tuple(st["sent"]["A"]), tuple(st["sent"]["B"]), tuple(st.get("asked", ())))
        c = s.__dict__.setdefault("_po", {})
        if key not in c:
            have = {r: 0 for r in PATH}; n = max(8, s.samples)
            for j in range(n):
                f = s.fork(st, j); e = st["x"]
                for r in PATH:
                    k = (r, e)
                    if st["owner"][k] == "B" or k in st["sent"]["A"]: have[r] += 1
                    e = f["val"][k]
            c[key] = {r: v / n for r, v in have.items()}
        return c[key][rel]

    def focus(s, st, rel):
        """The whole message on one hop: A's unsent facts of that relation in the standard's relevance order."""
        if s.done(st): return []
        ranked, _ = s._ranked(st, "A")
        return [k for k in ranked if k[0] == rel][:K]

    def joint(s, st):
        """Native joint action: CHAIN (A's own linked facts sent together, the coupled branch)."""
        return [(n, a) for n, a in s.branches(st) if n == "chain"]

    def map_part(s, st, a, pf, pt):
        """a's pattern on hop pf re-expressed on hop pt: the r-th ranked unsent fact of relation pf -> the r-th ranked
        unsent fact of relation pt (same message format); a key on pf -> a key on pt only if it is A's frontier hop."""
        ranked, _ = s._ranked(st, "A"); rf = [k for k in ranked if k[0] == pf]; rt = [k for k in ranked if k[0] == pt]
        m, keys, h, f = s._split(a or [])
        out = [rt[rf.index(x)] for x in f if x in rf and rf.index(x) < len(rt)]
        _, front = s._path(st)
        kk = [("?",) + front for x in keys if x[1] == pf and front is not None and front[0] == pt and st["owner"][front] == "B"]
        return m + kk[:1] + out

    def shape(s, st):
        """Compact state key: round, the path pattern in A's view (per hop: a = A's unsent, s = sent by A, r = received,
        b = B's known by key / ownership, ? = beyond A's frontier), A's number of unsent path hops."""
        view = s._view(st, "A"); e = st["x"]; pat = ""
        for r in PATH:
            k = (r, e)
            if k not in view: pat += "?" * (len(PATH) - len(pat)); break
            pat += ("s" if k in st["sent"]["A"] else "a") if st["owner"][k] == "A" else "r"
            e = view[k]
        front = s._path(st)[1]
        return (st["t"], pat, bool(front) and (("?",) + front) in st.get("asked", ()))

    OPS_OF = {"F:holo": "compress", "F:holokey": "compress", "F:holopack": "compress", "chain": "fuse"}

    def op_of(s, fam):
        """Hologram message / key / pack (structure, the receiver computes) = COMPRESS; chain (coupled facts) = FUSE;
        focus_<rel> -> beam and P1..P8 via the seed's table."""
        return s.OPS_OF.get(fam)

    def objective(s, st): return (st["result"], -float(st["tokens"]))   # free-resource row (14:15)

    def report(s, st):
        return {"result": st["result"], "resource": float(st["tokens"]), "rounds": st["t"], "msg_tokens": st["msg_tokens"],
                "answered": st["answered"], "truth": st["answer"], "models": list(s.models), "model_calls": st["calls"],
                "held_slots": st.get("held", 0), "errors": list(st.get("errors", [])),
                "holo_msgs": st.get("holo_msgs", 0), "keys_sent": st.get("keys_sent", 0),
                "failed_calls": st.get("failed_calls", 0)}
