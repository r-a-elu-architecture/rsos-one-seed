"""A3b: the hologram palace (D90) in the A3 harness. PREREGISTRATION_A3B.md.

`a1_agents.py` is imported unchanged (so A3's P and D stay byte-identical). An H condition is the palace flow of P
with a codec on every edge; every LLM prompt is built exactly as in P, and every wire message is asserted to decode
to exactly the text P would have carried ("if the door is opened ... everything is there and the same").

    python experiments/a3b_hologram.py smoke Hc|Hd        # seed 999
    python experiments/a3b_hologram.py run [Hc,Hd]        # seeds 100-107, 300-307, resumable
    python experiments/a3b_hologram.py replayP Hc|Hd      # offline: H codec on A3's recorded P conversations
"""

import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a1_agents as A                      # noqa: E402
from rsoslang import palace as PAL         # noqa: E402

SEEDS = list(range(100, 108)) + list(range(300, 308))
RES = os.path.join(A.ROOT, "results", "a3b_results.jsonl")
TRANS = os.path.join(A.ROOT, "results", "a3b_transcripts.jsonl")
_lock = threading.Lock()

try:
    import tiktoken
    _BPE = tiktoken.get_encoding("o200k_base")

    def bpe(s):
        return len(_BPE.encode(s))
except Exception:  # noqa: BLE001
    _BPE = None

    def bpe(s):
        return -1


class Undecodable(Exception):
    pass


# ---------------------------------------------------------------- H-copy (the brief's table; fixed in the prereg)

class HCopy:
    name = "Hc"
    DOT = 6

    def table_tok(self):
        return A.ntok(A.UCR_TABLE)

    def new_task(self, init_text):
        pass

    def dot(self, text):
        return PAL.h(text, self.DOT)

    # instruction (planner -> worker): '#<dot>' + qenc(instruction)
    def enc_instr(self, instr, planner_book):
        return f"#{self.dot(planner_book)}\n{A.qenc(instr)}"

    def dec_instr(self, msg, worker_book):
        head, _, body = msg.partition("\n")
        return A.qdec(body), head[1:]

    # edits (worker -> checker, forwarded to the planner): anchors + ' =<dot of new state>'
    def enc_edits(self, old_text, new_text):
        ed = A.edits_between(A.state_of_text(old_text), A.state_of_text(new_text))
        pay = A.d_payload(ed)
        return (pay + " " if pay else "") + "=" + self.dot(new_text)

    def dec_edits(self, msg, book_text):
        """New book text, or raise Undecodable (truncation / mismatch / malformed)."""
        items = msg.split(" ")
        dot = items[-1]
        if not dot.startswith("=") or len(dot) != self.DOT + 1:
            raise Undecodable("dot")
        ed = []
        for it in items[:-1]:
            if it.startswith("-"):
                if it[1:] not in A.OF_ANCHOR and "." not in it[1:]:
                    raise Undecodable(it)
                ed.append((A.OF_ANCHOR.get(it[1:], it[1:]), None))
            else:
                a, eq, v = it.partition("=")
                if not eq or not v or (a not in A.OF_ANCHOR and "." not in a):
                    raise Undecodable(it)
                ed.append((A.OF_ANCHOR.get(a, a), A.OF_ANCHOR.get(v, v)))
        new = A.text_of(A.apply_ed(A.state_of_text(book_text), ed))
        if self.dot(new) != dot[1:]:
            raise Undecodable("hash")
        return new

    # door
    def enc_verdict(self, good, reason, base_text=None, attempted_text=None):
        return "✓" if good else "✗ " + A.qenc(reason)

    def dec_verdict(self, msg, base_text=None, attempted_text=None):
        return (True, None) if msg == "✓" else (False, A.qdec(msg[2:]))

    # heal by reference: restore from the agreed snapshot, verify with the dot, notice '!k'
    def heal_worker(self, work, snap, planner_book, dot_rx):
        w, s = work.split("\n"), snap.split("\n")
        if len(w) == len(s):
            ks = [i for i in range(len(w)) if w[i] != s[i]]
            if ks and self.dot(snap) == dot_rx:
                return snap, [("worker", "planner", "!" + ",".join(map(str, ks)))]
        healed, chan, _ = A.dragon_heal(planner_book, work)
        return healed, [("worker", "planner", chan)]

    def heal_fallback_tok(self, planner_book, work):
        return A.ntok(A.dragon_heal(planner_book, work)[1])

    # generic interface used by run_task
    def receive_instr(self, msg, work, snap, planner_book):
        instr, dot_rx = self.dec_instr(msg, work)
        heal = []
        if self.dot(work) != dot_rx:                     # green dot: drift found before the LLM call
            work, hm = self.heal_worker(work, snap, planner_book, dot_rx)
            heal = [(a, b, t, "heal") for a, b, t in hm]
        return instr, work, heal

    def checker_heal(self, sender_text, checker_book):
        healed, chan, _ = A.dragon_heal(sender_text, checker_book)
        return healed, [("checker", "worker", chan, "heal")]

    def do_forward(self, m, approved_text, planner_book):
        msgs = [("checker", "planner", m, "msg")]
        try:
            return self.dec_edits(m, planner_book), msgs
        except Undecodable:
            chan = A.dragon_heal(approved_text, planner_book)[1]
            return approved_text, msgs + [("planner", "checker", chan, "heal")]


# ---------------------------------------------------------------- the H task run (P's flow, codec on every edge)

def run_task(codec, seed, tag=None):
    cond = codec.name
    task = A.make_task(seed)
    truths = task["truths"]
    plan = A.drift_plan(task, truths)
    log, msgs, calls, drift_events = [], [], [], []
    t_start = time.time()
    ctx = {"attempt": 0, "step": 0}
    codec.new_task(A.text_of(task["init"]))

    def send(step, a, b, text, kind="msg", book=None):
        m = {"step": step, "attempt": ctx["attempt"], "from": a, "to": b, "text": text, "tok": A.ntok(text),
             "bpe": bpe(text), "bytes": len(text.encode()), "kind": kind}
        if book is not None:
            m["book"] = book
        msgs.append(m)

    def call(role, prompt):
        text, so, rec = A.llm(A.SYS[role], prompt, None, log)
        rec["role"] = role; rec["step"] = ctx["step"]; rec["attempt"] = ctx["attempt"]
        calls.append(rec)
        return text, so, rec

    books = {r: A.text_of(task["init"]) for r in ("planner", "worker", "checker")}
    snaps = dict(books)                       # agreed state at the last approval (not touched by drift)
    step_fail = 0
    for st, req in enumerate(task["requests"]):
        ctx["step"], ctx["attempt"] = st, 0
        instr, _, _ = call("planner", f"Change request: {req}\n\nState:\n{books['planner']}")
        instr = instr.strip()
        m = codec.enc_instr(instr, books["planner"])
        send(st, "planner", "worker", m)
        dr = plan.get(st)
        d_ev = None
        if dr:
            ws = A.state_of_text(books["worker"]); ws[dr[0]] = dr[1]; books["worker"] = A.text_of(ws)
            d_ev = {"step": st, "key": dr[0], "true": truths[st][dr[0]], "wrong": dr[1]}
        t0 = time.time()
        drifted = books["worker"] != snaps["worker"]
        fb_tok = codec.heal_fallback_tok(books["planner"], books["worker"]) if drifted else None
        instr_rx, healed, hm = codec.receive_instr(m, books["worker"], snaps["worker"], books["planner"])
        assert instr_rx == instr, "instruction not restored exactly"
        if healed != books["worker"] or hm:
            books["worker"] = healed
            for a, b, txt, kd in hm:
                send(st, a, b, txt, kind=kd)
            if d_ev:
                d_ev.update({"detected_by": "green_dot" if cond == "Hc" else "snapshot_sha",
                             "recovery_tok": sum(A.ntok(x[2]) for x in hm),
                             "recovery_sec": time.time() - t0, "fallback_heal_tok": fb_tok})
        if d_ev:
            d_ev["pre_worker_true"] = A.state_of_text(books["worker"]).get(d_ev["key"]) == d_ev["true"]
        feedback, ok = "", False
        for attempt in range(A.MAX_RETRY + 1):
            ctx["attempt"] = attempt
            fb = f"\n\nThe checker rejected your previous attempt: {feedback}" if feedback else ""
            wtext, _, _ = call("worker", f"Instruction: {instr_rx}{fb}\n\nYour state:\n{books['worker']}\n\n{A.W_P}")
            old = books["worker"]
            new_text = A.text_of(A.apply_edits(A.state_of_text(old), wtext))
            m = codec.enc_edits(old, new_text)
            assert codec.dec_edits(m, old) == new_text, "edits not restored exactly"
            send(st, "worker", "checker", m, book=books["checker"])
            try:
                dec_text = codec.dec_edits(m, books["checker"])
            except Undecodable:
                healed, hm = codec.checker_heal(old, books["checker"])
                books["checker"] = healed
                for a, b, txt, kd in hm:
                    send(st, a, b, txt, kind=kd)
                dec_text = codec.dec_edits(m, books["checker"])
            cprompt = (f"Change request: {req}\nInstruction: {instr}\n\nChanges the worker made (decoded):\n"
                       f"{A.diff_view(A.state_of_text(books['checker']), A.state_of_text(dec_text))}\n\n{A.C_OUT}")
            ctext, so, _ = call("checker", cprompt)
            good, reason = A.parse_verdict(ctext, so)
            vm = codec.enc_verdict(good, reason, books["checker"], dec_text)
            g_rx, r_rx = codec.dec_verdict(vm, old, new_text)
            assert g_rx == good and (good or r_rx == reason), "verdict not restored exactly"
            send(st, "checker", "worker", vm)
            if good:
                books["checker"] = dec_text
                dp, fms = codec.do_forward(m, dec_text, books["planner"])
                for a, b, txt, kd in fms:
                    send(st, a, b, txt, kind=kd)
                books["planner"] = dp
                books["worker"] = new_text
                snaps = {r: new_text for r in snaps}
                if hasattr(codec, "approved"):
                    codec.approved(new_text)
                ok = True
                break
            feedback = r_rx
        if not ok:
            step_fail += 1
            books["worker"] = books["planner"]
        if d_ev:
            copies = [A.state_of_text(b) for b in books.values()]
            cur = A.state_of_text(books["planner"])
            d_ev["healed"] = all(c.get(d_ev["key"]) == d_ev["true"] for c in copies)
            d_ev["healed_zero_call"] = d_ev["healed"] and d_ev["pre_worker_true"]
            d_ev["caught"] = cur.get(d_ev["key"]) == d_ev["true"]
            d_ev.setdefault("detected_by", "none")
            drift_events.append(d_ev)
    final = A.state_of_text(books["planner"])
    copies = [A.state_of_text(b) for b in books.values()]
    truth = task["final"]
    keys = set(truth) | set(final)
    acc = sum(final.get(k) == truth.get(k) for k in keys) / len(keys)
    for e in drift_events:
        e["silent_in_final"] = final.get(e["key"]) != e["true"]
        e["in_any_copy_final"] = any(c.get(e["key"]) != e["true"] for c in copies)
    res = {"cond": cond, "seed": seed, "tag": tag, "success": final == truth, "line_acc": acc,
           "replica_success": all(c == truth for c in copies),
           "final_errors": sorted(k for k in keys if final.get(k) != truth.get(k)),
           "steps_failed": step_fail, "n_msgs": len(msgs), "n_calls": len(calls),
           "channel_tok": sum(m["tok"] for m in msgs), "channel_bpe": sum(m["bpe"] for m in msgs),
           "channel_bytes": sum(m["bytes"] for m in msgs),
           "billed_tok": sum(A.billed(c) for c in calls), "out_tok": sum(c["out"] for c in calls),
           "in_tok": sum(c["in"] + c["cache_w"] + c["cache_r"] for c in calls),
           "cost_usd": sum(c["cost"] or 0 for c in calls), "wall_sec": time.time() - t_start,
           "drift": drift_events,
           "per_call": [{k: c[k] for k in ("role", "step", "attempt", "in", "cache_w", "cache_r", "out", "sec")}
                        for c in calls],
           "per_msg": [{k: m[k] for k in ("step", "attempt", "from", "to", "tok", "bpe", "bytes", "kind")}
                       for m in msgs]}
    out = os.environ.get("A_TRANSCRIPTS", TRANS)
    with _lock:
        with open(out, "a") as f:
            f.write(json.dumps({"cond": cond, "seed": seed, "tag": tag, "msgs": msgs, "calls": log}) + "\n")
    print(f"{cond} {seed} success={res['success']} acc={acc:.3f} chan={res['channel_tok']} bpe={res['channel_bpe']} "
          f"billed={res['billed_tok']} calls={len(calls)} wall={res['wall_sec']:.0f}s "
          f"heal0={sum(e['healed_zero_call'] for e in drift_events)}/3", flush=True)
    return res


# ---------------------------------------------------------------- codecs, replay, runner

def codec_of(name):
    if name == "Hc":
        return HCopy()
    if name == "Hd":
        from a3b_hdragon import HDragon
        return HDragon()
    raise ValueError(name)


def replay_with(rec, codec_name, seed):
    """Run an H codec over recorded LLM outputs (prompts asserted identical)."""
    queue = list(rec["calls"])
    real = A.llm

    def fake(system, prompt, schema=None, log=None):
        c = queue.pop(0)
        assert c["prompt"] == prompt and c["system"] == system[:40], "replay diverged"
        r = {k: c[k] for k in ("in", "cache_w", "cache_r", "out", "sec", "api_ms", "turns", "cost")}
        if log is not None:
            log.append(c)
        return c["text"], c["structured"], r

    A.llm = fake
    try:
        res = run_task(codec_of(codec_name), seed, tag="replayP")
    finally:
        A.llm = real
    assert not queue, "unused recorded calls"
    return res


def replay_p(codec_name):
    os.environ["A_TRANSCRIPTS"] = os.path.join(A.ROOT, "results", f"a3b_replayP_{codec_name}_transcripts.jsonl")
    if os.path.exists(os.environ["A_TRANSCRIPTS"]):
        os.remove(os.environ["A_TRANSCRIPTS"])
    out = []
    for line in open(os.path.join(A.ROOT, "results", "a3_transcripts.jsonl")):
        rec = json.loads(line)
        if rec["cond"] == "P":
            out.append(replay_with(rec, codec_name, rec["seed"]))
    path = os.path.join(A.ROOT, "results", f"a3b_replayP_{codec_name}.json")
    json.dump({"runs": out}, open(path, "w"), indent=1)
    n = len(out)
    print(codec_name, "replay of A3 P:", n, "runs; chan", sum(r["channel_tok"] for r in out) / n,
          "bpe", sum(r["channel_bpe"] for r in out) / n, "success", sum(r["success"] for r in out),
          "heal0", sum(e["healed_zero_call"] for r in out for e in r["drift"]))


def main_run(conds):
    done = {}
    if os.path.exists(RES):
        for line in open(RES):
            r = json.loads(line); done[(r["cond"], r["seed"])] = r
    todo = [(c, s) for s in SEEDS for c in conds if (c, s) not in done]
    print(f"loaded {len(done)}, live {len(todo)}", flush=True)
    with ThreadPoolExecutor(int(os.environ.get("A3B_WORKERS", "8"))) as ex:
        futs = [ex.submit(run_task, codec_of(c), s) for c, s in todo]
        for fu in as_completed(futs):
            r = fu.result(); done[(r["cond"], r["seed"])] = r
            with _lock:
                with open(RES, "a") as f:
                    f.write(json.dumps(r) + "\n")
    runs = [done[(c, s)] for s in SEEDS for c in conds if (c, s) in done]
    json.dump({"model": A.MODEL, "runs": runs}, open(os.path.join(A.ROOT, "results", "a3b_runs.json"), "w"), indent=1)
    print("wrote a3b_runs.json", len(runs))


if __name__ == "__main__":
    if sys.argv[1] == "smoke":
        os.environ["A_TRANSCRIPTS"] = os.path.join(A.ROOT, "results", "a3b_smoke_transcripts.jsonl")
        r = run_task(codec_of(sys.argv[2]), 999, tag="smoke")
        print(json.dumps({k: v for k, v in r.items() if k not in ("per_call", "per_msg")}, indent=1))
    elif sys.argv[1] == "run":
        main_run(sys.argv[2].split(",") if len(sys.argv) > 2 else ["Hc", "Hd"])
    elif sys.argv[1] == "replayP":
        replay_p(sys.argv[2])
