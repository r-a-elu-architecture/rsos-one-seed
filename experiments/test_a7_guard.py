"""Offline tests of the ENGINE3 guards with a fake planner model (no API calls)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a1_agents as A    # noqa: E402
import a7_arms as S      # noqa: E402
import a7_guard as G     # noqa: E402

SEED, SET = 502, "S1"


def truth_patch(task, k):
    a, b = task["truths"][k], task["truths"][k + 1]
    ops = [{"op": "remove", "path": "/" + x} for x in a if x not in b]
    ops += [{"op": "replace", "path": "/" + x, "value": b[x]} for x in b if a.get(x) != b[x]]
    return json.dumps(ops)


def fake_llm(corrupt_late):
    task = A.make_task(SEED); reqs = task["requests"]; n = len(reqs)

    def llm(system, prompt):
        rec = {"cost": 0.0, "out": 0, "think": 0}
        if prompt.count("\n#") <= 1 and "#1 " in prompt and n > 1 and prompt.strip().endswith(tuple(reqs)):
            k = reqs.index(prompt.split("#1 ", 1)[1].strip())
            return "#1\n" + truth_patch(task, k), None, rec
        out = []
        for k in range(n):
            p = truth_patch(task, k)
            if corrupt_late and k >= n // 2:
                p = "[]"
            out.append(f"#{k + 1}\n{p}")
        return "\n".join(out), None, rec
    return llm


class GuardTests(unittest.TestCase):
    def test_late_repairs_corrupted_second_half(self):
        costs = []
        res, _ = S.run_plan("B2", SET, SEED, planner=G.make_planner(SEED, SET, ["LATE"], costs, fake_llm(True)),
                            auditor=lambda p, c: "\n".join(f"#{i} OK" for i in range(1, 200)))
        self.assertTrue(res["success"])

    def test_without_guard_corruption_fails(self):
        costs = []
        res, _ = S.run_plan("B2", SET, SEED, planner=G.make_planner(SEED, SET, [], costs, fake_llm(True)),
                            auditor=lambda p, c: "\n".join(f"#{i} OK" for i in range(1, 200)))
        self.assertFalse(res["success"])


if __name__ == "__main__":
    unittest.main()
