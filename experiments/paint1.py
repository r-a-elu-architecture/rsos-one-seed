"""PAINT-1: gestures on a painted agent workflow. See PREREGISTRATION_PAINT1.md."""

import os

from common import save, ROOT
from rsoslang.agents.workflow import build
from rsoslang.agents.tickets import make_tickets
from rsoslang.painting.scene import apply, encode, render_svg

A = make_tickets(500, 2, typo_rate=0.3, unseen_rate=0.3)
B = make_tickets(500, 3, typo_rate=0.3, unseen_rate=0.3)

COMPOSED = """PIERCE spell_corrector THROUGH classify.brain
PIERCE synonym_expander THROUGH classify.brain
PIERCE cache THROUGH memory.heart
PIERCE fast_retry THROUGH act.heart
SHIFT act TO grey
"""


def ev(wf, data, seed):
    r = wf.evaluate(data, seed)
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}


def main():
    base = build()
    results = {"baseline": {"A": ev(base, A, 2), "B": ev(base, B, 3), "changes": []}}
    gestures = {}
    for guest in ("spell_corrector", "synonym_expander"):
        for place in ("head", "heart", "brain"):
            gestures[f"{guest}@classify.{place}"] = f"PIERCE {guest} THROUGH classify.{place}\n"
        gestures[f"{guest}@near.classify"] = f"PLACE {guest} NEAR classify\n"
    for place in ("head", "heart", "brain"):
        gestures[f"cache@memory.{place}"] = f"PIERCE cache THROUGH memory.{place}\n"
    gestures["fast_retry@act.heart"] = "PIERCE fast_retry THROUGH act.heart\n"
    gestures["act grey"] = "SHIFT act TO grey\n"
    gestures["heal act"] = "HEAL act\n"
    gestures["amount_validator dot extract"] = "DOT amount_validator INTO extract\n"
    gestures["composed"] = COMPOSED
    wfs = {}
    for name, g in gestures.items():
        wf, changes = apply(base, g)
        wfs[name] = wf
        results[name] = {"A": ev(wf, A, 2), "B": ev(wf, B, 3), "changes": changes, "gesture": g.strip()}

    def outc(n):
        return (results[n]["A"]["accuracy"], results[n]["A"]["cost_per_ticket"])

    h1 = {guest: len({outc(f"{guest}@classify.{p}") for p in ("head", "heart", "brain")} | {outc(f"{guest}@near.classify")})
          for guest in ("spell_corrector", "synonym_expander")}
    ba, bb = results["baseline"]["A"], results["baseline"]["B"]
    g_a, g_b = results["act grey"]["A"], results["act grey"]["B"]
    summary = {
        "H1_place_decides": {"distinct_outcomes": h1, "pass": all(v >= 3 for v in h1.values())},
        "H2_near_acts_on_neighbours": {
            "classify_errors_baseline": ba["errors"].get("classify", 0),
            "classify_errors_near": results["spell_corrector@near.classify"]["A"]["errors"].get("classify", 0),
            "pass": ba["errors"].get("classify", 0) == results["spell_corrector@near.classify"]["A"]["errors"].get("classify", 0)},
        "H3_grey_contains": {"crashed_A": g_a["crashed"], "crashed_B": g_b["crashed"],
                             "accuracy_A": [ba["accuracy"], g_a["accuracy"]], "accuracy_B": [bb["accuracy"], g_b["accuracy"]],
                             "pass": g_a["crashed"] == 0 and g_b["crashed"] == 0 and g_a["accuracy"] >= ba["accuracy"]
                             and g_b["accuracy"] >= bb["accuracy"]},
        "H4_cache_where_it_means": {
            "cost": {p: results[f"cache@memory.{p}"]["A"]["cost_per_ticket"] for p in ("head", "heart", "brain")},
            "baseline": ba["cost_per_ticket"],
            "pass": results["cache@memory.heart"]["A"]["cost_per_ticket"] < ba["cost_per_ticket"] <= results["cache@memory.head"]["A"]["cost_per_ticket"]},
        "H5_composed_beats_baseline": {"score_A": [ba["score"], results["composed"]["A"]["score"]],
                                       "score_B": [bb["score"], results["composed"]["B"]["score"]],
                                       "accuracy_A": [ba["accuracy"], results["composed"]["A"]["accuracy"]],
                                       "pass": results["composed"]["A"]["score"] > ba["score"] and results["composed"]["B"]["score"] > bb["score"]},
    }
    path, digest = save("PAINT-1", {"summary": summary, "results": {k: {kk: vv for kk, vv in v.items()} for k, v in results.items()}})
    # paintings: baseline and composed, measured on A
    before = render_svg(encode(base, results["baseline"]["A"]), "The workflow as a painting: before")
    after = render_svg(encode(wfs["composed"], results["composed"]["A"]), "After the gestures (measured on held-out A)")
    rows = "".join(f"<tr><td>{k}</td><td><code>{v.get('gesture', '—')}</code></td><td>{v['A']['accuracy']:.3f}</td>"
                   f"<td>{v['A']['crashed']:.3f}</td><td>{v['A']['cost_per_ticket']:.2f}</td><td>{v['A']['score']:.3f}</td>"
                   f"<td>{v['B']['score']:.3f}</td></tr>" for k, v in results.items())
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>PAINT-1</title>
<style>body{{font-family:sans-serif;max-width:1150px;margin:24px auto;color:#222}}table{{border-collapse:collapse;font-size:13px}}
td,th{{border:1px solid #ccc;padding:4px 8px}}code{{font-size:12px}}</style></head><body>
<h1>PAINT-1: a program edited as a painting</h1>
<p>Twelve-module support workflow. Gestures are RSOS statements compiled into exact program changes; every number is
measured by running the program on held-out tickets (A: seed 2, B: seed 3; 30% typos, 30% unseen phrasing).
Squares are guests at a place: above = head, centre = heart, purple = brain, right = near.</p>
{before}<br>{after}
<h2>Every gesture, measured</h2><table><tr><th>Gesture</th><th>RSOS</th><th>Accuracy A</th><th>Crashed A</th>
<th>Cost/ticket A</th><th>Score A</th><th>Score B</th></tr>{rows}</table>
<p>results_sha256 {digest}</p></body></html>"""
    with open(os.path.join(ROOT, "results", "PAINT-1.html"), "w") as f:
        f.write(html)
    print(path, digest)
    for k, v in summary.items():
        print(k, v)
    for k, v in results.items():
        print(f"{k:34s} acc {v['A']['accuracy']:.3f} crash {v['A']['crashed']:.3f} cost {v['A']['cost_per_ticket']:.2f} score {v['A']['score']:.3f} | B {v['B']['score']:.3f}")


if __name__ == "__main__":
    main()
