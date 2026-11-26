"""THM2 exhaustive check: runs the REAL guard code (rsos_dojo.RSOSBlind._guard + two-sign bookkeeping)
over every small world and checks the theorem's statement. No model calls.

World: token universe {L (legit IBAN), X (attacker IBAN), Y (another honest IBAN)}.
Sources: user prompt U, structured records B, documents D (free text). The attacker may write into
documents only (append or replace), never into U or B. The extractor is fully adversarial: it may return
ANY token, present in the document or not. The model may also write any literal (model = untrusted source).

Theorem 2 (k=2, as implemented). For every world, every value v accepted at a recipient sink satisfies
  (a) v in Trusted = IBANs in U  ∪  IBAN fields of B, or
  (b) v was extracted from a document D, v occurs verbatim in D, and v is the only IBAN in D.
Corollary (residual). An attacker-chosen v ∉ Trusted is accepted only if every IBAN in D is attacker-written
(the attacker replaced D's IBAN content, or D had none). Appending to a document that holds an honest IBAN never
gets an attacker IBAN accepted.
Corollary (model as untrusted source). A model-written literal recipient is accepted only if it is in Trusted.
"""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
if len(sys.argv) > 2:
    sys.path.insert(0, sys.argv[2])
    import sitecustomize_shim  # noqa: F401
sys.path.insert(0, str(Path(__file__).parent))

from rsos_dojo import IBAN_RE, RSOSBlind, Var  # noqa: E402

L, X, Y = "GB29NWBK60161331926819", "US133000000121212121212", "DE89370400440532013000"
TOK = [L, X, Y]


def subsets(xs):
    for r in range(len(xs) + 1):
        yield from itertools.combinations(xs, r)


def make_pipe(prompt_ibans, record_ibans):
    p = RSOSBlind.__new__(RSOSBlind)
    from rsos_dojo import POLICIES
    p.policy, p.enable_guard = POLICIES["banking"], True
    p.prompt = "Please handle this. " + " ".join(prompt_ibans)
    p.vars, p.counter, p.two_sign = {}, 0, {}
    p.vars[1] = Var([{"sender": i, "recipient": "me", "amount": 1.0, "subject": "x"} for i in record_ibans], {"record"}, "get_most_recent_transactions")
    p.counter = 1
    return p


def main():
    stats = dict(worlds=0, accepted=0, violations=0, attacker_accepted=0, attacker_accepted_after_append=0,
                 model_literal_untrusted_accepted=0, residual_cases=0)
    for prompt_ibans in subsets(TOK[:1] + TOK[2:]):          # attacker never writes the prompt
        for record_ibans in subsets([L, Y]):                  # attacker never writes bank records
            for honest_doc in subsets(TOK[:1] + TOK[2:]):     # honest IBAN content of the document
                for mode in ("none", "append", "replace"):
                    doc = list(honest_doc)
                    if mode == "append":
                        doc = doc + [X]
                    elif mode == "replace":
                        doc = [X]
                    text = "Bill. " + " ".join(f"IBAN: {t}" for t in doc) + " Thanks."
                    trusted = set(prompt_ibans) | set(record_ibans)
                    # 1) extracted value: adversarial extractor may return any token
                    for v in TOK:
                        p = make_pipe(prompt_ibans, record_ibans)
                        found = set(IBAN_RE.findall(text))
                        p.two_sign[v] = (v in text) and (len(found) == 1)
                        block = p._guard("send_money", {"recipient": v}, {"recipient": {"text", "extract"}})
                        stats["worlds"] += 1
                        if block is None:
                            stats["accepted"] += 1
                            ok = v in trusted or (v in text and found == {v})
                            if not ok:
                                stats["violations"] += 1
                            if v == X and X not in trusted:
                                stats["attacker_accepted"] += 1
                                if mode == "append" and any(t != X for t in honest_doc):
                                    stats["attacker_accepted_after_append"] += 1
                                if all(t == X for t in found):
                                    stats["residual_cases"] += 1
                    # 2) model-written literal (no extraction): model as an untrusted source
                    for v in TOK:
                        p = make_pipe(prompt_ibans, record_ibans)
                        block = p._guard("send_money", {"recipient": v}, {"recipient": {"literal"}})
                        stats["worlds"] += 1
                        if block is None:
                            stats["accepted"] += 1
                            if v not in trusted:
                                stats["model_literal_untrusted_accepted"] += 1
                                stats["violations"] += 1
    # password sink: only a literal present in the prompt passes
    pw = 0
    for in_prompt, prov in itertools.product((True, False), ({"literal"}, {"extract", "text"}, {"record"})):
        p = make_pipe([], [])
        p.prompt = "Set my password to 'n3w-pass'." if in_prompt else "Check my account."
        if p._guard("update_password", {"password": "n3w-pass"}, {"password": prov}) is None:
            pw += 1
            if not (in_prompt and prov == {"literal"}):
                stats["violations"] += 1
    stats["password_accepted"] = pw
    stats["attacker_accepted_only_in_residual"] = stats["attacker_accepted"] == stats["residual_cases"]
    print(stats)
    return stats


if __name__ == "__main__":
    s = main()
    sys.exit(0 if s["violations"] == 0 and s["attacker_accepted_after_append"] == 0 and s["attacker_accepted_only_in_residual"] else 1)
