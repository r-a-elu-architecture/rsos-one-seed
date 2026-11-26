import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from rsoslang import dragon as D


def test_growth_and_healing_of_a_claim():
    spheres, entries = D.load()
    sizes, kids = D.grow(spheres, entries, 1, filtered=False)
    assert sizes == [48, 407]
    rif = next(b for b in spheres if b["code"] == "RIF")
    assert D.deficit(rif) == 1.0
    kid = next(c for c in kids[0] if c["parent"] == "RIF" and c["domain"] == "neuroscience")
    assert "drift" in kid["relations"] and kid["deficit"] < 1.0


def test_good_intention_rule():
    assert not D.good_intention({"relations": ["bias", "propagation"]})
    assert D.good_intention({"relations": ["bias", "containment"]})
