"""Conformance tests for RSOS protocol v0."""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import protocol_v0 as P  # noqa: E402

BOOK = {"cup.owner": "rover", "mug.owner": "rover", "cup.x": "3", "mug.x": "5"}
SAFE_VALUES = {"owner": {"rover", "drone", "arm"}, "x": {str(i) for i in range(10)}}


def safe(k, v):
    return v in SAFE_VALUES[k.split(".")[1]]


def env(ops, book=BOOK, seq=1):
    return P.envelope("A", "B", "memory", book, ops, seq, safe)


class Conformance(unittest.TestCase):
    def test_accept_valid(self):
        b, v = P.receive(dict(BOOK), env([{"op": "REHOST", "field": "owner", "old": "rover", "new": "drone"}]), safe, set())
        self.assertEqual(v, "accepted"); self.assertEqual(b["cup.owner"], "drone"); self.assertEqual(b["mug.owner"], "drone")

    def test_values_never_travel(self):
        e = env([{"op": "DERIVE", "src": "cup.x", "dst": "mug.x", "add": 2, "cap": 9}])
        self.assertTrue(all("value" not in op for op in e["ops"]))
        self.assertNotIn(BOOK["cup.x"], [str(v) for op in e["ops"] for k, v in op.items() if k not in ("op", "src", "dst")])

    def test_tamper_refused(self):
        e = env([{"op": "SET", "key": "cup.x", "value": "4"}]); e2 = copy.deepcopy(e); e2["ops"][0]["value"] = "7"
        self.assertEqual(P.receive(dict(BOOK), e2, safe, set())[1], "refused:tampered")

    def test_not_ready_refused(self):
        drifted = dict(BOOK); drifted["cup.x"] = "8"
        self.assertEqual(P.receive(drifted, env([{"op": "SET", "key": "mug.x", "value": "1"}]), safe, set())[1],
                         "refused:not_ready")

    def test_law0_refused(self):
        self.assertEqual(P.receive(dict(BOOK), env([{"op": "SET", "key": "cup.x", "value": "99"}]), safe, set())[1],
                         "refused:law0")

    def test_replay_refused(self):
        seen = set(); e = env([{"op": "SET", "key": "cup.x", "value": "4"}])
        b, v = P.receive(dict(BOOK), e, safe, seen); self.assertEqual(v, "accepted")
        self.assertIn(P.receive(dict(BOOK), e, safe, seen)[1], ("refused:replay", "refused:not_ready"))

    def test_unknown_operator_refused(self):
        self.assertEqual(P.receive(dict(BOOK), env([{"op": "WIPE"}]), safe, set())[1], "refused:operator")


if __name__ == "__main__":
    unittest.main()
