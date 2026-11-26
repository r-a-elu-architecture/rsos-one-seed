"""A2 analysis: Q1-Q4 from results/a2_runs.json -> results/a2_dragon.json + results/A2_map.png (3D map)."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import ROOT, save              # noqa: E402

PARTS = ["planner", "worker", "checker", "memory", "channel"]
DEPTHS = ["surface", "procedure", "structure"]


def draw(landings, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(projection="3d")
    pos = {}
    for L in landings:
        x, y, z = PARTS.index(L["part"]), DEPTHS.index(L["depth"]), L["order"]
        pos[L["order"]] = (x, y, z)
        ax.scatter([x], [y], [z], s=60 + 120 * L["predicted_error_reduction_per_task"], color="#30a46c")
        ax.text(x, y, z + 0.15, f'{L["order"]}. {L.get("primitive") or "prompt"}\n{L["domain"][:28]}', fontsize=7)
    for L in landings:
        for d in L.get("depends_on", []):
            if d in pos:
                a, b = pos[d], pos[L["order"]]
                ax.plot([a[0], b[0]], [a[1], b[1]], [a[2], b[2]], color="#ffc53d", lw=1.2)
    ax.set_xticks(range(len(PARTS))); ax.set_xticklabels(PARTS, fontsize=7)
    ax.set_yticks(range(len(DEPTHS))); ax.set_yticklabels(DEPTHS, fontsize=7)
    ax.set_zlabel("order"); ax.set_title("A2 knowing White Dragon: landings (part x depth x order)", fontsize=9)
    fig.savefig(path, dpi=150, bbox_inches="tight")


def main():
    R = json.load(open(os.path.join(ROOT, "results", "a2_runs.json")))
    S = R["stages"]
    base = S["baseline"]["errors_per_task"]
    B = R["budget"]
    curve = {a: [base] + [S[f"{a}_{k}"]["errors_per_task"] for k in range(1, B + 1)]
             for a in ("knowing", "blind", "weighted")}
    curve["shuffled"] = [base] + [S[f"shuffled_{k}"]["errors_per_task"] for k in range(1, B)] + [curve["knowing"][-1]]
    red = {a: c[0] - c[-1] for a, c in curve.items()}
    gains = {a: [c[k - 1] - c[k] for k in range(1, B + 1)] for a, c in curve.items()}
    auc = {a: sum(base - x for x in c[1:]) for a, c in curve.items()}
    know = R["knowing_map"]
    pred_total = sum(L["predicted_error_reduction_per_task"] for L in know)
    tok = {a: [S["baseline"]["billed_mean"]] + [S[f"{a}_{k}"]["billed_mean"] for k in range(1, B + 1)]
           for a in ("knowing", "blind", "weighted")}
    succ = {a: [S["baseline"]["success"]] + [S[f"{a}_{k}"]["success"] for k in range(1, B + 1)]
            for a in ("knowing", "blind", "weighted")}
    drift = {a: [S["baseline"]["drift_caught"]] + [S[f"{a}_{k}"]["drift_caught"] for k in range(1, B + 1)]
             for a in ("knowing", "blind", "weighted")}
    checks = {
        "Q1": {"knowing": red["knowing"], "blind": red["blind"], "weighted": red["weighted"],
               "pass": red["knowing"] >= 2 * red["blind"] and red["knowing"] >= red["weighted"]},
        "Q2": {"gains": gains["knowing"], "pass": sum(g > 0 for g in gains["knowing"]) >= 3},
        "Q3": {"predicted_total": pred_total, "measured_total": red["knowing"],
               "pass": abs(pred_total - red["knowing"]) <= 0.5 * abs(red["knowing"]) if red["knowing"] else False},
        "Q4": {"auc_map": auc["knowing"], "auc_shuffled": auc["shuffled"], "perm": R["shuffle_perm"],
               "pass": auc["knowing"] >= auc["shuffled"]},
    }
    landings = {a: S[f"{a}_{B}"]["landings"] for a in ("knowing", "blind", "weighted")}
    calib = [{"order": L["order"], "part": L["part"], "primitive": L["primitive"],
              "predicted": L["predicted_error_reduction_per_task"], "measured": g}
             for L, g in zip(know, gains["knowing"])]
    draw(know, os.path.join(ROOT, "results", "A2_map.png"))
    payload = {"dragon_model": R["dragon_model"], "agent_model": R["agent_model"], "seeds": R["seeds"],
               "curves_errors_per_task": curve, "gains": gains, "auc": auc, "billed_mean": tok, "success": succ,
               "drift_caught": drift, "calibration": calib, "landings": landings, "weights_final":
               R.get("weights_final"), "checks": checks}
    p, d = save("a2_dragon", payload)
    print(json.dumps({k: payload[k] for k in ("curves_errors_per_task", "gains", "auc", "billed_mean", "success",
                                              "drift_caught", "calibration", "checks")}, indent=1))
    for a in ("blind", "weighted"):
        print(a, [(L["part"], L["depth"], L["primitive"], L["domain"][:30]) for L in landings[a]])
    print(p, d)


if __name__ == "__main__":
    main()
