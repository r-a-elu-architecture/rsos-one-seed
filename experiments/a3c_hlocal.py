"""A3c H-local (labelled arm): Qwen/Qwen2.5-0.5B as the shared predictor (results/a3c_dragon_design.json).

Stream per prose message: MODE {LLM 15/16, HPRED 1/16}; LLM = payload tokens + EOT under the model's quantised
full-vocabulary distribution, then chk8 = sha256(T || S) mod 256; HPRED = the H-pred stream. The encoder codes both
ways and keeps the shorter. Every forward pass is counted as a local model call. Edits, door approve, forward and
heal are H-pred's.

Determinism: fp32 weights pinned to one snapshot, eager attention, fixed threads, deterministic algorithms, one
model call at a time (global lock), identical code path (prefill DYN in one pass, then one token per call) on both
sides. DEV: the design's fresh-process proofread decode is not run (its risk 5 allows dropping it); chk8, the
canonical check and the '?' NAK fallback to H-pred remain.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
os.environ.setdefault("MKL_CBWR", "AVX2")

import copy                                 # noqa: E402
import hashlib                              # noqa: E402
import json                                 # noqa: E402
import re                                   # noqa: E402
import threading                            # noqa: E402
import time                                 # noqa: E402

import numpy as np                          # noqa: E402

import a1_agents as A                       # noqa: E402
import a3c_hpred as P                       # noqa: E402
from a3c_coder import Dec, Enc, Undecodable  # noqa: E402

MODEL_ID = "Qwen/Qwen2.5-0.5B"
REVISION = "060db6499f32faf8b98477b0a26969ef7d8b9987"   # snapshot hash recorded at download
EOT = 151643
PRE_LIMIT, CTX_LIMIT = 1400, 2600
HEADER = "Instructions written by a planner for a worker who edits a configuration state.\n\n"
LOCK = threading.Lock()
STATS = {"forward_passes": 0, "tokens_processed": 0, "cpu_sec": 0.0, "wall_sec": 0.0}


class Qwen:
    _inst = None

    _load_lock = threading.Lock()

    @classmethod
    def get(cls):
        with cls._load_lock:                       # one load per process (8 task threads start together)
            if cls._inst is None:
                cls._inst = cls()
        return cls._inst

    def __init__(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(4)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
        torch.use_deterministic_algorithms(True)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
        self.model = AutoModelForCausalLM.from_pretrained(MODEL_ID, revision=REVISION, dtype=torch.float32,
                                                          attn_implementation="eager").eval()
        self.pre_ids = build_pre(self)
        with torch.inference_mode():
            out = self._fwd(self.pre_ids, None)
        self.pre_cache = out.past_key_values

    def ids(self, s):
        return self.tok.encode(s, add_special_tokens=False)

    def _fwd(self, ids, cache):
        t0, c0 = time.time(), time.process_time()
        x = self.torch.tensor([ids], dtype=self.torch.long)
        out = self.model(input_ids=x, past_key_values=cache, use_cache=True)
        STATS["forward_passes"] += 1
        STATS["tokens_processed"] += len(ids)
        STATS["wall_sec"] += time.time() - t0
        STATS["cpu_sec"] += time.process_time() - c0
        return out

    def run(self, cd, dyn, payload):
        """Code payload token ids (encoder) or decode them (decoder) under PRE + dyn. Returns the ids incl. EOT."""
        torch = self.torch
        with LOCK, torch.inference_mode():
            cache = copy.deepcopy(self.pre_cache)
            out = self._fwd(dyn, cache)
            cache = out.past_key_values
            res = []
            while True:
                lg = out.logits[0, -1].float().numpy().astype(np.float64)
                z = lg - lg.max()
                p = np.exp(z)
                p /= p.sum()
                V = len(p)
                freq = 1 + np.floor(p * ((1 << 30) - V)).astype(np.int64)
                cum = np.cumsum(freq)
                t = cd.cumsym(cum, payload[len(res)] if cd.enc else None)
                res.append(int(t))
                if t == EOT:
                    return res
                if len(res) > 1500:
                    raise Undecodable("runaway")
                out = self._fwd([int(t)], cache)
                cache = out.past_key_values


def block(q, label, ids):
    return q.ids(label) + ids + [EOT] + q.ids("\n\n")


def build_pre(q):
    """Design: greedy exemplars by new distinct word trigrams (ties: lower (seed, step)) while PRE <= 1,400 Qwen
    tokens; then the 2 shortest priming reject reasons; exemplars in (seed, step) order."""
    path = os.path.join(A.ROOT, "results", "a3c_priming_transcripts.jsonl")
    ex, reasons = [], []
    if os.environ.get("A3C_PRE") != "none":
        for line in open(path):
            t = json.loads(line)
            pl = [c for c in t["calls"] if c["system"].startswith("You are the PLANNER")]
            for st, c in enumerate(pl):
                ex.append(((t["seed"], st), c["text"].strip()))
            for c in t["calls"]:
                if c["system"].startswith("You are the CHECKER"):
                    g, r = A.parse_verdict(c["text"], c["structured"])
                    if not g:
                        reasons.append(((t["seed"], c.get("step", 0)), r))
    ex.sort()

    def tri(s):
        w = re.findall(r"\w+", s.lower())             # IMPL: word = \w+, lowercased
        return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}

    covered, chosen = set(), []
    pre = q.ids(HEADER)
    pool = list(ex)
    while pool:
        best = max(pool, key=lambda e: (len(tri(e[1]) - covered), [-x for x in e[0]]))
        add = block(q, "Instruction:\n", q.ids(best[1]))
        if len(pre) + len(add) > PRE_LIMIT:
            break
        chosen.append(best); covered |= tri(best[1]); pre = pre + add
        pool.remove(best)
    chosen.sort()
    pre = q.ids(HEADER)
    for _, t in chosen:
        pre += block(q, "Instruction:\n", q.ids(t))
    for _, r in sorted(reasons, key=lambda e: (len(e[1]), e[0]))[:2]:
        pre += block(q, "Reviewer rejection:\n", q.ids(r))
    q.pre_info = {"exemplars": [k for k, _ in chosen], "n_reasons": min(2, len(reasons)), "pre_tokens": len(pre)}
    return pre


def chk8(text, S):
    return int(hashlib.sha256((text + A.text_of(S)).encode()).hexdigest(), 16) % 256


class HLocal(P.HPred):
    name = "Hl"

    def new_task(self, init_text):
        P.HPred.new_task(self, init_text)
        self.q = Qwen.get()
        self.hist_text = []
        self.cur_text = ""
        self.stats.update({"mode_llm": 0, "mode_hpred": 0, "llm_ctx_fallback": 0})

    def _dyn(self, S, mode, extra_text=None):
        q = self.q
        ids = []
        for t in self.hist_text[-6:]:
            ids += block(q, "Instruction:\n", q.ids(t))
        ids += q.ids("State:\n") + q.ids(A.text_of(S)) + q.ids("\n\n")
        if mode == "I":
            ids += q.ids("Instruction:\n")
        else:
            instr, ops = extra_text
            lines = [f"{k} = {v}" if t == "set" else f"delete {k}" if t == "del" else f"add {k} = {v}"
                     for t, k, v in ops]
            ids += q.ids("Instruction:\n") + q.ids(instr) + [EOT] + q.ids("\nProposed edits:\n") + \
                q.ids("\n".join(lines)) + q.ids("\nReviewer rejection:\n")
        return ids

    def _llm_words(self, text, S, mode, rx):
        q = self.q
        pay = q.ids(text)
        dyn = self._dyn(S, mode, rx)
        if q.tok.decode(pay, clean_up_tokenization_spaces=False) != text or \
                len(q.pre_ids) + len(dyn) + len(pay) + 1 > CTX_LIMIT:
            self.stats["llm_ctx_fallback"] += 1
            return None
        cd = Enc()
        cd.sym(["L", "P"], [15, 1], "L")
        q.run(cd, dyn, pay + [EOT])
        cd.uni(256, chk8(text, S))
        return cd.words()

    def _hp_words(self, text, S, mode, extra):
        cd = Enc()
        cd.sym(["L", "P"], [15, 1], "P")
        P.code_message(cd, self.M, self._ctx(S, mode, *extra), P.lex(text))
        return cd.words()

    def _enc(self, text, S, mode, extra=((), ()), rx=None, force_hp=False):
        hp = self._hp_words(text, S, mode, extra)
        lw = None if force_hp else self._llm_words(text, S, mode, rx)
        return lw if lw is not None and len(lw.split(" ")) <= len(hp.split(" ")) else hp

    def _dec(self, msg, S, mode, extra=((), ()), rx=None):
        cd = Dec(msg)
        m = cd.sym(["L", "P"], [15, 1])
        if m == "L":
            ids = self.q.run(cd, self._dyn(S, mode, rx), None)
            text = self.q.tok.decode(ids[:-1], clean_up_tokenization_spaces=False)
            if cd.uni(256) != chk8(text, S):
                raise Undecodable("chk8")
            cd.check_canonical()
            # the H-pred model is kept primed on every message (IMPL): same update as if H-pred had coded it
            units, upd = P.code_message(Enc(), self.M, self._ctx(S, mode, *extra), P.lex(text))
        else:
            units, upd = P.code_message(cd, self.M, self._ctx(S, mode, *extra), None)
            cd.check_canonical()
            text = "".join(s for _, s in units)
        self.stats["mode_llm" if m == "L" else "mode_hpred"] += 1
        return text, units, upd

    def enc_instr(self, instr, planner_book):
        self._sent = instr
        return self._enc(instr, A.state_of_text(planner_book), "I")

    def receive_instr(self, msg, work, snap, planner_book):
        if P.sha8(work) != P.sha8(snap):
            work = snap
        S = A.state_of_text(work)
        heal = []
        try:
            t, units, upd = self._dec(msg, S, "I")
        except Undecodable:
            # design: worker '?' -> checker relays '?' -> planner re-sends in H-pred mode (counted)
            self.stats["nak"] += 1
            m2 = self._enc(self._sent, A.state_of_text(planner_book), "I", force_hp=True)
            heal = [("worker", "checker", "?", "nak"), ("checker", "planner", "?", "nak"),
                    ("planner", "worker", m2, "nak")]
            t, units, upd = self._dec(m2, S, "I")
            msg = m2
        self._commit_instr(t, units, upd, msg)
        self.hist_text.append(t)
        self.cur_text = t
        return t, work, heal

    def _rx(self, base_text, attempted_text):
        old, new = A.state_of_text(base_text), A.state_of_text(attempted_text)
        return self.cur_text, P.ops_between(old, new)

    def enc_verdict(self, good, reason, base_text, attempted_text):
        if good:
            return "+"
        return self._enc(reason, A.state_of_text(base_text), "R", self._reason_extra(base_text, attempted_text),
                         self._rx(base_text, attempted_text))

    def dec_verdict(self, msg, base_text, attempted_text):
        if msg == "+":
            return True, None
        t, units, upd = self._dec(msg, A.state_of_text(base_text), "R",
                                  self._reason_extra(base_text, attempted_text), self._rx(base_text, attempted_text))
        P.apply_updates(self.M, upd)
        self.stats["n_reason"] += 1
        self.stats["reason_chars"] += len(t)
        self.stats["reason_bits"] += P.bits_of(msg)
        return False, t
