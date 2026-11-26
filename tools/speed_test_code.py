"""Speed test, code arm (spec/SPEED_TEST.md): edit src/rsoslang/agents/workflow.py (or apply guests in code),
press Enter to check against the task's target; the time and number of checks are logged.

    python3 tools/speed_test_code.py typos|phrasing|cost|crashes|all
"""
import importlib
import json
import sys
import time

sys.path.insert(0, "src")
from rsoslang.agents.tickets import make_tickets  # noqa: E402

A = make_tickets(500, 2, typo_rate=0.3, unseen_rate=0.3)
TASKS = {"typos": lambda m: m["accuracy"] >= 0.66, "phrasing": lambda m: m["accuracy"] >= 0.57,
         "cost": lambda m: m["cost_per_ticket"] <= 11.40 and m["accuracy"] >= 0.488,
         "crashes": lambda m: m["crashed"] == 0, "all": lambda m: m["score"] >= 0.65}
task = sys.argv[1]
t0, checks = time.time(), 0
print(f"Task {task}: edit the workflow code, then press Enter to check.")
while True:
    input()
    checks += 1
    import rsoslang.agents.library as lib
    import rsoslang.agents.workflow as wfm
    importlib.reload(lib)
    importlib.reload(wfm)
    m = wfm.build().evaluate(A, 2)
    print({k: round(m[k], 4) for k in ("accuracy", "crashed", "cost_per_ticket", "score")})
    if TASKS[task](m):
        rec = {"task": task, "seconds": round(time.time() - t0, 1), "checks": checks, "arm": "code", "metrics":
               {k: m[k] for k in ("accuracy", "crashed", "cost_per_ticket", "score")}}
        json.dump(rec, open(f"speed_test_code_{task}.json", "w"), indent=1)
        print("Done:", rec)
        break
