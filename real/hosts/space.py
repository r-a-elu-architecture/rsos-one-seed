"""REAL1 row 5 "space": satellite downlink over real ground-station contact windows (Skyfield SGP4 orbits).

HOST
  One Earth-observation satellite, four real ground stations (Wallops VA, Hartebeesthoek ZA, Awarua NZ, Perth AU).
  Contact windows = the satellite above 10 deg elevation at a station (Skyfield find_events on the real orbital
  elements); overlapping windows of different stations are merged (one transmitter). One step = one contact (pass).
  Budget per pass = downlink rate x contact seconds (RATE_MBPS = 2 MB/s, S-band class); bytes counted in MB.
  Data items arrive on board over time (Poisson, LAMBDA_PER_H per hour) in three classes:
      alert   p .2  size 20-80 MB    value 8-12  deadline arrival + 3-6 h
      science p .5  size 100-300 MB  value 3-6   deadline arrival + 12-24 h
      bulk    p .3  size 300-600 MB  value 1-2   deadline arrival + 36-48 h
  Items are sent in the order of the action; an item counts its value only if its last byte reaches the ground before
  its deadline (delivery time = pass start + cumulative MB / rate). Items past their deadline are dropped.
  Offered load: LAMBDA_PER_H = LOAD x (mean contact capacity in MB/h of the elements in use, over the offset-0 window)
  / MEAN_ITEM_MB, with LOAD = 1.5 and MEAN_ITEM_MB = 245 (the class mix's mean size): a fixed rule set before any seed
  run, so the load is 1.5 x capacity for any satellite (stand-in: ~300 MB/h of contacts -> ~1.8 items/h).
ACTION  : an ordered list of item ids to downlink in this pass; valid() packs them greedily into the pass budget, drops
          ids that are unknown, expired, or cannot reach the ground before their deadline in that order, and then FILLS
          the rest of the pass with the standard's next items (same order and rule as default), so every action uses the
          pass capacity as the standard does (rule 4 as changed 13:45: the resource is a constraint, not divided).
STANDARD: value-density priority queue with greedy fill: unexpired items sorted by value per MB (highest first), items
          that would miss their deadline in the transmission order are skipped, the pass is filled until no further item
          fits. Earliest-deadline-first (EDF, same greedy fill and deadline skip) was the other named standard; both
          were run in default mode on development cells 1..4 before this choice and the priority queue delivered more
          value with fewer MB in all 4 cells (R: EDF 0.0256/0.0262/0.0342/0.0292, PQ 0.0261/0.0298/0.0395/0.0340;
          value: EDF 282/299/388/363, PQ 283/321/394/393), so the priority queue is the standard (rule 1: the stronger one). `python space_quick.py --edf` prints EDF.
          Source: value/priority-queue downlink is the common operational rule for EO data; EDF is the classic
          deadline scheduler (Liu & Layland 1973).
BRANCHES (focused, same pass budget): focus_alert, focus_science, focus_bulk (only that class, EDF within it);
          urgent (only items whose deadline falls before the next pass, EDF); each is filled up by valid() with the
          standard's next items, so a branch = "this part first". No coupled action: the data items do not
          drive each other in this host.
OWN FUTURE (fork): the future pass schedule is known exactly (orbits are predictable: computed at reset from the
          elements); future data arrivals are drawn from the host's arrival model with a fresh generator seeded
          (cell, t, j, 4421), never the real generator, which draws the real arrivals only inside the real step.
REPORT  : result = value delivered before deadlines; resource = MB transmitted. OBJECTIVE = the result only (value
          delivered so far; rule 4 as changed 13:45). Pass rule per cell: Pareto win over the standard (value >= and
          MB <=, one strictly). First version divided value by MB: the seed withheld data (value per MB x3-4, value
          delivered down 33-66 %); replaced by the coordinator's decision before any sealed run.
EPISODE  : 2 days from the cell's start (cell c starts at the element epoch + (c % 6) x 6 h), ~20-30 passes.
          horizon = 6 passes, samples = 3: about 25 rollouts x 3 samples x 6 passes per decision, a few seconds per
          episode on 1 CPU here (rule 5).
ELEMENTS: real/hosts/data/space_tle.txt if present (written by space_fetch.py on the laptop from CelesTrak; first
          satellite in the file, or the one named by env REAL1_SPACE_SAT). Otherwise the STAND-IN below.
STAND-IN for the interface check only, never for results: the two-line elements of FLOCK 2E-1 (NORAD 41483, a real
          Planet EO cubesat, epoch 2018-05-15) copied from Skyfield's own test file skyfield/tests/test_io_parsing.py.
          They are real historical elements, but not current CelesTrak data; report() carries "stand_in": True.

REAL2 ADDITIONS (24 Nov; HOST_BRIEF.md REAL2 A and C)
LANDINGS (Law 4, seed.land): one landing = ONE DATA ITEM in the current pass (its id in the valid action).
          without(L): item L is not downlinked in this pass (kept on board for a later pass); valid() fills the freed
            capacity with the standard's next items as always (rule 4, 13:45: fixed-budget row, the pass happens and
            its capacity is spent whether or not L is in it; resource falls only if nothing else fits). Encoding: the
            action carries the marker -(L+1) = "not L in this pass"; valid() keeps the markers of live items, step()
            ignores them. An action without markers is handled exactly as in REAL1 (seed_noland/rollout/default are
            unchanged by this addition).
          targets(L): up to 3 live items not in the action that fit in L's place (size <= L's size + free capacity),
            highest need first: items whose deadline falls before the next pass (lost if not sent now), then value per
            MB (the standard's own priority).
          retarget(L, T): T takes L's place in the transmission order and L is marked "not in this pass" (L's bytes
            moved to T; same pass budget).
          Size: 3-8 items per pass -> at most ~30 extra rollouts per decision (quick test stays in minutes).
STRONGEST (Space("strongest"), run in mode default): receding-horizon look-ahead downlink planner. At each pass an
          exact 0-1 MILP (scipy.optimize.milp = HiGHS) assigns the CURRENT on-board queue to the current pass and all
          known future passes (the pass schedule is known from the orbit; future data arrivals are not: the plan uses
          the current queue and its deadlines only, no look-ahead into the data):
            max sum value_i x_ip (1 - 1e-3 p)       [the factor only breaks ties toward the earlier pass]
            sum_p x_ip <= 1;  sum_i size_i x_ip <= cap_p;  x_ip exists only if a_p + size_i / rate <= d_i;
            exact single-pass EDF feasibility for every deadline d_k inside pass p:
              sum_{i: d_i <= d_k} size_i x_ip <= rate (d_k - a_p) + cap_p (1 - x_kp).
          The current pass's planned items are sent in EDF order (feasible by construction); remaining capacity is
          filled by valid() in value-density order, as for every action. Re-planned at every pass.
          Source: the satellite downlink scheduling problem (SDSP) for RADARSAT-2: Karapetyan, Mitrovic-Minic, Malladi,
          Punnen, "Satellite downlink scheduling problem: A case study", Omega 53 (2015) 115-123, arXiv:1206.5503 (the
          same assignment of on-board data to known ground-station windows; they use GRASP / ejection-chain heuristics
          because of instance size). Here an instance is small (tens of items x ~25 passes), so it is solved exactly
          (HiGHS, time limit 10 s per pass, relative gap 1e-4).

REAL3 (24 Nov; HOST_BRIEF.md REAL3; seed3.py binding). Space(policy, loss=0.0). With loss=0 (the REAL1/REAL2 host) every
          action without REAL3 tokens takes the old valid()/step() verbatim (_valid2/_step2): REAL1/REAL2 modes give
          identical numbers (checked cells 1-4 against quick_logs/space_real2.txt).
LOSS MODEL (opt-in, loss=p > 0; a new variant, not the REAL2 host): every FRAME_MB = 5 MB frame is lost with probability
          p (own generator lrng (cell, 5502), so the arrival stream stays identical across modes; forks (cell, t, j,
          4422)). The standard under loss = the same priority queue + selective repeat (CCSDS CFDP class 2): the lost
          frames of an item stay on board as a residual (its size = lost MB) and are resent at a later pass; value counts
          when the last byte is down before the deadline.
HOLOGRAM CODING OF THE BACKLOG (family "F:holo"; action tokens FRAG + i and HOLO, see constants):
          (a) carry: the pass tail that no whole item fits (the standard leaves ~25 % of all pass capacity unused, e.g.
              cell 1: 10822 of 14233 MB) carries a FRAGMENT of a backlog item; the rest goes at later passes (frames
              of one item spread over passes; it counts when the last frame is down before its deadline). Only items
              that can still be completed at the next pass at full rate are offered.
          (b) code (only when loss > 0): the pass is ONE code block: r repair frames at its end (MDS / RaptorQ-class
              assumption), r = smallest with P(Binomial(n data frames, p_eff) > r) <= 0.05. Each repair frame serves
              EVERY item of the pass: if the lost data frames L <= repair frames received, all are recovered at the
              block end (items recovered then must still meet their deadline); otherwise none, and the losses become
              residuals as for the standard. Across passes the backlog's residuals are re-served at the next pass;
              with the pass-end feedback the standard already has, a fountain across passes recovers exactly what
              selective repeat does, so no extra gain is claimed there.
          (c) tube (only when loss > 0, inside a coded pass): where >= 2 stations see the satellite at once (per-station
              windows, overlaps()), both receive and their frames are merged over the ground network: frame loss p^2
              instead of p in those segments (the standard schedules one station per pass). On the STAND-IN orbit the
              four stations NEVER overlap (0.0 h in every cell tried), so the tube is inert here; it acts only with
              an orbit file / station set whose windows overlap.
          Candidates: F:holo-carry = PQ order + carry (+ code), F:holo-plan = exact-planner order + carry (+ code),
          F:holo-code = PQ order + code (loss only). With loss = 0 (b) and (c) are off: there is no loss to code against.
PRIMITIVES: P1 counter-shift (the class with the most value at risk before the next pass takes the pass, EDF); P2 price
          on loss (value density with items at risk scaled by 1 + lost/delivered so far); P3 repair (partly-delivered
          items first, EDF; only when there are any); P4P5 = the exact look-ahead MILP planner (the STRONGEST method) as one
          candidate. P6/P7/P8 are seed3's own (pool order, apoptosis, the TREE of futures).
coupled() = loss > 0: a coded pass is one block whose repair frames serve every item, so it lands as a whole; with
          loss = 0 items are landed one by one as in REAL2.
"""
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TLE_FILE = os.path.join(HERE, "data", "space_tle.txt")
STAND_IN_TLE = ("FLOCK 2E-1",
                "1 41483U 98067JD  18135.38689952  .00096183  14684-4  28212-3 0  9990",
                "2 41483  51.6270 103.3896 0004826  61.7810 298.3684 15.92672255114129")
STATIONS = {"Wallops": (37.940, -75.466), "Hartebeesthoek": (-25.887, 27.707), "Awarua": (-46.528, 168.381),
            "Perth": (-31.802, 115.885)}
MIN_ELEV = 10.0; RATE_MBPS = 2.0; LOAD = 1.5; MEAN_ITEM_MB = 245.0; DAYS = 2.0
CLASSES = [("alert", .2, (20, 80), (8, 12), (3, 6)), ("science", .5, (100, 300), (3, 6), (12, 24)),
           ("bulk", .3, (300, 600), (1, 2), (36, 48))]
_PASS_CACHE = {}
FRAME_MB = 5.0          # REAL3: downlink frame size (loss unit and code symbol)
FRAG = 10 ** 9          # REAL3 action token FRAG + i: fill the pass tail with a fragment of item i (carried across passes)
HOLO = 2 * 10 ** 9      # REAL3 action token: code this pass as one block (repair frames) + tube (station diversity)
P_FAIL = 0.05           # REAL3: repair frames r = smallest r with P(lost data frames > r) <= P_FAIL

def station_windows(tle, start_offset_h, days=DAYS):
    """REAL3: per-station (unmerged) windows, same Skyfield call as contact_windows."""
    key = ("st", tle, start_offset_h, days)
    if key in _PASS_CACHE: return _PASS_CACHE[key]
    from skyfield.api import load, EarthSatellite, wgs84
    ts = load.timescale(builtin=True); sat = EarthSatellite(tle[1], tle[2], tle[0], ts)
    t0 = ts.tt_jd(sat.epoch.tt + start_offset_h / 24.0); t1 = ts.tt_jd(t0.tt + days); out = []
    for name, (lat, lon) in STATIONS.items():
        times, ev = sat.find_events(wgs84.latlon(lat, lon), t0, t1, altitude_degrees=MIN_ELEV); rise = None
        for t, e in zip(times, ev):
            h = (t.tt - t0.tt) * 24.0
            if e == 0: rise = h
            elif e == 2: out.append((name, 0.0 if rise is None else rise, h)); rise = None
        if rise is not None: out.append((name, rise, days * 24.0))
    _PASS_CACHE[key] = out; return out

def overlaps(tle, off, passes):
    """REAL3: per pass, the segments (hours) where >= 2 stations see the satellite (where a tube can merge receptions)."""
    w = station_windows(tle, off); ev = sorted([(a, 1) for _, a, b in w] + [(b, -1) for _, a, b in w])
    seg, k, last = [], 0, None
    for t, d in ev:
        if k >= 2 and last is not None and t > last: seg.append((last, t))
        k += d; last = t
    return [[(max(a, x), min(b, y)) for x, y in seg if min(b, y) > max(a, x)] for a, b, _ in passes]

def load_tle():
    if os.path.exists(TLE_FILE):
        lines = [l.rstrip() for l in open(TLE_FILE) if l.strip()]
        want = os.environ.get("REAL1_SPACE_SAT", "")
        for i in range(len(lines) - 2):
            if lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 ") and (not want or want in lines[i]):
                return (lines[i].strip(), lines[i + 1], lines[i + 2]), False
    return STAND_IN_TLE, True

def contact_windows(tle, start_offset_h, days=DAYS):
    """Merged contact windows (start_h, end_h) relative to the episode start, from Skyfield on the real elements."""
    key = (tle, start_offset_h, days)
    if key in _PASS_CACHE: return _PASS_CACHE[key]
    from skyfield.api import load, EarthSatellite, wgs84
    ts = load.timescale(builtin=True); sat = EarthSatellite(tle[1], tle[2], tle[0], ts)
    t0 = ts.tt_jd(sat.epoch.tt + start_offset_h / 24.0); t1 = ts.tt_jd(t0.tt + days)
    wins = []
    for name, (lat, lon) in STATIONS.items():
        times, ev = sat.find_events(wgs84.latlon(lat, lon), t0, t1, altitude_degrees=MIN_ELEV)
        rise = None
        for t, e in zip(times, ev):
            h = (t.tt - t0.tt) * 24.0
            if e == 0: rise = h
            elif e == 2:
                wins.append((0.0 if rise is None else rise, h)); rise = None
        if rise is not None: wins.append((rise, days * 24.0))
    wins.sort(); merged = []
    for a, b in wins:
        if merged and a <= merged[-1][1]: merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else: merged.append((a, b))
    _PASS_CACHE[key] = merged
    return merged

def _arrivals(rng, t_from, t_to, next_id, lam):
    """Items arriving on board in [t_from, t_to) hours (the host's data model; same in the real step and the model)."""
    out = []; n = rng.poisson(lam * max(0.0, t_to - t_from))
    ps = np.array([c[1] for c in CLASSES])
    for k in range(n):
        ci = int(rng.choice(len(CLASSES), p=ps)); nm, _, sz, val, dl = CLASSES[ci]; arr = float(rng.uniform(t_from, t_to))
        out.append({"id": next_id + k, "cls": nm, "arr": arr, "size": float(rng.uniform(*sz)),
                    "value": float(rng.uniform(*val)), "deadline": arr + float(rng.uniform(*dl))})
    out.sort(key=lambda it: it["arr"])
    for k, it in enumerate(out): it["id"] = next_id + k
    return out

class Space:
    horizon = 6; samples = 3

    def __init__(s, policy="pq", loss=0.0):
        s.tle, s.stand_in = load_tle(); s.policy = policy; s._plan_cache = {}; s.loss = float(loss)   # REAL3: loss
        cap_h = sum((b - a) * 3600.0 * RATE_MBPS for a, b in contact_windows(s.tle, 0.0)) / (DAYS * 24.0)
        s.lam = LOAD * cap_h / MEAN_ITEM_MB

    # ---- episode ----
    def reset(s, cell):
        off = (cell % 6) * 6.0
        passes = [(a, b, (b - a) * 3600.0 * RATE_MBPS) for a, b in contact_windows(s.tle, off)]
        rng = np.random.default_rng([cell, 5501])
        first = passes[0][0] if passes else DAYS * 24.0
        q = _arrivals(rng, 0.0, first, 0, s.lam)
        st = {"t": 0, "cell": cell, "passes": passes, "queue": q, "next_id": len(q), "rng": rng,
              "value": 0.0, "mb": 0.0, "lost": 0.0, "model": False}
        if s.loss > 0:   # REAL3 loss model: own generator (the arrivals rng is untouched, so arrivals stay equal by mode)
            st["lrng"] = np.random.default_rng([cell, 5502]); st["ov"] = overlaps(s.tle, off, passes)
        return st

    def done(s, st): return st["t"] >= len(st["passes"])

    def _live(s, st):
        a = st["passes"][st["t"]][0]
        return [it for it in st["queue"] if it["deadline"] > a]

    def _edf(s, items): return [it["id"] for it in sorted(items, key=lambda it: (it["deadline"], it["id"]))]

    def _pq(s, items): return [it["id"] for it in sorted(items, key=lambda it: (-it["value"] / it["size"], it["id"]))]

    def default(s, st):
        if s.done(st): return []
        live = s._live(st)
        if s.policy == "strongest": return s._milp(st, live)
        return s._pq(live) if s.policy == "pq" else s._edf(live)

    def _milp(s, st, live):
        """STRONGEST: exact look-ahead MILP over the current queue and the known passes from now on (docstring)."""
        key = (st["cell"], st["t"], st["model"], tuple(it["id"] for it in live))
        if key in s._plan_cache: return s._plan_cache[key]
        from scipy.optimize import milp, LinearConstraint, Bounds
        from scipy.sparse import lil_matrix
        R = RATE_MBPS * 3600.0                                    # MB per hour
        dmax = max((it["deadline"] for it in live), default=0.0)
        P = [(a, b, c) for (a, b, c) in st["passes"][st["t"]:] if a < dmax]
        var = [(i, p) for i, it in enumerate(live) for p, (a, b, c) in enumerate(P)
               if a + it["size"] / R <= it["deadline"]]
        if not var:
            out = s._pq(live); s._plan_cache[key] = out; return out
        col = {v: n for n, v in enumerate(var)}; nv = len(var)
        c_obj = -np.array([live[i]["value"] * (1.0 - 1e-3 * p) for i, p in var])
        rows, lb, ub = [], [], []
        for i in range(len(live)):                                 # each item at most once
            r = [(col[(i, p)], 1.0) for p in range(len(P)) if (i, p) in col]
            if r: rows.append(r); lb.append(0.0); ub.append(1.0)
        for p, (a, b, cap) in enumerate(P):
            inp = [i for i in range(len(live)) if (i, p) in col]
            if not inp: continue
            rows.append([(col[(i, p)], live[i]["size"]) for i in inp]); lb.append(0.0); ub.append(cap)   # capacity
            for k in inp:                                          # EDF feasibility for deadlines inside the pass
                dk = live[k]["deadline"]
                if dk >= a + cap / R: continue
                r = [(col[(i, p)], live[i]["size"] + (cap if i == k else 0.0)) for i in inp if live[i]["deadline"] <= dk]
                rows.append(r); lb.append(-np.inf); ub.append(R * (dk - a) + cap)
        A = lil_matrix((len(rows), nv))
        for ri, r in enumerate(rows):
            for n, v in r: A[ri, n] += v
        res = milp(c_obj, integrality=np.ones(nv), bounds=Bounds(0, 1),
                   constraints=LinearConstraint(A.tocsr(), lb, ub),
                   options={"time_limit": 10.0, "mip_rel_gap": 1e-4, "disp": False})
        now = [] if res.x is None else [live[i] for (i, p), xv in zip(var, res.x) if p == 0 and xv > 0.5]
        first = s._edf(now); fs = set(first)
        out = first + [i for i in s._pq(live) if i not in fs]
        if len(s._plan_cache) > 5000: s._plan_cache.clear()
        s._plan_cache[key] = out; return out

    def branches(s, st):
        if s.done(st): return []
        live = s._live(st); out = []
        for nm, *_ in CLASSES:
            part = [it for it in live if it["cls"] == nm]
            if part: out.append((f"focus_{nm}", s._edf(part)))
        nxt = st["passes"][st["t"] + 1][0] if st["t"] + 1 < len(st["passes"]) else 1e9
        urg = [it for it in live if it["deadline"] <= nxt]
        if urg: out.append(("urgent", s._edf(urg)))
        return out

    def valid(s, st, a):
        if s._special(a): return s._valid3(st, a)                  # REAL3 hologram tokens (docstring REAL3)
        return s._valid2(st, a)

    def _valid2(s, st, a):
        """Pack the ordered ids into the pass budget; skip unknown/expired ids and items that would miss their deadline."""
        if s.done(st): return []
        a0, b0, cap = st["passes"][st["t"]]
        by = {it["id"]: it for it in st["queue"]}; used = 0.0; out = []
        excl = {-int(x) - 1 for x in a if int(x) < 0}             # REAL2 landing markers: "not this item in this pass"
        # the action's items first, then filled up with the standard's next items (no pass capacity left unused by a
        # stale or narrow branch: rule 4, 13:45)
        for i in dict.fromkeys([int(x) for x in a if int(x) >= 0] + [int(x) for x in s.default(st)]):
            it = by.get(i)
            if it is None or i in excl or used + it["size"] > cap: continue
            if a0 + (used + it["size"]) / RATE_MBPS / 3600.0 > it["deadline"]: continue
            out.append(i); used += it["size"]
        return out + [-i - 1 for i in sorted(excl) if i in by]

    # ---- REAL2 Law 4 landing interface (seed.land): one landing = one data item in the current pass ----
    def landings(s, st, a): return [int(i) for i in a if 0 <= int(i) < FRAG]   # REAL3 tokens are not landings

    def without(s, st, a, L): return [i for i in a if i != L] + [-L - 1]

    def targets(s, st, a, L):
        if s.done(st): return []
        a0, b0, cap = st["passes"][st["t"]]; by = {it["id"]: it for it in st["queue"]}
        sent = {i for i in a if i >= 0}; excl = {-i - 1 for i in a if i < 0}
        free = cap - sum(by[i]["size"] for i in sent if i in by); room = free + (by[L]["size"] if L in by else 0.0)
        nxt = st["passes"][st["t"] + 1][0] if st["t"] + 1 < len(st["passes"]) else 1e9
        cand = [it for it in s._live(st) if it["id"] not in sent and it["id"] not in excl and it["size"] <= room]
        cand.sort(key=lambda it: (0 if it["deadline"] <= nxt else 1, -it["value"] / it["size"], it["id"]))
        return [it["id"] for it in cand[:3]]

    def retarget(s, st, a, L, T): return [T if i == L else i for i in a] + [-L - 1]

    def step(s, st, a):
        if s._special(a) or s.loss > 0: return s._step3(st, a)     # REAL3 (loss model / hologram tokens)
        return s._step2(st, a)

    def _step2(s, st, a):
        st = dict(st); a0, b0, cap = st["passes"][st["t"]]
        by = {it["id"]: it for it in st["queue"]}; used = 0.0; sent = set()
        for i in a:   # a is already valid
            if i < 0: continue   # REAL2 landing marker (not sent)
            it = by[i]; used += it["size"]
            if a0 + used / RATE_MBPS / 3600.0 <= it["deadline"]: st["value"] += it["value"]
            sent.add(i)
        st["mb"] += used
        t_next = st["passes"][st["t"] + 1][0] if st["t"] + 1 < len(st["passes"]) else DAYS * 24.0
        q = [it for it in st["queue"] if it["id"] not in sent]
        st["lost"] += sum(it["value"] for it in q if it["deadline"] <= t_next)
        q = [it for it in q if it["deadline"] > t_next]
        new = _arrivals(st["rng"], a0, t_next, st["next_id"], s.lam)   # arrivals since this pass began (on board for the next)
        st["queue"] = q + new; st["next_id"] += len(new); st["t"] += 1
        return st

    def fork(s, st, j):
        """The host's own model: same pass schedule (predictable orbit), same queue as known now, future arrivals from a
        fresh generator independent of the real one."""
        f = dict(st); f["queue"] = list(st["queue"]); f["model"] = True
        f["rng"] = np.random.default_rng([st["cell"], st["t"], j, 4421])
        if s.loss > 0: f["lrng"] = np.random.default_rng([st["cell"], st["t"], j, 4422])   # REAL3 own loss model
        return f

    def objective(s, st): return st["value"]

    def report(s, st):
        return {"result": st["value"], "resource": st["mb"], "passes": len(st["passes"]), "lost_value": st["lost"],
                "loss": s.loss, "frag_mb": st.get("frag_mb", 0.0), "repair_mb": st.get("repair_mb", 0.0),
                "recovered_frames": st.get("recovered", 0), "lost_frames": st.get("lost_frames", 0),
                "standard": s.policy, "lambda_per_h": round(s.lam, 3), "stand_in": s.stand_in, "satellite": s.tle[0]}

    # ================================================================ REAL3 (seed3 binding; docstring "REAL3")
    @staticmethod
    def _special(a): return any(int(x) >= FRAG for x in a)

    def _peff(s, st, t1, t2, tube):
        """frame loss probability averaged over [t1, t2]: p, or p^2 where a tube merges two stations' receptions."""
        p = s.loss
        if not tube or t2 <= t1: return p
        ov = sum(max(0.0, min(t2, y) - max(t1, x)) for x, y in st["ov"][st["t"]])
        f = min(1.0, ov / (t2 - t1)); return p * (1 - f) + p * p * f

    def _repair(s, st, tube):
        """repair frames of the pass code: smallest r with P(Binomial(n data frames, p_eff) > r) <= P_FAIL."""
        if s.loss <= 0: return 0
        from scipy.stats import binom
        a0, b0, cap = st["passes"][st["t"]]; pe = s._peff(st, a0, b0, tube); n = int(cap // FRAME_MB)
        for r in range(n):
            if binom.sf(r, n - r, pe) <= P_FAIL: return r
        return 0

    def _valid3(s, st, a):
        if s.done(st): return []
        a0, b0, cap = st["passes"][st["t"]]; holo = HOLO in [int(x) for x in a]
        cap_d = cap - FRAME_MB * s._repair(st, True) if holo else cap
        by = {it["id"]: it for it in st["queue"]}; used = 0.0; out = []
        excl = {-int(x) - 1 for x in a if int(x) < 0}
        frags = [int(x) - FRAG for x in a if FRAG <= int(x) < HOLO]
        for i in dict.fromkeys([int(x) for x in a if 0 <= int(x) < FRAG] + [int(x) for x in s.default(st)]):
            it = by.get(i)
            if it is None or i in excl or used + it["size"] > cap_d: continue
            if a0 + (used + it["size"]) / RATE_MBPS / 3600.0 > it["deadline"]: continue
            out.append(i); used += it["size"]
        room = cap_d - used; fr = []
        for i in frags:   # the first carried fragment that is live, not sent whole, and larger than the tail
            it = by.get(i)
            if it is None or i in out or i in excl or it["deadline"] <= a0 or room < FRAME_MB or it["size"] <= room: continue
            fr = [FRAG + i]; break
        return out + fr + ([HOLO] if holo else []) + [-i - 1 for i in sorted(excl) if i in by]

    def _step3(s, st, a):
        """REAL3 real/model step: whole items, an optional tail fragment carried to later passes, an optional pass code
        (repair frames at the end of the pass) with tube; with loss, each frame is lost with p (p^2 in tube overlap).
        Lost frames that the code does not recover stay on board as a residual (selective repeat, CFDP class 2)."""
        st = dict(st); a0, b0, cap = st["passes"][st["t"]]; R = RATE_MBPS * 3600.0
        toks = [int(x) for x in a]; holo = HOLO in toks; r = s._repair(st, True) if holo else 0
        by = {it["id"]: dict(it) for it in st["queue"]}; used = 0.0; pieces = []
        for i in toks:
            if 0 <= i < FRAG:
                it = by[i]; t1 = a0 + used / R; used += it["size"]; pieces.append((i, it["size"], t1, a0 + used / R, True))
        cap_d = cap - FRAME_MB * r
        for i in toks:
            if FRAG <= i < HOLO:
                it = by[i - FRAG]; room = cap_d - used
                if room >= FRAME_MB and it["size"] > room:
                    t1 = a0 + used / R; used += room; pieces.append((i - FRAG, room, t1, a0 + used / R, False))
                    st["frag_mb"] = st.get("frag_mb", 0.0) + room
        lrng = st.get("lrng"); lost = {}
        if s.loss > 0:
            for k, (i, mb, t1, t2, _) in enumerate(pieces):
                nf = int(math.ceil(mb / FRAME_MB - 1e-9)); lost[k] = int(lrng.binomial(nf, s._peff(st, t1, t2, holo)))
        t_rep0 = a0 + used / R
        if r:
            used += FRAME_MB * r; st["repair_mb"] = st.get("repair_mb", 0.0) + FRAME_MB * r
            rx = r - int(lrng.binomial(r, s._peff(st, t_rep0, a0 + used / R, True)))
        t_block = a0 + used / R; L = sum(lost.values())
        if r and 0 < L <= rx:   # the pass code decodes: every lost data frame recovered at the block end
            st["recovered"] = st.get("recovered", 0) + L; rec = True
        else:
            rec = False; st["lost_frames"] = st.get("lost_frames", 0) + L
        sent = set()
        for k, (i, mb, t1, t2, whole) in enumerate(pieces):
            it = by[i]; miss = 0 if rec else min(lost.get(k, 0) * FRAME_MB, mb)
            t_done = t_block if (rec and lost.get(k, 0)) else t2
            rem = it["size"] - mb + miss
            if rem <= 1e-9:
                if t_done <= it["deadline"]: st["value"] += it["value"]
                sent.add(i)
            else:
                it["size"] = rem; it["part"] = True
        st["mb"] += used
        t_next = st["passes"][st["t"] + 1][0] if st["t"] + 1 < len(st["passes"]) else DAYS * 24.0
        q = [by[it["id"]] for it in st["queue"] if it["id"] not in sent]
        st["lost"] += sum(it["value"] for it in q if it["deadline"] <= t_next)
        q = [it for it in q if it["deadline"] > t_next]
        new = _arrivals(st["rng"], a0, t_next, st["next_id"], s.lam)
        st["queue"] = q + new; st["next_id"] += len(new); st["t"] += 1
        return st

    def _frag_cands(s, st, live):
        """items worth carrying: completable at the next pass start (rest of the item at full rate before its deadline)."""
        nxt = st["passes"][st["t"] + 1][0] if st["t"] + 1 < len(st["passes"]) else None
        if nxt is None: return []
        c = [it for it in live if it["size"] > FRAME_MB and nxt + it["size"] / (RATE_MBPS * 3600.0) <= it["deadline"]]
        return [FRAG + i for i in s._pq(c)[:3]]

    def primitives(s, st):
        if s.done(st): return []
        live = s._live(st); out = []
        nxt = st["passes"][st["t"] + 1][0] if st["t"] + 1 < len(st["passes"]) else 1e9
        risk = {}
        for it in live:
            if it["deadline"] <= nxt: risk[it["cls"]] = risk.get(it["cls"], 0.0) + it["value"]
        if risk:   # P1: the class with the most value at risk before the next pass pulls the pass to itself
            c = max(risk, key=risk.get); out.append(("P1", "P1:counter-shift", s._edf([it for it in live if it["cls"] == c])))
        lam = 1.0 + st["lost"] / max(st["value"], 1.0)   # P2: price on loss, rising while value keeps being lost
        out.append(("P2", "P2:price-on-loss", [it["id"] for it in sorted(
            live, key=lambda it: (-(it["value"] * (lam if it["deadline"] <= nxt else 1.0)) / it["size"], it["id"]))]))
        part = [it for it in live if it.get("part")]
        if part: out.append(("P3", "P3:repair-partial", s._edf(part)))   # P3: finish what is partly down first
        out.append(("P4P5", "P4P5:exact-planner", s._milp(st, live)))    # P4+P5: exact look-ahead MILP (strongest)
        return out

    def frame(s, st):
        if s.done(st): return []
        live = s._live(st); fr = s._frag_cands(st, live); h = [HOLO] if s.loss > 0 else []
        out = []
        if fr:
            out.append(("F:holo", "F:holo-carry", s._pq(live) + fr + h))
            out.append(("F:holo", "F:holo-plan", s._milp(st, live) + fr + h))
        if h: out.append(("F:holo", "F:holo-code", s._pq(live) + h))
        return out

    def coupled(s, st):
        return s.loss > 0   # with loss, a coded pass is one block: its repair frames serve every item (land as a whole)

    # ================================================================ REAL3 v2 hooks (real/HOST_INTERFACE_REAL3v2.md)
    # PARTS = the three data classes (alert, science, bulk): one step is one (merged) pass with one transmitter, so the
    # pass capacity is the step's resource and the classes are the parts competing for it. Stations are NOT parts: the
    # overlapping windows are merged into one pass and one transmitter serves it (the tube, loss variant only, is a
    # property of the whole coded pass, not a separate lever per station). SUB-PARTS of a class (ENTER depth 2):
    # (cls, "urgent") = its live items due before the next pass starts (lost if not sent now), (cls, "later") = the rest.
    # MERGE: in dict order, each named part's items of its action (its order kept; carried fragments FRAG+i and landing
    # markers of its items kept; HOLO kept if any named action codes the pass), then the standard's priority order on
    # the items of the parts not named; valid() packs it into the pass and fills the rest with the standard as always.
    # CARRY: the pass tail no whole item fits carries a FRAGMENT of a backlog item to later passes (the F:holo carry
    # mechanism, unchanged), exposed as carry(s, a) = a's whole items + the fragment candidates.
    # MAP_PART: a's pattern on class pf = the value-density ranks of the pf items it sends, in its order; re-expressed on
    # class pt = the pt items of the same ranks, same order.
    def _next_start(s, st): return st["passes"][st["t"] + 1][0] if st["t"] + 1 < len(st["passes"]) else 1e9

    def _sel(s, st, p):
        cls, band = (p, None) if not isinstance(p, tuple) else p; nxt = s._next_start(st)
        return lambda it: it["cls"] == cls and (band is None or ((it["deadline"] <= nxt) == (band == "urgent")))

    def parts(s, st, within=None):
        if within is None: return [nm for nm, *_ in CLASSES]
        cls = within if not isinstance(within, tuple) else within[0]
        return [(cls, "urgent"), (cls, "later")]

    def merge(s, st, d):
        by = {it["id"]: it for it in st["queue"]}; out, frags, excl, named = [], [], [], set(); holo = False
        for p, a in d.items():
            sel = s._sel(st, p); named |= {i for i, it in by.items() if sel(it)}
            for x in a:
                x = int(x)
                if x == HOLO: holo = True
                elif x >= FRAG: frags += [x] if (x - FRAG) in by and sel(by[x - FRAG]) else []
                elif x >= 0: out += [x] if x in by and sel(by[x]) else []
                elif (-x - 1) in by and sel(by[-x - 1]): excl.append(x)
        out += [int(i) for i in s.default(st) if int(i) not in named]
        return list(dict.fromkeys(out)) + frags + ([HOLO] if holo else []) + excl

    def part_objective(s, st, p):
        sel = s._sel(st, p); return -sum(it["value"] for it in s._live(st) if sel(it))   # minus value waiting on board

    def focus(s, st, p):
        sel = s._sel(st, p); return s._edf([it for it in s._live(st) if sel(it)])   # the part's items first, EDF

    def shape(s, st):
        a0, b0, cap = st["passes"][st["t"]]; back = sum(it["size"] for it in s._live(st))
        caps = sorted(c for _, _, c in st["passes"]); med = caps[len(caps) // 2]
        nxt = st["passes"][st["t"] + 1][2] if st["t"] + 1 < len(st["passes"]) else None
        band = lambda c: "none" if c is None else ("S" if c < 0.5 * med else "M" if c < 1.5 * med else "L")
        return (min(8, int(2 * back / max(cap, 1.0))), band(cap), band(nxt))   # backlog / pass (x0.5), pass, next pass

    def carry(s, st, a):
        base = [int(x) for x in a if not (FRAG <= int(x) < HOLO)]
        return base + s._frag_cands(st, s._live(st))

    def map_part(s, st, a, pf, pt):
        live = s._live(st); sf, sp = s._sel(st, pf), s._sel(st, pt)
        rf = s._pq([it for it in live if sf(it)]); rt = s._pq([it for it in live if sp(it)])
        return [rt[rf.index(int(x))] for x in a if 0 <= int(x) < FRAG and int(x) in rf and rf.index(int(x)) < len(rt)]

    def op_of(s, fam):
        if fam.startswith("focus_"): return "beam"      # the pass to one class first = BEAM 1
        if fam == "urgent": return "heal"               # what fails before the next pass is served first = HEAL
        if fam == "F:holo": return "carry"              # the pass tail carries a fragment to later passes = CARRY
        return None
