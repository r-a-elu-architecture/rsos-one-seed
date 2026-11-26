"""Day 2 gate, part 1: operators behave differently, and declared meanings change what runs."""

import numpy as np

from rsoslang import compile_source
from rsoslang.runtime import run, random_env, grid_modules

HEAD = "LANGUAGE RSOS 0.2\nWORLD w\n"


def world(body, seed=0, layouts=None, choice=None):
    res = compile_source(HEAD + body)
    assert res.ok, [str(d) for d in res.errors]
    return run(res.ir, layouts, seed, choice).w


def two_paintings(seed=0):
    rng = np.random.default_rng(seed)
    return {"a": grid_modules(rng), "b": grid_modules(rng)}


def kinds(w):
    return sorted({l.kind for l in w.links})


def test_pierce_is_not_attach():
    lay = two_paintings()
    w_attach = world("OBJECT a\nOBJECT b\nMOVE b ONTO a\nATTACH b TO a\n", layouts=lay)
    w_pierce = world("OBJECT a\nOBJECT b\nMOVE b ONTO a\nPIERCE b THROUGH a\n", layouts=lay)
    assert kinds(w_attach) == ["dependency"]
    assert "pierce" in kinds(w_pierce)
    assert len(w_pierce.links) > 10 * len(w_attach.links)
    env = random_env(np.random.default_rng(1))
    assert w_attach.execute(env) != w_pierce.execute(env)


def test_pierce_goes_through_layers_and_both_ways():
    w = world("OBJECT a\nOBJECT b\nMOVE b ONTO a\nPIERCE b THROUGH a DEPTH 2\n", layouts=two_paintings())
    dst = {l.dst for l in w.links if l.kind == "pierce"}
    assert any(k.endswith(".body") for k in dst) and any(k.endswith(".subcode") for k in dst)
    assert any(k.startswith("a.") for k in dst) and any(k.startswith("b.") for k in dst)   # each side sees the other


def test_touch_is_local_and_entry_side_meaning_runs():
    lay = two_paintings()
    w_surface = world("OBJECT a\nOBJECT b\nTOUCH a ON b\n", layouts=lay)
    w_top = world("OBJECT a\nOBJECT b\nTOUCH a ON b AT top\n", layouts=lay)      # core: supervisory_entry
    assert len(w_surface.links) == 1
    assert {l.kind for l in w_top.links} == {"supervise"} and len(w_top.links) == 8


def test_a_declared_binding_changes_execution():
    lay = two_paintings()
    core = world("OBJECT a\nOBJECT b\nTOUCH a ON b AT top\n", layouts=lay)
    bound = world("OBJECT a\nOBJECT b\nMEANING contact.top = local_contact SCOPE world IN w\nTOUCH a ON b AT top\n",
                  layouts=lay)
    assert {l.kind for l in core.links} == {"supervise"}
    assert {l.kind for l in bound.links} == {"local"} and len(bound.links) == 1


def test_search_candidate_is_chosen_by_the_runner():
    body = "OBJECT a\nOBJECT b\nSEARCH contact.bottom OVER lateral, local_contact\nPIERCE a THROUGH b FROM bottom\n"
    lay = two_paintings()
    w1 = world(body, layouts=lay, choice={"contact.bottom": "lateral"})
    w2 = world(body, layouts=lay, choice={"contact.bottom": "local_contact"})
    assert "lateral" in kinds(w1) and "local" in kinds(w2)


def test_rotation_changes_many_links_at_once():
    lay = two_paintings()
    base = "OBJECT a\nOBJECT b\nMOVE b ONTO a\nPLACE b X 0.25 Y 0\nPIERCE b THROUGH a\n"
    w0 = world(base, layouts=lay)
    w1 = world("OBJECT a\nOBJECT b\nMOVE b ONTO a\nPLACE b X 0.25 Y 0 ROT 90\nPIERCE b THROUGH a\n", layouts=lay)
    assert len(w0.link_set() ^ w1.link_set()) > 5


def test_overlay_half_exposes_half():
    w = world("OBJECT a\nOBJECT b\nOVERLAY b ON a SHOW half\n", layouts=two_paintings())
    assert len(w.objs["a"].hidden) and len(w.objs["b"].hidden)


def test_region_is_not_a_point_and_whole_is_not_part():
    from rsoslang.runtime.model import Module
    rng = np.random.default_rng(3)
    car = [Module(n, "", d, xy, rng.normal(size=7)) for n, d, xy in
           [("", 0, (0, 0)), ("engine", 1, (-0.2, 0.0)), ("seat", 1, (0.05, 0.05)), ("window", 1, (0.1, 0.25))]]
    lay = {"car": car}
    pre = "OBJECT grass\nOBJECT car\nOBJECT road\nPLACE grass X -1 Y 0\nPLACE car X 0 Y 0\nPLACE road X 1 Y 0\nENTER car DEPTH 1\n"
    tri = world(pre + "REGION r SHAPE triangle CENTER car SIZE 0.4\nLINE l THROUGH grass, r, road\n", layouts=lay)
    pt = world(pre + "REGION r SHAPE point CENTER car SIZE 0.4\nLINE l THROUGH grass, r, road\n", layouts=lay)
    assert len(tri.links) > len(pt.links)
    whole = world(pre + "LINE l THROUGH grass, car, road\n", layouts=lay)
    part = world(pre + "LINE l THROUGH grass, car.seat, road\n", layouts=lay)
    assert {l.dst for l in whole.links} != {l.dst for l in part.links}


def test_path_direction_matters():
    pre = "OBJECT a\nOBJECT b\nOBJECT c\nPLACE a X 0 Y 0\nPLACE b X 1 Y 0\nPLACE c X 2 Y 0\n"
    fwd = world(pre + "LINE l THROUGH a, b, c\n")
    rev = world(pre + "LINE l THROUGH c, b, a\n")
    assert {(l.src, l.dst) for l in fwd.links} == {(l.dst, l.src) for l in rev.links}
    env = random_env(np.random.default_rng(2))
    assert fwd.execute(env, sinks_only=True) != rev.execute(env, sinks_only=True)


def test_colour_state_changes_function():
    w_black = world("OBJECT p\nSHIFT p TO black\n")
    w_grey = world("OBJECT p\nSHIFT p FROM black TO grey\n")
    pb = w_black.module("p").props
    pg = w_grey.module("p").props
    assert (pb <= 0).all()                     # destructive only
    assert (pg > pb).all()                      # good and bad held, protection added


def test_heal_and_beam():
    w = world("OBJECT top_level\nOBJECT country\nHEAL country SCOPE container\n")
    assert (w.module("country").props >= world("OBJECT top_level\nOBJECT country\n").module("country").props).all()
    lay = {"self": grid_modules(np.random.default_rng(5), rows=1, cols=2)}
    before = world("OBJECT self\n", layouts=lay)
    after = world("OBJECT self\nBEAM self\n", layouts=lay)
    deep_b = [m.props for m in before.modules() if m.depth == 2]
    deep_a = [m.props for m in after.modules() if m.depth == 2]
    assert any(not np.allclose(a, b) for a, b in zip(deep_a, deep_b))     # lands on the lower layers


def test_route_by_state():
    body = "HOST p KIND human STATES slumped, agency\nUSE HOST p\nCONSENT p\nOBJECT tv\nOBJECT problems\nOBJECT strategy\n" \
           "PLACE problems X 1 Y 0\nPLACE strategy X 2 Y 0\nROUTE tv BY slumped -> problems ; agency -> strategy\n"
    w = world(body + "USE STATE agency\n")
    assert [l.dst for l in w.all_links()] == ["strategy"]
    w = world(body + "USE STATE slumped\n")
    assert [l.dst for l in w.all_links()] == ["problems"]


def test_flows_differ_by_direction():
    lay = {"heart": grid_modules(np.random.default_rng(6), rows=1, cols=2), "other": None}
    v = world("OBJECT heart\nOBJECT other\nFLOW heart DIRECTION vertical\n", layouts=lay)
    h = world("OBJECT heart\nOBJECT other\nFLOW heart DIRECTION horizontal\n", layouts=lay)
    o = world("OBJECT heart\nOBJECT other\nFLOW heart DIRECTION outward\n", layouts=lay)
    assert all(l.dst.startswith("heart.") for l in v.links)
    assert all(l.dst.split(".")[0] == "other" for l in o.links)
    assert {l.kind for l in h.links} == {"flow_horizontal"}


def test_dot_adds_without_replacing():
    lay = {"lg": grid_modules(np.random.default_rng(7), rows=1, cols=2, depth_layers=(0,))}
    before = world("OBJECT lg\nOBJECT immune\n", layouts=lay)
    after = world("OBJECT lg\nOBJECT immune\nDOT immune INTO lg.m0 AS d1\n", layouts=lay)
    assert set(before.objs["lg"].modules) < set(after.objs["lg"].modules)
    assert np.allclose(before.module("lg.m0").props, after.module("lg.m0").props)


def test_rehost_behaves_differently_per_host():
    body = "OBJECT rocket\nOBJECT body\nOBJECT planet\n"
    w1 = world(body + "REHOST rocket IN body AS x\n")
    w2 = world(body + "REHOST rocket IN planet AS x\n")
    env = random_env(np.random.default_rng(8))
    assert w1.execute(env) != w2.execute(env)


def test_execution_is_deterministic():
    lay = two_paintings(11)
    src = "OBJECT a\nOBJECT b\nMOVE b ONTO a\nPIERCE b THROUGH a\n"
    env = random_env(np.random.default_rng(1))
    assert world(src, layouts=lay).execute(env) == world(src, layouts=two_paintings(11)).execute(env)
