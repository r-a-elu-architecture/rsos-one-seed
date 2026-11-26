"""Tests for rsos_engine on a toy host (maximise a hidden quadratic); no study data."""
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsos_engine as R  # noqa: E402

SPACE = R.Space({"a": (0.0, 1.0, "float"), "b": (0, 5, "int")})
INC = {"a": 0.0, "b": 0}
score = lambda c: -((c["a"] - 0.7) ** 2) - 0.1 * (c["b"] - 3) ** 2


class EngineTests(unittest.TestCase):
    def run_engine(self, **kw):
        path = tempfile.mktemp(suffix=".jsonl"); gen = R.Genome(path)
        champ, rec = R.run(SPACE, INC, score, kw.pop("law0", lambda c: True), kw.pop("target", lambda c: score(c) > -0.01),
                           gen, np.random.default_rng(1), **kw)
        return champ, rec, path

    def test_improves_and_chain_verifies(self):
        champ, rec, path = self.run_engine(causes=[{"b": 3}])
        self.assertGreater(score(champ), score(INC)); self.assertTrue(R.Genome.verify(path))

    def test_law0_refuses(self):
        _, rec, _ = self.run_engine(law0=lambda c: c["b"] != 3, target=lambda c: False, max_evals=20)
        self.assertGreater(rec["law0_refused"], 0)

    def test_tote_exits(self):
        _, rec, _ = self.run_engine(target=lambda c: False, patience=3, max_evals=100)
        self.assertIn(rec["exit"], ("information_budget", "budget"))

    def test_mother_coverage(self):
        _, rec, _ = self.run_engine(target=lambda c: False, max_evals=30, patience=100)
        self.assertTrue(all(rec["alloc"][c] >= 3 for c in R.EXPLORERS))

    def test_tamper_breaks_chain(self):
        _, _, path = self.run_engine(); lines = open(path).read().splitlines()
        lines[1] = lines[1].replace('"child"', '"chlid"'); open(path, "w").write("\n".join(lines) + "\n")
        self.assertFalse(R.Genome.verify(path))


if __name__ == "__main__":
    unittest.main()
