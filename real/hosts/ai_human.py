"""REAL1 row 3 "ai_human": AI-human communication on real human dialogue data (a PROXY: no live humans).
FREE-RESOURCE row (brief rule 4, 14:15): pass per cell = Pareto: coverage >= standard AND tokens <= standard, one strictly.

HOST
  Data: Topical-Chat (Amazon Alexa AI 2019), conversations/test_freq.json, 539 real human-human conversations, fetched from
  GitHub by ai_human_fetch.py (sha256 checked; reachable here and on the laptop, so no stand-in data is needed).
  Conversations are taken in sorted-id order; cell c = conversation number c (development cells 1..8; the confirmatory
  cells are fixed by the lead in the seal). agent_1 is "the human"; the model replaces agent_2.
  Episode = the first 8 positions i where agent_1 speaks (h_t), agent_2 replies (r*_t, the real human reply) and agent_1
  speaks again (h_t+1). At each step the model writes ONE reply to h_t from the real history up to h_t (the last 6 turns;
  teacher forcing: the real r*_t, not the model's reply, stays in the history, because the real h_t+1 answered r*_t).
  Units = the points the reply can address: the sentences (or clauses) of h_t (at most 5) and at most one carried point
  (the longest sentence of h_t-1 that the real reply r*_t-1 left uncovered: past data). The words of the units are the
  candidate needs of the next human turn.

ACTIONS (revised 24 Nov, owner's two structural lessons)
  ("direct",)            the standard reply: system prompt SYS, unchanged.
  ("mention", w1, ...)   the reply is asked to cover chosen words of the units: the system prompt is SYS with its first
                         sentence (the persona line "You are chatting with ... facts.") REPLACED by the slot
                         " Mention: w1, w2." at the end. Branches change WHAT the reply covers inside the same prompt
                         length; they add no instruction on top of the standard prompt.
  Focused branches: the top words of one unit (the 4 units with the largest expected need mass). Coupled: the top words
  over all units ("top"), and the question point linked with the carried point ("link") when both exist.

TOKEN PARITY (lesson 1; a construction, not an estimate)
  Every branch prompt = the same history + a system string S_b with count(S_b) <= count(SYS) for EVERY token counter
  available: the model's own tokenizer (llama-3.x: the Llama 3 tiktoken BPE shipped in the `llama-models` package;
  Mistral: the Tekken BPE shipped in `mistral-common`), and the chars/4 counter of the mock. The slot words are added
  greedily (highest need probability first) only while the inequality holds; a word that does not fit is dropped; an
  action with no word left is the direct reply. The chat template wraps the system string between special tokens, so
  the prompt's input tokens satisfy tin(branch) <= tin(standard) for the same history. The output cap is the same for
  every action (48 tokens, "at most 25 words"). A real run with a llama or mistral model REQUIRES its tokenizer
  (pip install tiktoken llama-models mistral-common); without it the host stops instead of guessing.
  report()["parity_max"] = max over the episode of count(S_b) - count(SYS) under the model's counter (always <= 0).
  The output tokens are the model's; they are measured, not bounded (same cap and word limit as the standard).

RESULT (FIXED SCORING RULE, a proxy; written 24 Nov 2026 before any run; unchanged)
  content(x) = lowercase alphabetic tokens of x, length >= 3, not in STOP (below), with a trailing "s" removed from
  words longer than 4 letters (not "ss").
  needs_t = content(h_t+1) & (content(h_t) | content(r*_t)); coverage_t = |needs_t & content(reply_t)| / |needs_t|; a turn
  with empty needs_t is not scored. result = mean coverage over the scored turns. Resource = kilotokens of the reply
  calls (input + output).
  objective(state) = (mean coverage, -tokens), lexicographic (lesson 1: the value matches the row's Pareto rule): observed
  coverage of past replies and the model's EXPECTED coverage of the current reply; then fewer tokens.

THE HOST'S OWN MODEL (fork; layer-1 rule: only data up to h_t, never r*_t or h_t+1) = the REAL TREE (lesson 2)
  Need probability of each candidate word w (ai_human_tree.py): counted on the 8628 real human-human conversations of the
  Topical-Chat TRAINING split (never the test conversations): P(w in h_t+1 | bucket of w in h_t) combined with w's own
  lexical carry rate; carried-point words use the corpus rate for such words. Then calibrated on THIS conversation's own
  real past (every real triple h_s, r_s, h_s+2 before h_t): factor (observed carries + 3) / (corpus-predicted + 3).
  Unknown needs (words the real partner will bring in, which no plan can cover): corpus mean, updated by this
  conversation's past (weight 2).
  What the reply covers: a word in the slot with rate e_dir (prior 0.8 with weight 4, then the model's own past slot
  words in this episode); a word not in the slot with the corpus rate at which a real human partner's reply covers a
  word of that bucket, times the factor (echoed + 4) / (expected + 4) measured on the model's own past replies of the
  same kind (direct / mention; mention falls back to direct with no data).
  The tree, not a single sample: each fork j draws D = 64 futures (needs, unknown needs, echo) with common random
  numbers for every action and stores the EXPECTED coverage over them; the seed averages 8 forks (512 futures per
  branch). Predicted tokens = history + count(system of the action) + the mean of the model's own past reply lengths
  (prior 30), so a branch's predicted tokens never exceed the standard's. Randomness: default_rng([cell, t, j, 4451]).
  Horizon 1, 8 samples.

MOCK (`mock:0`, the interface check here; STAND-IN, never for results): the reply is the slot words, then the units' text
  in order, cut to 20 words (an echo model); tokens = characters / 4 (and the parity check also holds under the real
  tokenizers if installed). The data are real; only the model is a stand-in.

SIZE (rule 5): 8 replies per episode, horizon 1, 8 samples x 64 draws; the quick test (mock) runs in seconds after the
  one-time tree build (~20 s, cached in data/topical_chat/tree_stats.json); on the laptop it is 8 short calls per cell and
  mode (~5k tokens).
Laptop models: openrouter:meta-llama/llama-3.1-8b-instruct (main), openrouter:mistralai/mistral-small-3.2-24b-instruct
  (second). Avoid reasoning models here (gpt-oss): hidden reasoning would consume the 48-token reply budget.

REAL2 ADDITIONS (24 Nov, brief A and C)
A. LAW 4 LANDINGS. The budget unit = ONE MENTION WORD IN THE SLOT (the direct reply has no slot and no landings).
     landings(st, a)        the slot words of a mention action
     without(st, a, w)      the slot without w (a shorter system string, fewer input tokens); no word left = the direct
                            reply (valid())
     targets(st, a, w)      up to 3 candidate need words not in the slot, highest need first (P(w in the next human turn)
                            from the real tree, calibrated on this conversation's own past: data up to h_t only), kept
                            only if the slot with the substitute still passes the token-parity check (same slot size)
     retarget(st, a, w, T)  the slot with T in w's place (valid() re-checks token parity under every counter)
   The landing test runs in the same own futures (the 8 forks x 64 draws of the tree): no extra model call.
C. STRONGEST METHOD: the current standard is the strongest available under this row's constraints. It is the model's
   own direct reply with the standard prompt (one call, the same 48-token output cap). Stronger reply methods in the
   literature either spend more tokens per turn (sample-and-rerank, plan-then-write: several calls) or need data that
   the human turn does not carry (knowledge-grounded replies on the Topical-Chat reading sets); both break the row's
   token Pareto rule or its data rule, so the direct reply is the standard and the membrane bound.
ROBUSTNESS (24 Nov): the reply call is made through _chat: exception text logged (stderr and report()["errors"]),
  one retry; a second failure gives an empty reply (0 tokens, the turn's coverage 0 if scored) and the episode goes on.
  A reply with no usage gets a chars/4 estimate (report()["usage_estimated"]).

REAL3 ADDITIONS (24 Nov, brief REAL3; seed3.py binding; REAL1/REAL2 modes give identical numbers: they never produce
the new action kinds, and the direct / mention paths are untouched)
FRAME LEVER = HOLOGRAM REPLY. The standard prompt carries the TRANSCRIPT (SYS + the last 6 turns). The hologram prompt
  carries the conversation's WHOLE STATE compactly instead:
    sees   the human's last turn h_t, verbatim (the only message)
    hears  "You said: ..." = content words of the partner's last turn r*_t-1 (data up to h_t) not in h_t (<= 4)
    topic  "Topic: ..."    = content words said in >= 2 turns of the dropped window, not in h_t (<= 4)
    needs  "Mention: ..."  = need words from the REAL TREE (calibrated P, as the mention slot)
  system = CORE + those sections; action ("holo", w1, ...) (full digest) or ("holomin", w1, ...) (needs only).
  TOKEN PARITY STAYS (construction): the whole hologram prompt <= the whole standard prompt of the same turn under EVERY
  counter, both as the sum of the parts and as the concatenated text; words are added greedily (needs first, then
  hears, then topic) only while that holds. Output cap and word limit unchanged. report()["parity_max"] for a hologram
  turn = count(hologram prompt) - count(standard prompt) (whole prompt; always <= 0).
  READY GATE (the receiver can take the whole from the hologram; checked in valid(), so also in every own future):
    (1) h_t carries >= READY_MIN content words (a short turn leans on the dropped transcript), and
    (2) every carried-point word (from h_t-1, which the hologram drops) with need P >= READY_P is in the prompt.
  Not READY -> the same words as the standard-parity mention action (or the direct reply).
  Own model: a hologram turn is predicted like a mention turn (slot words at e_dir, the rest at the free-echo rate times
  the kind's factor, measured on the model's own past hologram replies, falling back to mention then direct), with the
  hologram prompt's token count.
PRIMITIVES (map Part I.2 bound to the reply slot; standard parity):
  P1 counter-shift   carried-point words first (the part the last real reply left uncovered pulls the slot), then top
  P2 price on harm   words the human has repeated (said before h_t: the need persists) first, then top
  P3 part repair     the question point's words only
  P8 vote of futures only words that are needs in the majority of the own futures (P >= 0.5)
  P4P5 joint choice  slot ordered by expected gain P(w) * (e_dir - free echo of w): value carried back per word
COUPLED: True when the turn has a question point and a carried point (the link branch exists): the reply answers both
  as one whole, no per-word landing.
REAL3 v2 (25 Nov; seed operators, real/HOST_INTERFACE_REAL3v2.md; REAL1/REAL2 modes and seed3v1 byte-identical on
  mock cells 1-4). PARTS = the points of the human turn (units), sub-parts = each point's need words (ENTER depth 2).
  merge = per named point the words its action puts there (dict order), nothing elsewhere (the standard is the direct
  reply), a hologram kind on any named action = a hologram prompt; token parity by valid(). part_objective = expected
  share of the point's need words the STANDARD reply covers (own model). focus = the slot on one point (unit-k).
  joint = LINK / TOP. map_part = r-th word of pf -> r-th word of pt. shape = (points, question, carried, READY length,
  first turn). op_of: F:holo / F:holomin -> compress, unit -> beam, top / link -> fuse. CARRY not bound: parity is per
  turn (the construction), a carried token budget would break it. Model calls bounded (llm_bounded)."""
import os, sys, re, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AG = os.path.abspath(os.path.join(HERE, "..", "..", "experiments", "agents"))
if AG not in sys.path: sys.path.insert(0, AG)
if HERE not in sys.path: sys.path.insert(0, HERE)
import llm                                     # noqa: E402  (keys from environment only)
from ai_human_fetch import fetch               # noqa: E402
import ai_human_tree                           # noqa: E402
import llm_bounded as LB                       # noqa: E402  (REAL3 v2: bounded calls)

REPLY_TOK, REPLY_WORDS, MODEL_WORDS, MAX_TURNS, HISTORY = 48, 25, 20, 8, 6
DRAWS, E_DIR, E_DIR_W, CAL_W, ECHO_W, OUT_PRIOR = 64, 0.8, 4.0, 3.0, 4.0, 30.0
STOP = set("""the and for are but not you your yours all any can had has have her him his how its our out who what when where
why which that this these those they them their there then than with from into onto about over under again also just like
very really much many more most some such only own same too was were been being did does doing done would could should will
shall may might must one two yes yeah yep nope okay well know think thought thing things get got going gone make made see
said say says lot lots good great nice cool wow fun interesting pretty actually probably maybe sure right guess mean
something anything everything nothing someone anyone everyone way ever never always still even because while though
let let's i'm it's that's don't didn't doesn't isn't wasn't aren't can't won't you're they're i've i'd i'll we're what's
there's who's heard hear did know knew want wanted love loved hope""".split())
PERSONA = "You are chatting with another person about interesting topics and facts."
CORE = f"Reply naturally and briefly to their last message, in at most {REPLY_WORDS} words."
SYS = f"{PERSONA} {CORE}"                                   # the standard prompt (unchanged)
READY_MIN, READY_P, DIGEST_N = 3, 0.3, 4                    # REAL3 READY gate and digest size
HOLO_KINDS = ("holo", "holomin")

def content(x):
    out = set()
    for w in re.findall(r"[a-z']+", str(x).lower()):
        w = w.strip("'")
        if w.endswith("'s"): w = w[:-2]
        if len(w) < 3 or w in STOP: continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"): w = w[:-1]
        out.add(w)
    return out

def sentences(x): return [p.strip() for p in re.split(r"(?<=[.?!])\s+", str(x).strip()) if p.strip()]

def points_of(text):
    ps = [p for p in sentences(text) if content(p)]
    if len(ps) == 1 and len(content(ps[0])) >= 6:
        parts = [c.strip() for c in re.split(r",\s+|\s+(?:but|and|so)\s+", ps[0]) if len(content(c)) >= 2]
        if len(parts) >= 2: ps = parts
    return ps[:5]

def clip(x, n=REPLY_WORDS): w = str(x).split(); return " ".join(w[:n])

def ntok(x): return int(math.ceil(len(x) / 4))

def surfaces(text):
    """content word -> its first surface form in text (what the slot quotes)."""
    out = {}
    for raw in re.findall(r"[A-Za-z][A-Za-z']*", str(text)):
        c = content(raw)
        if len(c) == 1:
            w = next(iter(c)); out.setdefault(w, raw[:-2] if raw.lower().endswith("'s") else raw.strip("'"))
    return out

def slot_system(words): return f"{CORE} Mention: {', '.join(words)}."


# ---------- token counters (lesson 1: parity by construction) ----------
_TOK = {}

def _llama3():
    if "llama3" not in _TOK:
        import tiktoken, llama_models
        from tiktoken.load import load_tiktoken_bpe
        pat = r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
        ranks = load_tiktoken_bpe(os.path.join(os.path.dirname(llama_models.__file__), "llama3", "tokenizer.model"))
        enc = tiktoken.Encoding("llama3", pat_str=pat, mergeable_ranks=ranks, special_tokens={})
        _TOK["llama3"] = lambda x: len(enc.encode(x, disallowed_special=()))
    return _TOK["llama3"]

def _tekken():
    if "tekken" not in _TOK:
        import mistral_common
        from mistral_common.tokens.tokenizers.tekken import Tekkenizer
        tk = Tekkenizer.from_file(os.path.join(os.path.dirname(mistral_common.__file__), "data", "tekken_240911.json"))
        _TOK["tekken"] = lambda x: len(tk.encode(x, bos=False, eos=False))
    return _TOK["tekken"]

def counters(spec):
    """(primary counter, all counters). Real llama / mistral runs require their own tokenizer."""
    mock = spec.startswith("mock"); cs = {"chars/4": ntok}
    for name, load in (("llama3", _llama3), ("tekken", _tekken)):
        need = (name == "llama3" and "llama" in spec.lower()) or (name == "tekken" and "mistral" in spec.lower())
        try: cs[name] = load()
        except Exception as e:
            if need and not mock:
                raise RuntimeError(f"token parity needs the {name} tokenizer: pip install tiktoken llama-models mistral-common ({e})")
    prim = "chars/4" if mock else ("llama3" if "llama" in spec.lower() else ("tekken" if "mistral" in spec.lower() else
                                   ("llama3" if "llama3" in cs else "chars/4")))
    return cs[prim], cs


class AIHuman:
    horizon = 1
    samples = 8

    def __init__(s, spec="mock:0"):
        s.spec = spec; s.mock = spec.startswith("mock")
        d = json.load(open(fetch(quiet=True))); s.keys = sorted(d); s.data = d
        s.count, s.counters = counters(spec)
        s.sys_n = {k: c(SYS) for k, c in s.counters.items()}
        s.tree = ai_human_tree.load(content, sentences)
        s._cache = {}

    # ---------- episode ----------
    def reset(s, cell):
        conv = [(m["agent"], m["message"]) for m in s.data[s.keys[cell]]["content"]]
        pos = [i for i in range(len(conv) - 2) if conv[i][0] == "agent_1" and conv[i + 1][0] == "agent_2" and conv[i + 2][0] == "agent_1"]
        return {"sim": False, "cell": cell, "t": 0, "conv": conv, "pos": pos[:MAX_TURNS], "cov": [], "tok": 0, "reply_tok": 0,
                "in_tok": 0, "replies": [], "log": [], "parity": [], "mentions": 0, "errors": [], "usage_est": 0}

    def done(s, st): return st["t"] >= len(st["pos"]) or (st["sim"] and st["t"] > st["t0"])

    def _points(s, conv, i):
        """Units at position i, from data up to h_t only: points of h_t, plus one carried point of h_t-1."""
        pts = [(p, "now") for p in points_of(conv[i][1])]
        if i >= 2 and conv[i - 2][0] == "agent_1" and conv[i - 1][0] == "agent_2":
            reply_prev, now = content(conv[i - 1][1]), content(conv[i][1])
            cand = [p for p in sentences(conv[i - 2][1]) if len(content(p)) >= 2 and not (content(p) & (reply_prev | now))]
            if cand: pts.append((max(cand, key=lambda p: len(content(p))), "carried"))
        return pts

    def _units(s, cell, conv, i):
        """Candidate need words at h_t (data up to h_t): {w: (bucket key, corpus need prob)}, surfaces, points, the
        conversation calibration and unknown-need mean from its own real past."""
        key = (cell, i)
        if key in s._cache: return s._cache[key]
        conv = conv[: i + 1]; pts = s._points(conv, i)
        feats = ai_human_tree.word_feats(conv, i, content, sentences)
        W = {w: (k, s.tree.p_need(w, k)) for w, k in feats.items()}
        surf = surfaces(conv[i][1])
        for p, kind in pts:
            if kind == "carried":
                for w, sf in surfaces(p).items():
                    if w not in W: W[w] = ("carried", s.tree.p_need(w, "carried")); surf.setdefault(w, sf)
        obs = pred = 0.0; unk = []                           # this conversation's own real past (h_s, r_s, h_s+2), s+2 <= i
        for p in range(0, i - 1):
            if not (conv[p][0] == conv[p + 2][0] != conv[p + 1][0]): continue
            h, r, h2 = content(conv[p][1]), content(conv[p + 1][1]), content(conv[p + 2][1])
            for w, k in ai_human_tree.word_feats(conv, p, content, sentences).items():
                obs += w in h2; pred += s.tree.p_need(w, k)
            unk.append(len((h2 & r) - h))
        cal = (obs + CAL_W) / (pred + CAL_W)
        m = (sum(unk) + 2 * s.tree.unknown_mean) / (len(unk) + 2)
        P = {w: min(0.97, pw * cal) for w, (_, pw) in W.items()}
        out = {"W": W, "P": P, "surf": surf, "pts": pts, "m": m, "cal": cal}
        s._cache[key] = out; return out

    # ---------- standard method and branches ----------
    def default(s, st): return ("direct",)

    def _fit(s, words, surf):
        """Greedy slot: keep a word only while count(S_b) <= count(SYS) under every counter (token parity)."""
        kept = []
        for w in words:
            if w in kept or w not in surf: continue
            trial = slot_system([surf[x] for x in kept + [w]])
            if all(c(trial) <= s.sys_n[k] for k, c in s.counters.items()): kept.append(w)
        return kept

    def _u(s, st):
        if st["sim"]: return st["u"]
        return s._units(st["cell"], st["conv"], st["pos"][st["t"]])

    def branches(s, st):
        u = s._u(st); P, pts = u["P"], u["pts"]; out = []
        ranked = lambda ws: sorted((w for w in ws if w in P), key=lambda w: (-P[w], w))
        unit_words = [(k, ranked(content(p)), kind) for k, (p, kind) in enumerate(pts)]
        unit_words = [x for x in unit_words if x[1]]
        for k, ws, kind in sorted(unit_words, key=lambda x: -sum(P[w] for w in x[1]))[:4]:
            out.append((f"unit-{k}" + ("c" if kind == "carried" else ""), ("mention",) + tuple(ws)))
        out.append(("top", ("mention",) + tuple(ranked(P))))
        q = [ws for k, ws, kind in unit_words if kind == "now" and pts[k][0].rstrip().endswith("?")]
        c = [ws for k, ws, kind in unit_words if kind == "carried"]
        if q and c: out.append(("link", ("mention", q[-1][0], c[0][0])))
        seen, res = set(), []
        for name, a in out:
            v = s.valid(st, a)
            if v[0] == "mention" and v not in seen: seen.add(v); res.append((name, v))
        return res[:6]

    def valid(s, st, a):
        a = tuple(a) if a else ("direct",)
        if st["t"] < len(st["pos"]) and a[0] in HOLO_KINDS: return s._valid_holo(st, a)   # REAL3 only
        if st["t"] >= len(st["pos"]) or a[0] != "mention": return ("direct",)
        u = s._u(st); kept = s._fit([w for w in a[1:] if w in u["P"]], u["surf"])
        return ("mention",) + tuple(kept) if kept else ("direct",)

    def _system(s, u, a): return SYS if a[0] == "direct" else slot_system([u["surf"][w] for w in a[1:]])

    # ---------- REAL3: hologram reply, READY gate, primitives, frame, coupling ----------
    def _i(s, st): return st["pos"][st["t"]]

    def _digest(s, conv, i):
        """hears (partner's last turn) and topic (words in >= 2 dropped turns), data up to h_t only."""
        now = content(conv[i][1]); hears, topic = [], []
        if i >= 1 and conv[i - 1][0] == "agent_2":
            hears = [sf for w, sf in surfaces(conv[i - 1][1]).items() if w not in now][:DIGEST_N]
        cnt, surf = {}, {}
        for _, m in conv[max(0, i - HISTORY + 1): i]:
            for w in content(m): cnt[w] = cnt.get(w, 0) + 1
            for w, sf in surfaces(m).items(): surf.setdefault(w, sf)
        hs = {content(h).pop() for h in hears if content(h)}
        topic = [surf[w] for w in sorted(cnt, key=lambda w: (-cnt[w], w)) if cnt[w] >= 2 and w not in now and w not in hs and w in surf][:DIGEST_N]
        return hears, topic

    @staticmethod
    def _holo_system(topic, hears, words):
        x = CORE
        if topic: x += f" Topic: {', '.join(topic)}."
        if hears: x += f" You said: {', '.join(hears)}."
        if words: x += f" Mention: {', '.join(words)}."
        return x

    def _plen(s, c, system, msgs):
        return c(system) + sum(c(m["content"]) for m in msgs), c(system + "".join(m["content"] for m in msgs))

    def _holo_prompt(s, st_or_f, a):
        """(system, messages, kept words) of a hologram action, built greedily under whole-prompt token parity."""
        conv, i, u = st_or_f["conv"], s._i(st_or_f), s._u(st_or_f)
        std_msgs = s._history(conv, i); msgs = [{"role": "user", "content": conv[i][1]}]
        lim = {k: s._plen(c, SYS, std_msgs) for k, c in s.counters.items()}
        fits = lambda sysx: all(all(x <= y for x, y in zip(s._plen(c, sysx, msgs), lim[k])) for k, c in s.counters.items())
        hears_all, topic_all = s._digest(conv, i) if a[0] == "holo" else ([], [])
        words, hears, topic = [], [], []
        for w in a[1:]:
            if w in u["surf"] and w not in words and fits(s._holo_system([], [], [u["surf"][x] for x in words + [w]])): words.append(w)
        sw = [u["surf"][x] for x in words]
        for h in hears_all:
            if fits(s._holo_system([], hears + [h], sw)): hears.append(h)
        for t in topic_all:
            if fits(s._holo_system(topic + [t], hears, sw)): topic.append(t)
        system = s._holo_system(topic, hears, sw)
        if not fits(system): return None, None, []
        return system, msgs, words

    def _ready(s, st, system, msgs):
        u = s._u(st); i = s._i(st)
        if len(content(st["conv"][i][1])) < READY_MIN: return False
        have = content(system + " " + msgs[0]["content"])
        return all(w in have for w, (k, _) in u["W"].items() if k == "carried" and u["P"][w] >= READY_P)

    def _valid_holo(s, st, a):
        u = s._u(st); a = (a[0],) + tuple(w for w in a[1:] if w in u["P"])
        system, msgs, words = s._holo_prompt(st, a)
        if system is not None and s._ready(st, system, msgs): return (a[0],) + tuple(words)
        return s.valid(st, ("mention",) + a[1:])                          # not READY: the standard-parity slot

    def _prompt(s, st_or_f, a):
        if a[0] in HOLO_KINDS: return s._holo_prompt(st_or_f, a)[:2]
        return s._system(s._u(st_or_f), a), s._history(st_or_f["conv"], s._i(st_or_f))

    def coupled(s, st):
        if s.done(st): return False
        return any(n == "link" for n, _ in s.branches(st))

    def primitives(s, st):
        if s.done(st): return []
        u = s._u(st); P, pts = u["P"], u["pts"]
        rk = sorted((w for w in P if w in u["surf"]), key=lambda w: (-P[w], w)); out = []
        car = [w for w in rk if u["W"][w][0] == "carried"]
        if car: out.append(("P1", "P1-carried", ("mention",) + tuple(car + [w for w in rk if w not in car])))
        rep_ = [w for w in rk if u["W"][w][0] != "carried" and u["W"][w][0][2] == "1"]
        if rep_: out.append(("P2", "P2-persist", ("mention",) + tuple(rep_ + [w for w in rk if w not in rep_])))
        q = [content(p) for p, kind in pts if kind == "now" and p.rstrip().endswith("?")]
        if q: out.append(("P3", "P3-question", ("mention",) + tuple(w for w in rk if w in q[-1])))
        maj = [w for w in rk if P[w] >= 0.5]
        if maj: out.append(("P8", "P8-majority", ("mention",) + tuple(maj)))
        e_dir, fac, _ = s._echo_rates(st["log"])
        gain = lambda w: P[w] * (e_dir - min(0.97, s.tree.p_echo(u["W"][w][0]) * fac["mention"]))
        out.append(("P4P5", "P4P5-gain", ("mention",) + tuple(sorted(rk, key=lambda w: (-gain(w), w)))))
        res, seen = [], set()
        for fam, name, a in out:
            v = s.valid(st, a)
            if v[0] == "mention" and v not in seen: seen.add(v); res.append((fam, name, v))
        return res

    def frame(s, st):
        if s.done(st): return []
        u = s._u(st); P = u["P"]
        rk = tuple(sorted((w for w in P if w in u["surf"]), key=lambda w: (-P[w], w)))
        maj = tuple(w for w in rk if P[w] >= 0.5)
        out = [("F:holo", "F:holo-top", ("holo",) + rk[:6]), ("F:holo", "F:holo-maj", ("holo",) + maj),
               ("F:holomin", "F:holomin-top", ("holomin",) + rk[:6])]
        res, seen = [], set()
        for fam, name, a in out:
            v = s.valid(st, a)
            if v[0] in HOLO_KINDS and v not in seen: seen.add(v); res.append((fam, name, v))
        return res

    # ---------- REAL3 v2: seed operator hooks (real/HOST_INTERFACE_REAL3v2.md) ----------
    # PARTS = the points of the human turn (the units: sentences / clauses of h_t and the carried point of h_t-1), part id
    # ("pt", k); SUB-PARTS of a point = its candidate need words, ("w", word) (ENTER depth 2). The step's resource = the
    # reply prompt's slot under token parity (valid() keeps every merged action within the standard prompt's tokens).
    def _pwords(s, st, p):
        u = s._u(st); P = u["P"]
        if p[0] == "w": return [p[1]] if p[1] in P else []
        if p[1] >= len(u["pts"]): return []
        return sorted((w for w in content(u["pts"][p[1]][0]) if w in P and w in u["surf"]), key=lambda w: (-P[w], w))

    def parts(s, st, within=None):
        if within is None: return [("pt", k) for k in range(len(s._u(st)["pts"]))]
        return [("w", w) for w in s._pwords(st, within)]

    def merge(s, st, d):
        """The slot: per named part (dict order) the words its action puts on that part first; parts not named take the
        standard (the direct reply puts no word). A hologram kind on any named action makes the prompt a hologram (the
        format is the prompt's); no word and no hologram = the direct reply. Token parity: valid()."""
        words, kind = [], None
        for p, a in d.items():
            a = tuple(a) if a else ("direct",)
            if a[0] not in ("mention",) + HOLO_KINDS: continue
            if a[0] in HOLO_KINDS and kind is None: kind = a[0]
            pw = set(s._pwords(st, p)); words += [w for w in a[1:] if w in pw and w not in words]
        if kind: return (kind,) + tuple(words)
        return ("mention",) + tuple(words) if words else ("direct",)

    def part_objective(s, st, p):
        """The point's own value now: the expected share of its need words (P from the real tree, calibrated on this
        conversation's past) that the STANDARD direct reply covers (corpus partner-echo rate x the model's own direct
        factor). Low = a point the standard reply tends to leave uncovered. No word = 1."""
        u = s._u(st); ws = s._pwords(st, p)
        if not ws: return 1.0
        _, fac, _ = s._echo_rates(st["log"])
        num = sum(u["P"][w] * min(0.97, s.tree.p_echo(u["W"][w][0]) * fac["direct"]) for w in ws)
        return float(num / sum(u["P"][w] for w in ws))

    def focus(s, st, p):
        """The whole slot on one point (or one word): its need words, highest P first (the unit-k branch)."""
        ws = s._pwords(st, p)
        return ("mention",) + tuple(ws) if ws else ("direct",)

    def joint(s, st):
        """Native joint actions: LINK (the question point and the carried point answered as one) and TOP (the top words
        over all points)."""
        return [(n, a) for n, a in s.branches(st) if n in ("link", "top")]

    def map_part(s, st, a, pf, pt):
        """a's pattern on pf re-expressed on pt: the r-th ranked word of pf in the slot -> the r-th ranked word of pt."""
        a = tuple(a) if a else ("direct",)
        if a[0] not in ("mention",) + HOLO_KINDS: return a
        rf, rt = s._pwords(st, pf), s._pwords(st, pt)
        return (a[0],) + tuple(rt[rf.index(w)] for w in a[1:] if w in rf and rf.index(w) < len(rt))

    def shape(s, st):
        """Compact state key: number of points of h_t (<= 3), a question point, a carried point, h_t long enough for the
        READY gate, first turn of the episode."""
        u = s._u(st); i = s._i(st); now = [p for p, k in u["pts"] if k == "now"]
        return (min(3, len(now)), any(p.rstrip().endswith("?") for p in now), any(k == "carried" for _, k in u["pts"]),
                len(content(st["conv"][i][1])) >= READY_MIN, st["t"] == 0)

    OPS_OF = {"F:holo": "compress", "F:holomin": "compress", "unit": "beam", "top": "fuse", "link": "fuse"}

    def op_of(s, fam):
        """Hologram reply (the whole conversational state, compact) = COMPRESS; unit-k (slot on one point) = BEAM;
        top / link (several points in one slot) = FUSE; P1..P8 via the seed's table."""
        return s.OPS_OF.get(fam)

    # ---------- REAL2 A: Law 4 landings (one mention word in the slot) ----------
    def landings(s, st, a): return list(a[1:]) if a and a[0] in ("mention",) + HOLO_KINDS else []

    def without(s, st, a, L):
        rest = tuple(w for w in a[1:] if w != L)
        if a[0] in HOLO_KINDS: return (a[0],) + rest                       # REAL3: a hologram with fewer words
        return ("mention",) + rest if rest else ("direct",)

    def targets(s, st, a, L):
        u = s._u(st); P = u["P"]; slot = set(a[1:]); out = []
        for w in sorted((w for w in P if w not in slot and w in u["surf"]), key=lambda w: (-P[w], w)):
            if len(s.valid(st, s.retarget(st, a, L, w))) == len(a): out.append(w)   # fits the parity check, same size
            if len(out) == 3: break
        return out

    def retarget(s, st, a, L, T): return (a[0] if a[0] in HOLO_KINDS else "mention",) + tuple(T if w == L else w for w in a[1:])

    def _history(s, conv, i):
        h = [{"role": "user" if ag == "agent_1" else "assistant", "content": m} for ag, m in conv[max(0, i - HISTORY + 1): i + 1]]
        while h and h[0]["role"] != "user": h.pop(0)
        return h

    # ---------- real transition ----------
    def step(s, st, a):
        if st["sim"]: return s._sim_step(st, a)
        st = dict(st); i = st["pos"][st["t"]]; conv = st["conv"]; u = s._u(st); pts = u["pts"]
        system, msgs = s._prompt(st, a)
        if s.mock:   # STAND-IN for the interface check only, never for results: slot words, then echo of the units
            lead = " ".join(u["surf"][w] for w in a[1:]) if a[0] != "direct" else ""
            reply = clip((lead + " " + " ".join(p for p, kind in pts if kind == "now")).strip(), MODEL_WORDS)
            tin, tout = ntok(system + "".join(m["content"] for m in msgs)), ntok(reply)
        else:
            reply, tin, tout = s._chat(st, system, msgs)
        needs = content(conv[i + 2][1]) & (content(conv[i][1]) | content(conv[i + 1][1]))   # the outcome (arrives after the reply)
        cov = len(needs & content(reply)) / len(needs) if needs else None
        rc = content(reply); slot = set(a[1:]) if a[0] != "direct" else set()
        st["log"] = st["log"] + [{"kind": a[0], "slot": slot, "W": {w: k for w, (k, _) in u["W"].items()}, "reply": rc, "out": tout}]
        if a[0] in HOLO_KINDS:   # REAL3: whole-prompt parity of the hologram vs the standard prompt of this turn
            std_msgs = s._history(conv, i)
            st["parity"] = st["parity"] + [s.count(system + "".join(m["content"] for m in msgs)) - s.count(SYS + "".join(m["content"] for m in std_msgs))]
            st["holo"] = st.get("holo", 0) + 1
        else:
            st["parity"] = st["parity"] + [s.count(system) - s.count(SYS)]
        st["mentions"] += a[0] == "mention"
        st["cov"] = st["cov"] + [cov]; st["replies"] = st["replies"] + [reply]
        st["tok"] += tin + tout; st["in_tok"] += tin; st["reply_tok"] += tout; st["t"] += 1
        return st

    def _chat(s, st, system, msgs):
        """Robust reply call (24 Nov): log the exception text, retry once; a second failure = empty reply, 0 tokens."""
        for k in range(2):
            try:
                reply, tin, tout = LB.chat(s.spec, system, msgs, max_tokens=REPLY_TOK, temperature=0.0); break
            except Exception as e:     # noqa: BLE001
                note = f"[ai_human {s.spec} cell {st['cell']} turn {st['t']} try {k + 1}/2] {type(e).__name__}: {str(e)[:300]}"
                st["errors"] = st["errors"] + [note]; print(note, file=sys.stderr, flush=True)
                if not LB.retry_worthwhile(e): st["failed_calls"] = st.get("failed_calls", 0) + 1; return "", 0, 0
        else:
            st["failed_calls"] = st.get("failed_calls", 0) + 1
            return "", 0, 0
        reply = reply or ""; tin, tout = int(tin or 0), int(tout or 0)
        if tin + tout == 0:
            tin = ntok(system + "".join(m["content"] for m in msgs)); tout = ntok(reply); st["usage_est"] += 1
        return reply, tin, tout

    # ---------- the host's own model ----------
    def _echo_rates(s, log):
        """Own past replies: slot hit rate, and free-echo factor per kind vs the corpus partner-echo rate."""
        sh = sum(len(e["slot"] & e["reply"]) for e in log); sn = sum(len(e["slot"]) for e in log)
        e_dir = (sh + E_DIR * E_DIR_W) / (sn + E_DIR_W); fac = {}
        for kind in ("direct", "mention") + HOLO_KINDS:
            hit = exp = 0.0
            for e in log:
                if e["kind"] != kind: continue
                for w, k in e["W"].items():
                    if w in e["slot"]: continue
                    hit += w in e["reply"]; exp += s.tree.p_echo(k)
            fac[kind] = (hit + ECHO_W) / (exp + ECHO_W) if exp else None
        fac["direct"] = fac["direct"] or 1.0; fac["mention"] = fac["mention"] or fac["direct"]
        for kind in HOLO_KINDS: fac[kind] = fac[kind] or fac["mention"]       # REAL3
        out = [e["out"] for e in log]
        return e_dir, fac, (sum(out) + OUT_PRIOR) / (len(out) + 1)

    def fork(s, st, j):
        if st["sim"]: raise ValueError("fork of a fork")
        t = st["t"]; i = st["pos"][t]; conv = st["conv"][: i + 1]          # data up to h_t only
        u = s._units(st["cell"], st["conv"], i); words = sorted(u["W"])
        e_dir, fac, out_pred = s._echo_rates(st["log"])
        rng = np.random.default_rng([st["cell"], t, j, 4451])               # common random numbers for every action
        hist = "".join(x["content"] for x in s._history(conv, i))
        return {"sim": True, "cell": st["cell"], "t": t, "t0": t, "j": j, "pos": st["pos"], "conv": conv, "u": u,
                "words": words, "p": np.array([u["P"][w] for w in words]),
                "e_free": np.array([min(0.97, s.tree.p_echo(u["W"][w][0])) for w in words]),
                "e_dir": e_dir, "fac": fac, "out_pred": out_pred,
                "U_need": rng.random((DRAWS, len(words))), "U_echo": rng.random((DRAWS, len(words))),
                "unk": rng.poisson(u["m"], DRAWS), "cov": list(st["cov"]), "tok": st["tok"], "reply_tok": st["reply_tok"],
                "hist": hist}

    def _sim_step(s, f, a):
        f = dict(f); slot = set(a[1:]) if a[0] != "direct" else set()
        e = np.minimum(0.97, f["e_free"] * f["fac"][a[0]])
        if slot: e = np.where([w in slot for w in f["words"]], f["e_dir"], e)
        need = f["U_need"] < f["p"]; cov = f["U_echo"] < e
        den = need.sum(1) + f["unk"]; ok = den > 0
        f["cov"] = f["cov"] + [float(((need & cov).sum(1)[ok] / den[ok]).mean()) if ok.any() else None]
        if a[0] in HOLO_KINDS:   # REAL3: the hologram prompt's own token count
            system, msgs = s._holo_prompt(f, a)[:2]; f["tok"] += s.count(system + "".join(m["content"] for m in msgs)) + f["out_pred"]
        else:
            f["tok"] += s.count(f["hist"]) + s.count(s._system(f["u"], a)) + f["out_pred"]
        f["t"] += 1
        return f

    # ---------- value and report ----------
    @staticmethod
    def _mean(cov):
        sc = [c for c in cov if c is not None]; return sum(sc) / len(sc) if sc else 0.0

    def objective(s, st): return (s._mean(st["cov"]), -float(st["tok"]))   # free-resource row: lexicographic Pareto value

    def report(s, st):
        return {"result": s._mean(st["cov"]), "resource": st["tok"] / 1000.0, "reply_tokens": st["reply_tok"],
                "input_tokens": st["in_tok"], "parity_max": max(st["parity"]) if st["parity"] else 0,
                "mentions": st["mentions"], "holo": st.get("holo", 0), "scored": sum(c is not None for c in st["cov"]), "replies": len(st["cov"]),
                "errors": list(st.get("errors", [])), "usage_estimated": st.get("usage_est", 0),
                "failed_calls": st.get("failed_calls", 0),
                "unit": "coverage of the next human turn's needs (proxy); resource kilotokens"}
