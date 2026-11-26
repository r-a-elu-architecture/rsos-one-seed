"""T9: search, removal, induction, transfer. See PREREGISTRATION_T9.md."""
from common import save
from rsoslang.agents.workflow import build
from rsoslang.agents.tickets import make_tickets
from rsoslang.discovery import search, removal, induce, score, program, CHOICES

S = make_tickets(500, 11, typo_rate=0.3, unseen_rate=0.3)
A = make_tickets(500, 2, typo_rate=0.3, unseen_rate=0.3)
B = make_tickets(500, 3, typo_rate=0.3, unseen_rate=0.3)
OTHER = make_tickets(500, 21, typo_rate=0.5, unseen_rate=0.1)


def main():
    base = build()
    found = search(base, S, 11)
    best_s, best_cfg = found[0]
    ho = {n: score(base, best_cfg, d, sd) for n, d, sd in (("A", A, 2), ("B", B, 3))}
    import json
    table = json.load(open("../results/editor_table.json"))["table"]
    best_ho_A = max(v["score"] for v in table.values())
    rem = removal(base, best_cfg, A, 2)
    rule = induce(found)
    none = {g: None for g in CHOICES}
    other_base, other_rule = score(base, none, OTHER, 21), score(base, rule, OTHER, 21)
    summary = {
        "best_program_on_search_set": program(best_cfg).strip().split("\n"), "search_score": round(best_s, 4),
        "H1_holds_on_held_out": {"A": round(ho["A"], 4), "B": round(ho["B"], 4), "best_possible_A": best_ho_A,
                                 "pass": best_ho_A - ho["A"] <= 0.02},
        "H2_removal_locates_function": {"loss_when_removed": rem,
                                        "pass": max(rem.values()) >= 0.05 and min(rem.values()) < 0.01},
        "H3_induced_rule_transfers": {"rule": rule, "other_host_baseline": round(other_base, 4),
                                      "other_host_rule": round(other_rule, 4), "pass": other_rule - other_base >= 0.05},
    }
    path, digest = save("T9-DISCOVERY", {"summary": summary})
    print(path, digest)
    for k, v in summary.items():
        print(k, v)


if __name__ == "__main__":
    main()
