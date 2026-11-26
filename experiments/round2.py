"""Round 2: the owner's rules R1–R11 made executable (spec/ROUNDS.md). Predictions written before running.

Shiva throws only the placement. What each object does comes from its nature (the library below).
"""

import numpy as np

from common import bootstrap_ci, save

CH = ["air", "heat", "light", "water", "sound", "structure", "life", "harm"]
I = {c: i for i, c in enumerate(CH)}
ATTEN_LAND, ATTEN_PIERCE, GAIN_PIERCE = 0.5, 0.7, 1.5
EPS, MAX_HOPS, DAYS_MEMORY = 0.01, 6, 10


def v(**kw):
    x = np.zeros(len(CH))
    for k, val in kw.items():
        x[I[k]] = val
    return x


# ---- painting A: the lake painting (owner, 16 Nov 2026) --------------------------------------------
# medium: what the object carries; neighbours: who its effects reach; inhabitants: who lives in it.
LAKE = {
    "sky":   {"medium": "air", "neighbours": ["sun", "bird", "trees", "lake", "house"]},
    "sun":   {"medium": "light", "neighbours": ["sky"]},
    "bird":  {"medium": "air", "neighbours": ["sky", "house", "trees"], "alive": True},     # sits on the house
    "trees": {"medium": "air", "neighbours": ["lake", "sky", "bird", "bench"], "alive": True},  # near the lake
    "house": {"medium": "structure", "neighbours": ["bird", "path", "sky"], "inhabitants": "people"},
    "lake":  {"medium": "water", "neighbours": ["trees", "bench", "sky"], "inhabitants": "fish"},
    "bench": {"medium": "structure", "neighbours": ["lake", "path"]},                      # on the lake shore
    "path":  {"medium": "structure", "neighbours": ["house", "bench"]},
}

# ---- painting B: the machine painting; outputs by nature (power) ---------------------------------------
MACHINE = {
    "engine":  v(air=0.9, heat=0.3, sound=0.5),   # a rocket engine: the turbine runs, it moves the wind
    "turbine": v(air=0.7, sound=0.4),
    "fan":     v(air=0.3, sound=0.1),
    "pipe":    v(water=0.4),
    "valve":   v(air=-0.2, water=-0.2),           # regulates: calms what flows
    "gauge":   v(light=0.1),
    "cable":   v(light=0.3, structure=0.2),
    "tank":    v(harm=0.9, structure=0.6),        # a war tank: power to destroy, a body you can enter
}


def respond(obj, x, day):
    """What an object does with what reaches it (R2–R4). Returns the outputs it passes on and its own change."""
    out, own = np.zeros(len(CH)), x.copy()
    air, heat, sound, harm = x[I["air"]], x[I["heat"]], x[I["sound"]], x[I["harm"]]
    if obj == "sky":
        if day["clouds"]:                     # the wind moves the clouds: the sun is uncovered
            own += v(light=0.4 * abs(air))
            out += v(air=0.6 * air)
        else:                                 # no clouds: aerodynamics, the wind's path changes
            out += v(air=0.8 * air)
        out += v(heat=0.5 * heat, sound=0.5 * sound)
    elif obj == "bird":
        warm = day["sunny"] and air > 0       # the wind touches the head; sunny → warmth
        if warm:
            own += v(life=0.3 * air)          # feels good, blinks
            out += v(air=0.05 * air)          # exhales: moves the air slightly
        own += v(life=-0.4 * sound - 0.8 * harm)
    elif obj == "trees":
        out += v(sound=0.15 * abs(air), life=0.1 * abs(air), air=0.3 * air)   # leaves move, oxygen
        own += v(life=-0.8 * harm)
    elif obj == "lake":
        out += v(water=0.3 * abs(air) + x[I["water"]] * 0.5)                   # waves
        own += v(life=0.1 * x[I["water"]] - 0.9 * harm)                        # fish
    elif obj == "house":
        own += v(life=0.2 * heat - 0.3 * sound - 0.9 * harm)                   # people inside
        out += v(sound=0.3 * sound)
    elif obj in ("bench", "path"):
        calm_warm = day["sunny"] and sound < 0.2
        own += v(life=0.1 if calm_warm else 0.0, structure=-0.5 * harm)
        out += v(sound=0.3 * sound)
    elif obj == "sun":
        own += v(light=0.0)
    return out, own


def propagate(host, x, day, atten, reached, delta, source):
    """Send x into host; follow the chain to neighbours with attenuation (R2, R5)."""
    frontier = [(host, x, 0)]
    while frontier:
        obj, signal, hop = frontier.pop(0)
        if np.abs(signal).max() < EPS or hop > MAX_HOPS:
            continue
        out, own = respond(obj, signal, day)
        delta[obj] = delta.get(obj, 0) + own
        reached.add(obj)
        source[obj] = source.get(obj, 0) + np.abs(own).sum()
        if np.abs(out).max() >= EPS:
            for n in LAKE[obj]["neighbours"]:
                frontier.append((n, out * atten, hop + 1))


def needs(rng):
    """The weather of the day: what it asks for."""
    return {"sunny": bool(rng.random() < 0.6), "clouds": bool(rng.random() < 0.5),
            "w": v(air=rng.uniform(-0.5, 0.5), heat=rng.uniform(-0.3, 0.6), light=rng.uniform(0, 0.6),
                   water=rng.uniform(-0.2, 0.4), sound=rng.uniform(-0.6, 0), structure=rng.uniform(0, 0.3),
                   life=rng.uniform(0.4, 1.0), harm=-1.0)}


def score(delta, day):
    return float(sum(day["w"] @ d for d in delta.values()))


def land(guest, host, day, grey, mode, rng_world):
    """One guest arrives on one host. Returns (delta, reached, tank_gathering)."""
    x = MACHINE[guest].copy()
    med = LAKE[host]["medium"]
    if med == "water":                       # air-makers in water make bubbles and waves
        x = x + v(water=0.6 * x[I["air"]]) - v(air=x[I["air"]])
    elif med == "structure":                 # in a structure, airflow becomes vibration and sound
        x = x + v(sound=0.4 * abs(x[I["air"]])) - v(air=x[I["air"]])
    gathering = None
    # R6: does the guest help here? (its direct effect on the host, judged by the day's needs)
    trial = {}
    propagate(host, x, day, 0.0, set(), trial, {})
    helps = score(trial, day) > 0
    if helps:
        x = x * 1.2                           # the host envelopes it
    elif x[I["harm"]] > 0 and grey:          # R9 grey: the harm is held, another function appears
        x = x - v(harm=0.8 * x[I["harm"]])
        if "inhabitants" in LAKE[host]:
            beta = rng_world.uniform(-0.3, 0.6)    # R10–R11: they remember and tell others, or not
            g = 0.1
            for _ in range(DAYS_MEMORY):
                g = min(1.0, max(0.0, g + beta * g * (1 - g)))
            gathering = (0.1, g)
            x = x + v(life=0.4 * g)
    gain, atten = (GAIN_PIERCE, ATTEN_PIERCE) if mode == "pierce" else (1.0, ATTEN_LAND)
    delta, reached, src = {}, set(), {}
    propagate(host, x * gain, day, atten, reached, delta, src)
    return delta, reached, gathering, src


def throw(seed, grey=True, mode="land"):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(list(LAKE))
    placement = dict(zip(MACHINE, perm))      # Shiva throws only the placement
    days = [needs(np.random.default_rng(100_000 + seed * 10 + d)) for d in range(5)]
    world_rng = np.random.default_rng(200_000 + seed)
    per_day, info = [], {"placement": placement}
    reach, engine_mag, bird_mag, tank_scores, gath = [], 0.0, 0.0, [], None
    for day in days:
        total = {}
        for guest, host in placement.items():
            d, reached, g, src = land(guest, host, day, grey, mode, np.random.default_rng(world_rng.integers(1 << 30)))
            for k, val in d.items():
                total[k] = total.get(k, 0) + val
            reach.append(len(reached))
            if guest == "engine":
                engine_mag += sum(np.abs(val).sum() for val in d.values())
            if guest == "tank":
                tank_scores.append(score(d, day))
                if host == "lake" and g is not None and gath is None:
                    gath = g
        # the bird's own breath (R4/R5): what one exhale moves, on this day
        bd = {}
        if day["sunny"]:
            propagate("sky", v(air=0.05 * 0.5), day, ATTEN_LAND, set(), bd, {})
        bird_mag += sum(np.abs(val).sum() for val in bd.values())
        per_day.append(score(total, day))
    info.update(score=float(np.mean(per_day)), reach=float(np.mean(reach)), engine=engine_mag, bird=bird_mag,
                tank=float(np.mean(tank_scores)), tank_host=placement["tank"], gathering=gath)
    return info


def main():
    seeds = range(300, 500)    # 200 throws not used while reasoning
    land_grey = [throw(s, True, "land") for s in seeds]
    land_nogrey = [throw(s, False, "land") for s in seeds]
    pierce_grey = [throw(s, True, "pierce") for s in seeds]
    p1 = sum(r["engine"] > r["bird"] for r in land_grey)
    p2 = float(np.mean([r["reach"] for r in land_grey]))
    tank_diff = [a["tank"] - b["tank"] for a, b in zip(land_grey, land_nogrey)]
    p3 = sum(d > 0 for d in tank_diff)
    lake = [r["gathering"] for r in land_grey if r["tank_host"] == "lake" and r["gathering"]]
    grew = sum(g[1] > g[0] for g in lake)
    reach_diff = [a["reach"] - b["reach"] for a, b in zip(pierce_grey, land_grey)]
    p5 = sum(d > 0 for d in reach_diff)
    sc = {"land_grey": [r["score"] for r in land_grey], "land_no_grey": [r["score"] for r in land_nogrey],
          "pierce_grey": [r["score"] for r in pierce_grey]}
    summary = {
        "P1_engine_gt_bird": {"throws": p1, "n": 200, "pass": p1 == 200},
        "P2_objects_reached_per_landing": {"mean": p2, "pass": p2 >= 3},
        "P3_grey_helps_tank_landing": {"throws_better": p3, "n": 200, "mean_diff": float(np.mean(tank_diff)),
                                       "ci95": bootstrap_ci(tank_diff), "pass": p3 >= 160},
        "P4_fish_gather_or_not": {"tank_in_lake_worlds": len(lake), "gathering_grew": grew,
                                  "pass": 0 < grew < len(lake)},
        "P5_pierce_deeper_than_land": {"throws_deeper": p5, "n": 200, "mean_extra_objects": float(np.mean(reach_diff)),
                                       "pass": p5 >= 160},
        "scene_score_mean": {k: float(np.mean(x)) for k, x in sc.items()},
        "scene_score_ci95": {k: bootstrap_ci(x) for k, x in sc.items()},
    }
    path, digest = save("ROUND-2", {"summary": summary, "throws": {"land_grey": land_grey[:20]}})
    print(path, digest)
    for k, val in summary.items():
        print(k, val)


if __name__ == "__main__":
    main()
