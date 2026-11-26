"""REAL1 row 6, ENERGY: a home battery dispatched hour by hour on real solar and real household load.

REAL DATA
  Solar: pvlib's bundled real TMY3 file 723170TYA.CSV (Greensboro Piedmont Triad Intl, NC; measured/modelled NSRDB TMY3
    irradiance and temperature). PV output computed with pvlib: solar position, Hay-Davies plane-of-array irradiance,
    SAPM cell temperature (open rack glass/glass), PVWatts DC model (6 kWp, gamma -0.4 %/C), 14 % system losses,
    PVWatts inverter (5 kW AC, 96 % nominal). Array: tilt 30 deg, azimuth 180 deg.
  Load: UCI "Individual household electric power consumption" (one real household, Sceaux, France), hourly kWh,
    1000 hours 2006-12-16 18:00 .. 2007-01-27 09:00 (fetched by energy_fetch.py, sha256-checked).
  Pairing: each load hour (local clock, hour-starting) takes the TMY3 hour with the same month, day and clock hour
    (TMY3 stamps are hour-ending, so stamp h+1 covers h..h+1). Same season (Dec-Jan), different sites: the pairing is
    a documented construction, not one measured site.
DOCUMENTED PARAMETERS (fixed here, before any run)
  Battery: 13.5 kWh usable, 5 kW continuous, 90 % round-trip (Tesla Powerwall 2 datasheet values); charge and
    discharge efficiency sqrt(0.9) each; start state of charge 50 %. No battery export to the grid (battery discharge is
    capped at the household's net load, the usual net-metering rule).
  Tariff (DECLARED three-period residential time-of-use, the structure of US utility TOU rates; the values are set here,
    not quoted from one utility): off-peak 23:00-07:00 $0.12/kWh, mid 07:00-16:00 and 21:00-23:00 $0.22/kWh,
    peak 16:00-21:00 $0.42/kWh; PV export credit $0.04/kWh.
  Wear proxy: lambda = $0.05 per kWh cycled (LFP pack ~$300/kWh over ~6000 full cycles).
MEASURE
  (rule 4 as fixed 13:45: objective = the result only; the resource is a constraint; pass = Pareto win per cell)
  result   = NET $ saved vs the same house with no battery over the episode, after the wear cost:
             (no-battery cost - battery cost) + (end - start stored energy) x discharge efficiency x off-peak price
             - lambda x kWh cycled. The stored-energy term values what is left at its cost to recreate, so neither
             method can gain by emptying or hoarding at the end. The wear cost is part of the real money result.
  resource = battery throughput, kWh cycled (AC energy charged + discharged). Budget: the same 5 kW / 13.5 kWh
             limits for every action (valid()).
  objective(state) = result so far, exactly (no division, no bonus). report also gives saved_gross (before wear).
STANDARD METHOD (default)
  Rule-based TOU dispatch as in residential battery controllers ("Time-Based Control" of Tesla Powerwall, SolarEdge
  StorEdge TOU profiles; rule-based dispatch in e.g. Luthander et al. 2015, Appl. Energy 142:80): (1) PV surplus always
  charges the battery; (2) peak hours: discharge to cover the net load; (3) mid hours 21-23: discharge to cover the net
  load (cheap refill follows); mid hours 07-16: discharge only the energy above a reserve kept for the coming peak, the
  reserve = yesterday's 16-21 net-load deficit (persistence, data up to now); (4) off-peak: charge from the grid at full
  power up to a target = capacity - yesterday's 07-16 PV surplus (room left for tomorrow's solar); never discharge.
  The current hour's load and PV are observed in real time (as an inverter does); nothing later is seen.
OWN FUTURE (fork, layer-1 rule)
  Hours after the current one are a forecast from data up to now: load = same hour yesterday (persistence) x lognormal
  noise (sigma 0.25); PV = pvlib clear-sky PV (Ineichen, Linke turbidity 3: astronomy, not data) x yesterday's daily
  clear-sky index x lognormal noise (sigma 0.30). The noise rng is seeded from (cell, t, j, 6061), never the real data.
BRANCHES  hold, charge full (5 kW), charge half, discharge full, discharge half (focused: the hour's power budget on one
  direction), self-consume (coupled: battery follows PV - load exactly). valid() enforces power, energy and no-export.
SIZE (rule 5)  episode T = 168 h (one week), horizon 24 h (one daily cycle), samples 3: about 11 candidates x 2
  continuations x 3 forks x 25 hours ~ 1.7k model steps per decision; one seed episode ~10-20 s on 1 CPU here.
  Cells: start hour drawn by rng(cell) in [48, 1000 - 168]; dev cells 1..4.
REAL2 A. LANDINGS (Law 4, seed.land)
  A landing = one kWh block of this hour's charge/discharge decision: |b| is cut into 1 kWh blocks (the last one may be
  smaller), ids 0..n-1 (at most 5 = PMAX). without(L) = the decision with that block not drawn (|b| smaller by the
  block). targets(L) = up to 3 later hours inside the own horizon (and the episode) where the same block is needed most,
  read from the host's own state (data up to now: persistence load and PV of the same clock hour yesterday, the tariff):
  a discharge block goes to the hours with the highest price x uncovered forecast net load; a charge block to the hours
  where charging is cheapest (forecast PV surplus: export credit forgone; else the off-peak price). retarget(L, T) =
  the block withheld now and COMMITTED to hour T: the action becomes (b, ((T, +-kWh),)); the commitment is kept in the
  state and added on top of whatever action is taken at hour T, clipped there to the same power / energy / no-export
  limits (same resource). Actions without commitments stay plain floats, so the default path is unchanged bit for bit.
REAL2 C. STRONGEST METHOD (standard="strongest")
  Scenario-based stochastic MPC (two-stage stochastic programming in receding horizon; e.g. Parisio, Rikos & Glielmo
  2014 IEEE TCST 22(5):1813 "A model predictive control approach to microgrid operation optimization"; Hans, Sopasakis,
  Bemporad & Raisch, scenario-based MPC for energy management; Bertsekas, Dynamic Programming and Optimal Control vol.
  1, ch. 6 on MPC). Every hour: S = 20 scenarios of the next min(24, T - t) hours from the SAME forecast model as the
  own future (persistence load x lognormal 0.25; clear-sky PV x yesterday's clear-sky index x lognormal 0.30; data up to
  now only; rng seeded from (cell, t, scenario, 6062), independent of the forks and of the real data). The current hour
  is observed (as for the rule). One LP (scipy.optimize.linprog, HiGHS): per scenario and hour charge c, discharge d,
  import, export and SOC; the first hour's (c, d) is shared by all scenarios (non-anticipative), later hours are
  per-scenario recourse. Cost = the result exactly: import price x import - export credit x export + wear x (c + d) -
  terminal SOC x discharge efficiency x off-peak price; limits = 5 kW, 0..13.5 kWh, sqrt(0.9) each way, discharge <= net
  load (no export). The first hour's c - d is applied; the problem is re-solved next hour.
REAL3 (seed3 binding; read only by seed3.run, the REAL1/REAL2 modes give identical numbers)
  primitives(state):
    P2   "price_on_wear": the rule with the wear priced into its thresholds (see _rule_wear: grid kWh pay wear only at
         peak, so off-peak charging stops at the peak need; 21-23 discharge only above tonight's charge target).
    P4P5 "scenario_mpc": the strongest method's action (the scenario MPC above) as one candidate; valued in the forks by
         its own first action, the forks continue with the standard rule (no LP inside forks).
    P5   "soc_dp_realpast_tree": SOC dynamic programming (0.25 kWh grid, 0.125 kWh action grid, linear interpolation)
         over the REAL-PAST scenario tree: each hour of the next min(24, T - t) has 7 branches = the net load of the
         same clock hour on each of the last 7 real days (data up to now only); recombining, decided after each hour is
         observed; stage cost = grid $ + wear (the result exactly), terminal value = stored kWh x ED x off-peak price.
  frame(state):  F:coupled_hours "realpast_day_paths": the same DP but each past day is a whole path (the hours of one
         day drive each other), two-stage (non-anticipative at hour 0), mean of the 7 path values.
  coupled(state) = True: the hours are coupled through the state of charge; seed3 lands the chosen action whole.
REAL3 v2 HOOKS (25 Nov; real/HOST_INTERFACE_REAL3v2.md; read only by seed3.run(..., "seed3"))
  parts = the hour's three energy streams of the one battery: "pv" (PV surplus stored), "grid" (energy charged from the
    grid, on top of the surplus), "load" (net load covered by discharge); no sub-parts (ENTER depth 1).
  merge = each named stream from its action, the others from the rule; dict order = who gets the 5 kW first; the first
    non-zero stream sets the direction (one battery cannot charge and discharge in one hour).
  part_objective (0..1, data up to now): pv = share of the last 24 h PV surplus stored; load = price-weighted share of
    the last 24 h mid/peak net load covered by the battery; grid = readiness for the coming peak (deliverable stored
    energy / yesterday's 16-21 deficit). The state keeps the last 24 applied hours ("hist"; nothing else reads it).
  focus = the hour's whole power on one stream (store all surplus / charge 5 kW / cover the whole net load).
  map_part = the same share of the target stream's capacity this hour. joint = self-consume (serves pv and load).
  carry = the hour's unused power in the action's direction committed to the next hour (REAL2 commitment, clipped there
    to the same limits). shape = (hour of day, price period, SOC quarter, PV surplus now) (COMPRESS / INHERIT key).
  op_of: hold -> carry; charge/discharge full/half -> beam; self_consume -> fuse; F:coupled_hours -> zoom (a whole
    day as one block); P2 / P4P5 / P5 by the seed's table (contain / fuse / inherit).
"""
import math, os
import numpy as np, pandas as pd, pvlib
import scipy.sparse as sp
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
LOAD_CSV = os.path.join(HERE, "data", "household_load_uci_hourly.csv")
TMY = os.path.join(os.path.dirname(pvlib.__file__), "data", "723170TYA.CSV")

CAP, PMAX, RTE = 13.5, 5.0, 0.90
EC = ED = math.sqrt(RTE)
P_OFF, P_MID, P_PEAK, P_EXP = 0.12, 0.22, 0.42, 0.04
LAMBDA = 0.05

def price(hour):
    if hour >= 23 or hour < 7: return P_OFF, "off"
    if 16 <= hour < 21: return P_PEAK, "peak"
    return P_MID, "mid"

def _grid_cost(g, hour):
    p, _ = price(hour)
    return p * g if g > 0 else P_EXP * g

def _pv_series():
    d, m = pvlib.iotools.read_tmy3(TMY, coerce_year=1990, map_variables=True)
    loc = pvlib.location.Location(m["latitude"], m["longitude"], tz="Etc/GMT+5", altitude=m["altitude"])
    t_mid = d.index - pd.Timedelta(minutes=30)                      # hour-ending stamps -> sun at mid-hour
    sp = loc.get_solarposition(t_mid)
    dni_extra = pvlib.irradiance.get_extra_radiation(t_mid)
    def ac(ghi, dni, dhi, temp, wind):
        poa = pvlib.irradiance.get_total_irradiance(30, 180, sp["apparent_zenith"].values, sp["azimuth"].values,
                                                    dni, ghi, dhi, dni_extra=dni_extra.values, model="haydavies")
        tc = pvlib.temperature.sapm_cell(poa["poa_global"], temp, wind,
                                         **pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"])
        pdc = pvlib.pvsystem.pvwatts_dc(poa["poa_global"], tc, 6000.0, -0.004) * (1 - 0.14)
        return np.nan_to_num(np.asarray(pvlib.inverter.pvwatts(pdc, 5000.0 / 0.96, eta_inv_nom=0.96))) / 1000.0
    pv = ac(d["ghi"].values, d["dni"].values, d["dhi"].values, d["temp_air"].values, d["wind_speed"].values)
    cs = loc.get_clearsky(t_mid, model="ineichen", solar_position=sp, linke_turbidity=3.0)
    pvc = ac(cs["ghi"].values, cs["dni"].values, cs["dhi"].values, d["temp_air"].values * 0 + 10.0, d["wind_speed"].values * 0 + 1.0)
    start = d.index - pd.Timedelta(hours=1)                         # hour-starting clock hour
    key = list(zip(start.month, start.day, start.hour))
    return dict(zip(key, np.maximum(pv, 0))), dict(zip(key, np.maximum(pvc, 0)))

class Energy:
    horizon = 24; samples = 3
    NSCEN = 20
    def __init__(s, T=168, standard="rule"):
        s.T = T; s.standard = standard
        if not os.path.exists(LOAD_CSV): raise SystemExit("run real/hosts/energy_fetch.py first")
        ld = pd.read_csv(LOAD_CSV, parse_dates=["datetime"])
        s.load = (ld["Global_active_power"].values / 60.0).tolist()          # kWh per hour
        pvmap, csmap = _pv_series()
        ts = ld["datetime"]
        s.pv = [float(pvmap[(x.month, x.day, x.hour)]) for x in ts]
        s.cs = [float(csmap[(x.month, x.day, x.hour)]) for x in ts]
        s.hour = [int(x.hour) for x in ts]
        s._cache = {}

    # ---- data access: real states read the true series (only up to now is ever asked); forks read their forecast
    def _L(s, st, k):
        f = st["src"]
        return f[0][k - f[2]] if (f is not None and k >= f[2]) else s.load[k]
    def _PV(s, st, k):
        f = st["src"]
        return f[1][k - f[2]] if (f is not None and k >= f[2]) else s.pv[k]

    def reset(s, cell):
        rng = np.random.default_rng([int(cell), 6060])
        i0 = int(rng.integers(48, len(s.load) - s.T))
        return {"cell": int(cell), "i0": i0, "t": 0, "soc": 0.5 * CAP, "soc0": 0.5 * CAP, "cost": 0.0, "nobat": 0.0,
                "thr": 0.0, "src": None, "commit": {}}
    def done(s, st): return st["t"] >= s.T

    def _now(s, st):
        k = st["i0"] + st["t"]; return k, s._L(st, k), s._PV(st, k), s.hour[k]

    def default(s, st):
        if s.standard == "strongest": return s._mpc(st)
        return s._rule(st)
    def _rule(s, st):
        k, L, PV, h = s._now(st); net = L - PV; _, per = price(h)
        if net < 0:                                               # (1) PV surplus charges
            b = -net
            if per == "off": b = max(b, s._offpeak_charge(st, k))
            return b
        if per == "peak": return -net                             # (2)
        if per == "mid":
            if h >= 21: return -net                               # (3a)
            reserve = sum(max(s._L(st, j) - s._PV(st, j), 0.0) for j in s._yday(k, 16, 21)) / ED
            return -min(net, max(st["soc"] - reserve, 0.0) * ED)  # (3b)
        return s._offpeak_charge(st, k)                           # (4)
    def _yday(s, k, a, b):
        # absolute indices of the most recent completed clock hours a..b-1 (yesterday or today if already past)
        out = []
        for j in range(k - 1, k - 49, -1):
            if a <= s.hour[j] < b: out.append(j)
            if len(out) == b - a: break
        return out
    def _offpeak_charge(s, st, k):
        surplus = sum(max(s._PV(st, j) - s._L(st, j), 0.0) for j in s._yday(k, 7, 16)) * EC
        target = min(CAP, max(0.0, CAP - surplus))
        return min(PMAX, (target - st["soc"]) / EC) if st["soc"] < target else 0.0

    def branches(s, st):
        k, L, PV, h = s._now(st)
        return [("hold", 0.0), ("charge_full", PMAX), ("charge_half", PMAX / 2), ("discharge_full", -PMAX),
                ("discharge_half", -PMAX / 2), ("self_consume", PV - L)]

    @staticmethod
    def _split(a):
        if isinstance(a, tuple): return float(a[0]), tuple(a[1])
        return float(a), ()
    def _clip(s, st, b):
        k, L, PV, h = s._now(st)
        if b > 0: return min(b, PMAX, (CAP - st["soc"]) / EC)
        if b < 0: return -min(-b, PMAX, st["soc"] * ED, max(L - PV, 0.0))
        return 0.0
    def valid(s, st, a):
        b, com = s._split(a); b = s._clip(st, b)
        com = tuple((int(T), float(x)) for T, x in com if st["t"] < T < min(s.T, st["t"] + s.horizon) and x != 0.0)
        return (b, com) if com else b

    def step(s, st, a):
        k, L, PV, h = s._now(st); b, com = s._split(a); net = L - PV
        n = dict(st)
        if st["commit"] or com:                                   # blocks committed to this hour land on top (clipped)
            cm = dict(st["commit"]); b = s._clip(st, b + cm.pop(st["t"], 0.0))
            for T, x in com: cm[T] = cm.get(T, 0.0) + x
            n["commit"] = cm
        n["soc"] = st["soc"] + (b * EC if b > 0 else b / ED)
        n["soc"] = min(CAP, max(0.0, n["soc"]))
        n["cost"] = st["cost"] + _grid_cost(net + b, h)
        n["nobat"] = st["nobat"] + _grid_cost(net, h)
        n["thr"] = st["thr"] + abs(b); n["t"] = st["t"] + 1
        n["hist"] = (st.get("hist", ()) + ((k, b),))[-24:]         # REAL3 v2: last 24 applied hours (read by part_objective only)
        return n

    # ---- REAL2 A: landings = 1 kWh blocks of this hour's decision
    def _blocks(s, b):
        m = abs(b); n = int(math.ceil(m - 1e-9)) if m > 1e-9 else 0
        return [min(1.0, m - i) for i in range(n)]
    def landings(s, st, a):
        b, _ = s._split(a); return list(range(len(s._blocks(b))))
    def without(s, st, a, L):
        b, com = s._split(a); bl = s._blocks(b)
        if L >= len(bl): return a
        nb = math.copysign(abs(b) - bl[L], b) if abs(b) - bl[L] > 1e-12 else 0.0
        return (nb, com) if com else nb
    def targets(s, st, a, L):
        b, _ = s._split(a)
        if b == 0.0: return []
        k = st["i0"] + st["t"]; sc = []
        for off in range(1, min(s.horizon, s.T - st["t"])):
            q = k + off; Lh = s._L(st, q - 24); Ph = s._PV(st, q - 24); p, _ = price(s.hour[q]); net = Lh - Ph
            if b < 0 and net > 0: sc.append((p * min(1.0, net), st["t"] + off))           # discharge: value of covering load
            if b > 0: sc.append((-(P_EXP if net < 0 else p), st["t"] + off))              # charge: cheapest charging hour
        sc.sort(key=lambda x: (-x[0], x[1]))
        return [T for _, T in sc[:3]]
    def retarget(s, st, a, L, T):
        b, com = s._split(a); bl = s._blocks(b)
        if L >= len(bl): return a
        nb = s.without(st, b, L)
        return (float(nb), com + ((int(T), math.copysign(bl[L], b)),))

    # ---- REAL2 C: scenario-based stochastic MPC (standard="strongest")
    def _mpc(s, st):
        k, L0, PV0, h0 = s._now(st); H = min(s.horizon, s.T - st["t"]); S = s.NSCEN
        dpv = sum(s._PV(st, i) for i in range(k - 24, k)); dcs = sum(s.cs[i] for i in range(k - 24, k))
        csi = dpv / dcs if dcs > 1e-6 else 0.0
        net = np.zeros((S, H)); net[:, 0] = L0 - PV0
        for sc in range(S):
            rng = np.random.default_rng([st["cell"], st["t"], sc, 6062]); zl = rng.standard_normal(H); zp = rng.standard_normal(H)
            for i in range(1, H):
                q = k + i
                Lq = s._L(st, q - 24) * math.exp(0.25 * zl[i] - 0.03125)
                Pq = min(s.cs[q] * 1.1, s.cs[q] * csi * math.exp(0.30 * zp[i] - 0.045))
                net[sc, i] = Lq - Pq
        # variables: c0, d0 (shared), then per scenario s, hour i: c, d, gp, gm, soc(i+1)   (c, d of hour 0 unused)
        nv_s = 5 * H; nv = 2 + S * nv_s
        def ix(sc, i, f): return 2 + sc * nv_s + 5 * i + f
        cost = np.zeros(nv); lb = np.zeros(nv); ub = np.full(nv, np.inf)
        ub[0] = ub[1] = PMAX; ub[1] = min(PMAX, max(L0 - PV0, 0.0))
        rows, cols, vals, beq = [], [], [], []; r = 0
        for sc in range(S):
            for i in range(H):
                p, _ = price(s.hour[k + i])
                cI = 0 if i == 0 else ix(sc, i, 0); dI = 1 if i == 0 else ix(sc, i, 1)
                if i == 0: ub[ix(sc, 0, 0)] = ub[ix(sc, 0, 1)] = 0.0
                else:
                    ub[cI] = PMAX; ub[dI] = min(PMAX, max(net[sc, i], 0.0))
                    cost[cI] += LAMBDA / S; cost[dI] += LAMBDA / S
                gp, gm, so = ix(sc, i, 2), ix(sc, i, 3), ix(sc, i, 4)
                cost[gp] = p / S; cost[gm] = -P_EXP / S; ub[so] = CAP
                rows += [r] * 4; cols += [gp, gm, cI, dI]; vals += [1, -1, -1, 1]; beq.append(net[sc, i]); r += 1
                rows += [r, r, r]; cols += [so, cI, dI]; vals += [1, -EC, 1 / ED]
                if i == 0: beq.append(st["soc"])
                else: rows.append(r); cols.append(ix(sc, i - 1, 4)); vals.append(-1); beq.append(0.0)
                r += 1
            cost[ix(sc, H - 1, 4)] -= ED * P_OFF / S
        cost[0] += LAMBDA; cost[1] += LAMBDA
        A = sp.csr_matrix((vals, (rows, cols)), shape=(r, nv))
        res = linprog(cost, A_eq=A, b_eq=np.array(beq), bounds=np.column_stack([lb, ub]), method="highs")
        if res.status != 0: return s._rule(st)
        return float(res.x[0] - res.x[1])

    # ---- REAL3: library primitives, frame levers, coupling (seed3); read only by seed3, earlier modes unchanged
    SOC_GRID = np.linspace(0.0, CAP, 55)                          # 0.25 kWh
    B_GRID = np.linspace(-PMAX, PMAX, 81)                         # 0.125 kWh
    NDAYS = 7
    def _past_nets(s, st, k, H):
        """Real-past scenario tree: for hour offset i >= 1 the net loads of the same clock hour on the last NDAYS days
        (index q - 24 d < k: data up to now only); hour 0 is observed."""
        nd = min(s.NDAYS, k // 24); out = np.zeros((nd, H))     # never before the series start
        for d in range(1, nd + 1):
            for i in range(H):
                q = k + i; j = q - 24 * d
                out[d - 1, i] = s._L(st, j) - s._PV(st, j)
        return out
    def _stage(s, hour, net, Vn, soc_from):
        """min over the b grid of stage cost + interpolated next value, for one net value; soc_from (G,) -> (G,), argmin."""
        p, _ = price(hour); b = s.B_GRID[None, :]
        nxt = soc_from[:, None] + np.where(b > 0, b * EC, b / ED)
        ok = (nxt >= -1e-9) & (nxt <= CAP + 1e-9) & (-b <= max(net, 0.0) + 1e-9)
        g = net + b; c = np.where(g > 0, p * g, P_EXP * g) + LAMBDA * np.abs(b)
        tot = c + np.interp(np.clip(nxt, 0, CAP), s.SOC_GRID, Vn)
        tot = np.where(ok, tot, np.inf); a = tot.argmin(1)
        return tot[np.arange(len(soc_from)), a], s.B_GRID[a]
    def _soc_dp(s, st, paths=False):
        """P5 (value carried back): SOC dynamic programming over the real-past scenario tree, horizon min(24, T - t).
        paths=False: recombining tree (stage-wise independent: each hour's net is one of the NDAYS past values, decided
        after it is observed: non-anticipative at every hour). paths=True (frame lever F:coupled_hours): each past day
        is one whole path (the hours of one day drive each other: a dull day stays dull), two-stage: non-anticipative
        at hour 0 only. Stage cost = the result exactly (grid $ + wear); terminal value = stored energy x ED x P_OFF."""
        k, L0, PV0, h0 = s._now(st); H = min(s.horizon, s.T - st["t"])
        nets = s._past_nets(st, k, H); G = s.SOC_GRID
        Vend = -G * ED * P_OFF
        if paths:
            V1 = np.zeros(len(G)); nd = len(nets)
            for d in range(nd):
                V = Vend
                for i in range(H - 1, 0, -1): V, _ = s._stage(s.hour[k + i], nets[d, i], V, G)
                V1 += V / nd
        else:
            V1 = Vend
            for i in range(H - 1, 0, -1):
                V1 = np.mean([s._stage(s.hour[k + i], nets[d, i], V1, G)[0] for d in range(len(nets))], axis=0)
        _, b = s._stage(h0, L0 - PV0, V1, np.array([st["soc"]]))
        return float(b[0])
    def _rule_wear(s, st):
        """P2 (price on harm): the rule with the wear priced into its thresholds. A grid kWh charged off-peak and
        delivered later costs (P_OFF + LAMBDA (1 + RTE)) / RTE = $0.239 > the mid price $0.22: it pays only at peak. So
        off-peak charging stops at the energy the coming peak needs (yesterday's 16-21 deficit / ED, capped by the
        room left for tomorrow's PV), and the 21-23 discharge only uses energy above tonight's charge target (energy that
        would be refilled at $0.189/kWh delivered costs more than the $0.17 it saves after wear). PV surplus and peak
        rules are unchanged (PV kWh stored: (P_EXP + 1.9 LAMBDA) / 0.9 = $0.15 < $0.22)."""
        k, L, PV, h = s._now(st); net = L - PV; _, per = price(h)
        need = sum(max(s._L(st, j) - s._PV(st, j), 0.0) for j in s._yday(k, 16, 21)) / ED
        surplus = sum(max(s._PV(st, j) - s._L(st, j), 0.0) for j in s._yday(k, 7, 16)) * EC
        target = min(CAP, max(0.0, CAP - surplus), need)
        def charge(): return min(PMAX, (target - st["soc"]) / EC) if st["soc"] < target else 0.0
        if net < 0:
            b = -net
            if per == "off": b = max(b, charge())
            return b
        if per == "peak": return -net
        if per == "mid":
            floor = target if h >= 21 else need
            return -min(net, max(st["soc"] - floor, 0.0) * ED)
        return charge()
    def primitives(s, st):
        return [("P2", "P2:price_on_wear", s._rule_wear(st)),
                ("P4P5", "P4P5:scenario_mpc", s._mpc(st)),
                ("P5", "P5:soc_dp_realpast_tree", s._soc_dp(st))]
    def frame(s, st):
        return [("F:coupled_hours", "F:coupled_hours:realpast_day_paths", s._soc_dp(st, paths=True))]
    def coupled(s, st): return True       # hours drive each other through the state of charge: land the action whole

    # ---- REAL3 v2 hooks (read only by seed3.run(..., "seed3"); REAL1/REAL2 and seed3v1 never call them)
    PARTS = ("pv", "grid", "load")
    def _comp(s, st, a):
        """The hour's decision split into its three energy streams (kWh this hour): pv = PV surplus stored, grid = energy
        charged from the grid (on top of the PV surplus: a charge takes the surplus first), load = net load covered by
        discharge. One battery: a charge and a discharge cannot coexist in one hour."""
        b = s._clip(st, s._split(a)[0]); k, L, PV, h = s._now(st); sur = max(PV - L, 0.0)
        pv = min(max(b, 0.0), sur)
        return {"pv": pv, "grid": max(b, 0.0) - pv, "load": max(-b, 0.0)}
    def parts(s, st): return list(s.PARTS)
    def merge(s, st, d):
        """Each named part's stream taken from its action, the unnamed parts' streams from the standard; dict order =
        who gets the hour's 5 kW first; the first part with a non-zero stream sets the direction (charge or discharge),
        streams in the other direction are dropped (one battery). Commitments of the named actions are kept."""
        std = s._comp(st, s.default(st)); amt = {}; com = ()
        for p, a in d.items(): amt[p] = s._comp(st, a)[p]; com += s._split(a)[1]
        order = list(d) + [p for p in s.PARTS if p not in d]
        room, sign, b = PMAX, 0, 0.0
        for p in order:
            x = amt.get(p, std[p])
            if x <= 1e-12: continue
            sg = -1 if p == "load" else 1
            if sign == 0: sign = sg
            if sg != sign: continue
            take = min(x, room); room -= take; b += sg * take
        return (b, com) if com else b
    def _need(s, st, k):
        return sum(max(s._L(st, j) - s._PV(st, j), 0.0) for j in s._yday(k, 16, 21)) / ED
    def part_objective(s, st, p):
        """The stream's own value now, in [0, 1] (higher = better), from data up to now:
        pv   = share of the last 24 h PV surplus that was stored (1 if there was none);
        load = share of the last 24 h priced (mid / peak) net load covered by the battery, weighted by price (1 if none);
        grid = readiness for the coming peak: stored energy deliverable / the peak need (yesterday's 16-21 deficit)."""
        k = st["i0"] + st["t"]
        if p == "grid":
            need = s._need(st, k) * ED
            return 1.0 if need <= 1e-9 else min(1.0, st["soc"] * ED / need)
        num = den = 0.0
        for j, b in st.get("hist", ()):
            net = s._L(st, j) - s._PV(st, j)
            if p == "pv" and net < 0: num += min(max(b, 0.0), -net); den += -net
            if p == "load" and net > 0:
                pr, per = price(s.hour[j])
                if per != "off": num += pr * min(max(-b, 0.0), net); den += pr * net
        return 1.0 if den <= 1e-9 else num / den
    def focus(s, st, p):
        """The hour's whole power on one stream: pv = store all the PV surplus; grid = charge at 5 kW; load = discharge
        to cover the whole net load (valid() clips to 5 kW, energy and no-export)."""
        k, L, PV, h = s._now(st)
        if p == "pv": return max(PV - L, 0.0)
        if p == "grid": return PMAX
        return -max(L - PV, 0.0)
    def _cap(s, st, p):
        k, L, PV, h = s._now(st); sur = max(PV - L, 0.0); room = (CAP - st["soc"]) / EC
        if p == "pv": return min(PMAX, sur, room)
        if p == "grid": return max(0.0, min(PMAX, room) - min(PMAX, sur, room))
        return min(PMAX, st["soc"] * ED, max(L - PV, 0.0))
    def map_part(s, st, a, pf, pt):
        """RE-HOST: the stream a puts on pf, as a share of pf's capacity this hour, put on pt at the same share."""
        cf = s._cap(st, pf); x = s._comp(st, a)[pf]; share = x / cf if cf > 1e-9 else 0.0
        y = share * s._cap(st, pt); k, L, PV, h = s._now(st)
        if pt == "pv": return y
        if pt == "grid": return max(PV - L, 0.0) + y
        return -y
    def joint(s, st):
        k, L, PV, h = s._now(st)
        return [("self_consume", PV - L)]     # one move serving pv (stores the surplus) and load (covers the deficit)
    def carry(s, st, a):
        """CARRY: the hour's unused power in a's direction is committed to the next hour (REAL2 commitment, landing on top
        of the next hour's action, clipped there to the same 5 kW / energy / no-export limits). Direction: a's; for a
        hold, charge when there is PV surplus or off-peak, else discharge."""
        b, com = s._split(s.valid(st, a)); k, L, PV, h = s._now(st)
        if st["t"] + 1 >= s.T: return a
        sg = (1 if b > 0 else -1) if b != 0 else (1 if (PV > L or price(h)[1] == "off") else -1)
        left = PMAX - abs(b)
        if left <= 1e-9: return a
        return (b, com + ((st["t"] + 1, sg * left),))
    def shape(s, st):
        """Hour-of-day, price period, state-of-charge band (quarters of capacity), PV surplus now (the hourly pattern key)."""
        k, L, PV, h = s._now(st)
        return (h, price(h)[1], min(4, int(st["soc"] / (CAP / 4))), PV > L)
    OPMAP = {"hold": "carry", "charge_full": "beam", "charge_half": "beam", "discharge_full": "beam",
             "discharge_half": "beam", "self_consume": "fuse", "F:coupled_hours": "zoom"}
    def op_of(s, fam): return s.OPMAP.get(fam)

    def fork(s, st, j):
        k = st["i0"] + st["t"]; key = (st["cell"], st["t"], j)
        if key not in s._cache:
            if len(s._cache) > 64: s._cache.clear()
            rng = np.random.default_rng([st["cell"], st["t"], j, 6061])
            n0 = s.horizon + 2; n = 2 * s.horizon + 2              # REAL3 v2: forks reach 2H (Eagle room, ZOOM 2H)
            Lf = [s.load[k]]; Pf = [s.pv[k]]                      # the current hour is observed in real time
            dpv = sum(s.pv[i] for i in range(k - 24, k)); dcs = sum(s.cs[i] for i in range(k - 24, k))
            csi = dpv / dcs if dcs > 1e-6 else 0.0
            zl = rng.standard_normal(n0); zp = rng.standard_normal(n0)
            # the extension is drawn AFTER the first n0 draws: the first H + 2 hours of every fork are unchanged bit for bit
            zl = np.concatenate([zl, rng.standard_normal(n - n0)]); zp = np.concatenate([zp, rng.standard_normal(n - n0)])
            for i in range(1, n):
                q = k + i
                if q >= len(s.load): break
                prev = Lf[i - 24] if i - 24 >= 0 else s.load[q - 24]  # persistence; never a value after k
                Lf.append(prev * math.exp(0.25 * zl[i] - 0.03125))
                Pf.append(min(s.cs[q] * 1.1, s.cs[q] * csi * math.exp(0.30 * zp[i] - 0.045)))
            s._cache[key] = (Lf, Pf, k)
        f = dict(st); f["src"] = s._cache[key]; return f

    def _saved(s, st):
        return st["nobat"] - st["cost"] + (st["soc"] - st["soc0"]) * ED * P_OFF
    def _result(s, st): return s._saved(st) - LAMBDA * st["thr"]       # net $ saved after the wear cost
    def objective(s, st): return s._result(st)                         # = the result exactly (rule 4)
    def report(s, st): return {"result": s._result(st), "resource": st["thr"], "saved_gross": s._saved(st),
                               "cost_battery": st["cost"], "cost_no_battery": st["nobat"]}
