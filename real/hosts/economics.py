"""REAL1 row 7, ECONOMICS: multi-item inventory under a weekly capital budget, on real Walmart department demand.

REAL DATA
  Walmart Recruiting "Store Sales Forecasting" (Kaggle), store 1, 7 departments (1, 3, 8, 13, 38, 93, 95), 143 weeks
  2010-02-05 .. 2012-10-26, Weekly_Sales (USD). Shipped in the pip package pytimetk (datasets/walmart_sales_weekly.csv);
  fetched by economics_fetch.py from its GitHub source, sha256-checked. Demand unit = $1000 of retail sales.
  Proxy: realised sales are used as demand (true demand behind past stock-outs is not observable; usual practice).
DOCUMENTED PARAMETERS (fixed here, before any run)
  Price p = 1 per unit (retail value), unit cost c = 0.75 (25 % gross margin, about Walmart's reported gross margin),
  lost sales (no backorders), lead time 1 week (order placed in week t arrives for week t+1), weekly review.
  Carrying rate 25 %/year on capital at cost (h = 0.25/52 per $-week).
  Capital budget per week B = c x mean weekly total demand of the 52 weeks before the episode (the store's average
  purchase need): it binds when demand peaks or safety stocks rise; valid() scales an order down to B.
MEASURE
  (rule 4 as fixed 13:45: objective = the result only; the resource is a constraint; pass = Pareto win per cell)
  result   = profit after carrying cost over the episode in $k: revenue - purchases + c x (end stock - start stock)
             (stock at cost, so ending with more or less stock gives no gain) - h x capital-weeks. The carrying cost
             is part of the real money result.
  resource = capital tied up: mean over weeks of c x (stock on hand + stock in transit), $k. Budget: the same weekly
             capital budget B for every action (valid()).
  objective(state) = result so far, exactly (no division, no bonus). report also gives gross_profit.
  Also reported: fill rate (units sold / units demanded) as the service level.
STANDARD METHOD (default)
  Periodic-review base-stock (order-up-to) policy (Silver, Pyke & Peterson, "Inventory Management and Production
  Planning and Scheduling", ch. 7; Axsaeter, "Inventory Control"): S_i = (L+R) mu_i + z sigma_i sqrt(L+R), L = R = 1,
  mu_i, sigma_i = mean and sd of the last 13 weeks of demand (data up to now), z from the newsvendor critical ratio
  (p-c)/(p-c+h) = 0.986 -> z = 2.19; order S_i - stock_i. If the orders exceed the budget, all are scaled by the same
  factor (proportional / fair-share rationing).
OWN FUTURE (fork, layer-1 rule)
  Demand from the current week on is a forecast from data up to now: seasonal naive (same week 52 weeks earlier) x
  level ratio (last 8 weeks / the same 8 weeks a year earlier, per item) x lognormal noise (sigma 0.15); rng seeded from
  (cell, t, j, 7071). The current week's demand is not known when the order is placed (in the fork it is forecast too).
BRANCHES (same budget, valid() enforces it)
  focused: prebuild (order up to the seasonal-naive forecast of weeks t..t+1 + safety), lean (base-stock with z = 0),
  focus_big / focus_small (fund the base-stock orders of the 3 largest / 4 smaller departments first, the rest from what
  is left), focus_short (budget to the items with the largest forecast shortfall first);
  coupled: pair (the two departments whose demands are most correlated in the last 52 weeks get prebuild orders first,
  together; the rest base-stock).
SIZE (rule 5)  episode T = 26 weeks (half a year), horizon 8 weeks (two months: long enough to pre-build for a holiday),
  samples 3; ~11 candidates x 2 continuations x 3 forks x 9 weeks ~ 600 model steps per decision; a few seconds per
  episode here. Cells: start week drawn by rng(cell) in [60, 143 - 26] (60 weeks of history needed); dev cells 1..4.
REAL2 A. LANDINGS (Law 4, seed.land)
  A landing = one order unit on one item: the marginal block of u = 2.5 % of the weekly capital budget (in retail
  units, about $9k; the whole order of the item if it is smaller) on the top of item i's order; ids = the items with a
  positive order (at most 7). without(L) = the order with that unit not bought (less capital). targets(L) = up to 3
  other items with the largest positive forecast shortfall for the weeks the order covers (seasonal-naive forecast of
  weeks t..t+1 + z x sd - stock - order; data up to now, the host's own model). retarget(L, T) = the unit moved from
  item L to item T (same capital).
REAL2 C. STRONGEST METHOD (standard="strongest")
  Stochastic inventory optimisation with the capital budget: scenario-based two-stage stochastic LP in receding horizon
  (Birge & Louveaux, "Introduction to Stochastic Programming", ch. 1-3; Shapiro, Dentcheva & Ruszczynski, "Lectures on
  Stochastic Programming", ch. 1 (multi-item newsvendor with budget) ; rolling-horizon scenario inventory control as in
  e.g. Bertsimas & Thiele 2006 OR 54(1):150 for the robust counterpart). Every week: S = 30 demand scenarios of the
  next min(8, T - t) weeks from the SAME forecast model as the own future (seasonal naive x level ratio x lognormal
  0.15; data up to now only; rng from (cell, t, scenario, 7072), independent of the forks and of the real data). One
  LP (scipy.optimize.linprog, HiGHS): per scenario, week and item: order, sales (<= stock, <= demand: lost sales) and
  stock; this week's order is shared by all scenarios (non-anticipative), later orders are per-scenario recourse;
  every week's orders <= the capital budget B / c. Objective = the result exactly: revenue - purchases - carrying
  (h x capital tied up at cost after the order) + terminal stock at cost. The first week's orders are placed (lead
  time 1); re-solved every week. It replaces both the order-up-to levels and the fair-share rationing of the
  base-stock rule by one joint optimum under the budget.
REAL3 (seed3 binding; read only by seed3.run, the REAL1/REAL2 modes give identical numbers)
  primitives(state): P4P5 "stochastic_lp" = the strongest method's action (the LP above) as one candidate; valued in the
    forks by its own first order, the forks continue with the base-stock rule (no LP inside forks).
  frame(state):
    F:pool "capital_newsvendor": RELATION between items through the shared capital: multi-item newsvendor with one
      budget (Lagrangian shadow price by bisection) instead of proportional rationing.
    F:otrace "pool_corrected" / "lp_corrected": O trace of demand surprises: per item, log(realised / seasonal-naive
      forecast) of every past week (forecast from data before that week), AR(1) slope per item from that history
      clipped to [0, 1], forecast x exp(phi x last surprise); fed into the pooled newsvendor and into the same LP.
  WHAT THE WALMART DATA SUPPORT (measured on store 1, weeks 60..142, one-week-ahead surprises): substitution between
    departments is NOT identifiable (weekly sales only: no stock-outs, prices or assortment changes; the 7 departments
    are distinct categories), so no substitution lever is built. Cross-department surprise correlation is weak (mean
    pairwise 0.09; largest 0.43, dept 93 with 95), so no risk pooling across items (a unit of one department cannot
    serve another's demand). What the data do support: the shared capital budget (capital pooling) and persistence of
    surprises in some items (lag-1 autocorrelation 0.57 dept 1, 0.31 depts 3 and 8, ~0 for the others).
  coupled(state) = True when the base-stock orders exceed the budget (items then drive each other through the capital:
    the seed lands the action whole); otherwise False (per-item landing, Law 1).
REAL3 v2 HOOKS (25 Nov; real/HOST_INTERFACE_REAL3v2.md; read only by seed3.run(..., "seed3"))
  parts = the 7 departments (no sub-parts: weekly sales per department only; ENTER depth 1).
  merge = each named department's order from its action, funded in dict order from the week's budget; the others take
    the base-stock order rationed on what is left. part_objective = the department's forecast fill rate this week from
    stock on hand (stock / seasonal-naive forecast, capped at 1). focus = the week's capital on one department's
    pre-build order, nothing elsewhere. map_part = the same weeks of forecast cover on the target department.
  joint = the correlated pair pre-built together, and the capital-pooled newsvendor (one budget serving all items).
  carry = open-to-buy carry-over: the action ("carry", q) banks the week's unspent capital (bank <= B; later weeks may
    spend B + bank; state key "bank", absent unless carry is used, so REAL1/REAL2 states and numbers are unchanged).
  shape = (demand band: forecast / 13-week mean <0.9 | <1.15 | else; stock band: stock / forecast <1 | <1.5 | <2 | else;
    budget binding). op_of: focus_* -> beam; pair, F:pool -> fuse; prebuild -> zoom (a 2-week block); lean -> contain;
    F:otrace -> heal (counter-shift by the last surprise); P4P5 by the seed's table (fuse).
"""
import math, os
import numpy as np, pandas as pd
import scipy.sparse as sp
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "data", "walmart_sales_weekly.csv")
P, C = 1.0, 0.75
H_RATE = 0.25 / 52
Z = 2.19        # Phi^-1((p-c)/(p-c+h)), h = c * 0.25/52  -> CR = 0.25/0.25361 = 0.9858
SIG_F = 0.15

class Economics:
    horizon = 8; samples = 3
    NSCEN = 30; UNIT = 0.025
    def __init__(s, T=26, standard="base_stock"):
        s.T = T; s.standard = standard
        if not os.path.exists(CSV): raise SystemExit("run real/hosts/economics_fetch.py first")
        d = pd.read_csv(CSV)
        w = d.pivot(index="Date", columns="Dept", values="Weekly_Sales").sort_index() / 1000.0
        s.depts = list(w.columns); s.N = len(s.depts)
        s.D = np.maximum(w.values, 0.0)                                  # weeks x items
        s._cache = {}

    def _d(s, st, k):
        f = st["src"]
        return f[0][k - f[1]] if (f is not None and k >= f[1]) else s.D[k]
    def _hist(s, st, k, n):
        return np.array([s._d(st, j) for j in range(k - n, k)])

    def reset(s, cell):
        rng = np.random.default_rng([int(cell), 7070])
        w0 = int(rng.integers(60, len(s.D) - s.T + 1))
        B = C * float(s.D[w0 - 52:w0].sum(axis=1).mean())
        st = {"cell": int(cell), "w0": w0, "t": 0, "B": B, "src": None, "rev": 0.0, "buy": 0.0, "capw": 0.0,
              "sold": 0.0, "dem": 0.0}
        st["stock"] = s._S(st, Z); st["stock0"] = st["stock"].copy()
        return st
    def done(s, st): return st["t"] >= s.T

    def _S(s, st, z):
        k = st["w0"] + st["t"]; h = s._hist(st, k, 13)
        return 2.0 * h.mean(0) + z * h.std(0, ddof=1) * math.sqrt(2.0)
    def _fc(s, st, k, n):
        """Seasonal-naive forecast of weeks k..k+n-1 from data before k only (deterministic part of the own model)."""
        lvl = s._hist(st, k, 8).sum(0) / np.maximum(s.D[k - 60:k - 52].sum(0), 1e-9)
        return np.array([s.D[k + i - 52] for i in range(n)]) * lvl
    def _ration(s, st, q, first=None):
        q = np.maximum(np.asarray(q, float), 0.0); B = st["B"] / C
        if first is None:
            return q * min(1.0, B / q.sum()) if q.sum() > 0 else q
        out = np.zeros(s.N); m = np.zeros(s.N, bool); m[list(first)] = True
        a = q * m; out += a * min(1.0, B / a.sum()) if a.sum() > 0 else 0
        left = B - out.sum(); r = q * ~m
        if r.sum() > 0 and left > 0: out += r * min(1.0, left / r.sum())
        return out

    def default(s, st):
        if s.standard == "strongest": return s._sp(st)
        return s._ration(st, np.maximum(s._S(st, Z) - st["stock"], 0.0))

    def branches(s, st):
        k = st["w0"] + st["t"]; h13 = s._hist(st, k, 13)
        sd = h13.std(0, ddof=1) * math.sqrt(2.0)
        base = np.maximum(s._S(st, Z) - st["stock"], 0.0)
        pre = np.maximum(s._fc(st, k, 2).sum(0) + Z * sd - st["stock"], 0.0)
        lean = np.maximum(s._S(st, 0.0) - st["stock"], 0.0)
        mu = h13.mean(0); big = list(np.argsort(-mu)[:3]); small = list(np.argsort(-mu)[3:])
        short = np.argsort(-(pre / np.maximum(mu, 1e-9)))
        h52 = s._hist(st, k, 52); cc = np.corrcoef(h52.T); np.fill_diagonal(cc, -2)
        i, j = np.unravel_index(int(np.argmax(cc)), cc.shape)
        pair = base.copy(); pair[[i, j]] = pre[[i, j]]
        return [("prebuild", s._ration(st, pre)), ("lean", s._ration(st, lean)),
                ("focus_big", s._ration(st, base, big)), ("focus_small", s._ration(st, base, small)),
                ("focus_short", s._ration(st, pre, list(short[:3]))),
                ("pair", s._ration(st, pair, [int(i), int(j)]))]

    def valid(s, st, a):
        if isinstance(a, tuple) or st.get("bank", 0.0) > 0.0: return s._valid3(st, a)    # REAL3 v2 carry only
        return s._ration(st, a)

    # ---- REAL2 A: landings = one order unit on one item
    def _u(s, st): return s.UNIT * st["B"] / C
    def landings(s, st, a): a = s._q(a); return [i for i in range(s.N) if a[i] > 1e-9]
    def without(s, st, a, L):
        q = np.array(s._q(a), float); q[L] = max(0.0, q[L] - s._u(st)); return s._re(a, q)
    def targets(s, st, a, L):
        k = st["w0"] + st["t"]; sd = s._hist(st, k, 13).std(0, ddof=1) * math.sqrt(2.0)
        need = s._fc(st, k, 2).sum(0) + Z * sd - st["stock"] - np.asarray(s._q(a), float)
        return [int(i) for i in np.argsort(-need) if int(i) != L and need[i] > 0][:3]
    def retarget(s, st, a, L, T):
        q = np.array(s._q(a), float); m = min(q[L], s._u(st)); q[L] -= m; q[T] += m; return s._re(a, q)

    # ---- REAL2 C: scenario-based stochastic LP with the capital budget (standard="strongest")
    def _sp(s, st):
        k = st["w0"] + st["t"]; H = min(s.horizon, s.T - st["t"]); S = s.NSCEN; N = s.N
        if H < 2: return np.zeros(N)                         # an order placed in the last week arrives after the end
        base = s._fc(st, k, H)
        dem = np.empty((S, H, N))
        for sc in range(S):
            rng = np.random.default_rng([st["cell"], st["t"], sc, 7072])
            dem[sc] = base * np.exp(SIG_F * rng.standard_normal((H, N)) - SIG_F ** 2 / 2)
        # variables: q0[N] shared; per scenario s, week i: q (i >= 1), y (sales), x (stock after the week's order)
        nv_s = 3 * H * N; nv = N + S * nv_s
        def ix(sc, i, f, n): return N + sc * nv_s + (i * 3 + f) * N + n
        cost = np.zeros(nv); ub = np.full(nv, np.inf); lb = np.zeros(nv)
        cost[:N] = C                                         # minimise -(result)
        Ar, Ac, Av, beq = [], [], [], []; Ur, Uc, Uv, bub = [], [], [], []; r = 0; ru = 0
        Bu = st["B"] / C
        for n in range(N): Ur.append(ru); Uc.append(n); Uv.append(1.0)
        bub.append(Bu); ru += 1
        for sc in range(S):
            for i in range(H):
                for n in range(N):
                    qI = n if i == 0 else ix(sc, i, 0, n); y = ix(sc, i, 1, n); x = ix(sc, i, 2, n)
                    if i == 0: ub[ix(sc, 0, 0, n)] = 0.0
                    else: cost[qI] += C / S
                    ub[y] = dem[sc, i, n]; cost[y] = -P / S
                    cost[x] += H_RATE * C / S
                    # x_i = x_{i-1} - y_i + q_i   (x_{-1} = stock now);  y_i <= x_{i-1}
                    Ar += [r, r, r]; Ac += [x, y, qI]; Av += [1.0, 1.0, -1.0]
                    if i == 0: beq.append(float(st["stock"][n])); ub[y] = min(ub[y], float(st["stock"][n]))
                    else:
                        Ar.append(r); Ac.append(ix(sc, i - 1, 2, n)); Av.append(-1.0); beq.append(0.0)
                        Ur += [ru, ru]; Uc += [y, ix(sc, i - 1, 2, n)]; Uv += [1.0, -1.0]; bub.append(0.0); ru += 1
                    r += 1
                if i >= 1:
                    for n in range(N): Ur.append(ru); Uc.append(ix(sc, i, 0, n)); Uv.append(1.0)
                    bub.append(Bu); ru += 1
            for n in range(N): cost[ix(sc, H - 1, 2, n)] -= C / S      # terminal stock at cost
        A = sp.csr_matrix((Av, (Ar, Ac)), shape=(r, nv)); U = sp.csr_matrix((Uv, (Ur, Uc)), shape=(ru, nv))
        res = linprog(cost, A_ub=U, b_ub=np.array(bub), A_eq=A, b_eq=np.array(beq),
                      bounds=np.column_stack([lb, ub]), method="highs")
        if res.status != 0: return s._ration(st, np.maximum(s._S(st, Z) - st["stock"], 0.0))
        return np.maximum(res.x[:N], 0.0)

    # ---- REAL3: library primitives, frame levers, coupling (seed3); read only by seed3, earlier modes unchanged
    def _surprises(s, st, k):
        """O trace: log(realised / seasonal-naive forecast) of every past week j in [60, k) (forecast from data before j)."""
        return np.array([np.log(np.maximum(s._d(st, j), 1e-6) / np.maximum(s._fc(st, j, 1)[0], 1e-6))
                         for j in range(60, k)]).reshape(-1, s.N)
    def _otrace_factor(s, st, k):
        """Forecast correction from recent errors (data up to now): per item AR(1) on its own surprise history,
        phi_i = lag-1 regression slope clipped to [0, 1] (0 with fewer than 8 surprises); factor = exp(phi_i x last
        surprise). Items whose surprises do not persist get phi ~ 0 (no correction)."""
        sv = s._surprises(st, k)
        if len(sv) < 8: return np.ones(s.N)
        x, y = sv[:-1], sv[1:]; xc = x - x.mean(0)
        phi = np.clip((xc * (y - y.mean(0))).sum(0) / np.maximum((xc ** 2).sum(0), 1e-12), 0.0, 1.0)
        return np.exp(phi * sv[-1])
    def _pool(s, st, corr=None):
        """RELATION through the shared capital (capital pooling): the multi-item newsvendor with one budget (Lagrangian:
        Hadley & Whitin 1963 ch. 2; Silver, Pyke & Peterson ch. 7 'budget constraint'). Target x_i = mu_i + sigma_i
        Phi^-1(1 - (h + lam) / (p - c)), lam >= 0 the budget's shadow price found by bisection so the orders fit B;
        capital goes where the marginal expected margin is highest instead of the base stock's proportional cut.
        mu = seasonal-naive forecast of weeks t..t+1 (x the O-trace factor if given), sigma = 13-week sd x sqrt 2."""
        from scipy.stats import norm
        k = st["w0"] + st["t"]; sd = s._hist(st, k, 13).std(0, ddof=1) * math.sqrt(2.0)
        mu = s._fc(st, k, 2) * (corr if corr is not None else 1.0); mu = mu.sum(0)
        h = H_RATE * C; Bu = st["B"] / C
        def q(lam):
            cr = 1.0 - (h + lam) / (P - C)
            if cr <= 0: return np.zeros(s.N)
            return np.maximum(mu + sd * norm.ppf(min(cr, 1 - 1e-9)) - st["stock"], 0.0)
        if q(0.0).sum() <= Bu: return q(0.0)
        lo, hi = 0.0, P - C - h
        for _ in range(50):
            m = 0.5 * (lo + hi)
            if q(m).sum() > Bu: lo = m
            else: hi = m
        return q(hi)
    def _sp_corr(s, st, corr):
        """The stochastic LP with the O-trace-corrected forecast (same LP, same scenario rng; base forecast x factor)."""
        fc0 = s._fc
        s._fc = lambda st_, k, n: fc0(st_, k, n) * (corr if k == st_["w0"] + st_["t"] else 1.0)
        try: return s._sp(st)
        finally: s._fc = fc0
    def primitives(s, st):
        return [("P4P5", "P4P5:stochastic_lp", s._sp(st))]
    def frame(s, st):
        k = st["w0"] + st["t"]; corr = s._otrace_factor(st, k)
        return [("F:pool", "F:pool:capital_newsvendor", s._pool(st)),
                ("F:otrace", "F:otrace:pool_corrected", s._pool(st, corr)),
                ("F:otrace", "F:otrace:lp_corrected", s._sp_corr(st, corr))]
    def coupled(s, st):
        """Items drive each other only through the shared capital: coupled when the base-stock orders exceed the budget."""
        return float(np.maximum(s._S(st, Z) - st["stock"], 0.0).sum()) > st["B"] / C

    # ---- REAL3 v2 hooks (read only by seed3.run(..., "seed3"); REAL1/REAL2 and seed3v1 never call them).
    # An action is the order vector q, or ("carry", q) = q with the week's unspent capital banked for later weeks.
    @staticmethod
    def _q(a): return a[1] if isinstance(a, tuple) else a
    @staticmethod
    def _re(a, q): return ("carry", q) if isinstance(a, tuple) else q
    def _bu(s, st): return (st["B"] + st.get("bank", 0.0)) / C           # this week's budget in units (B + bank)
    def _valid3(s, st, a):
        q = np.maximum(np.asarray(s._q(a), float), 0.0); Bu = s._bu(st)
        q = q * min(1.0, Bu / q.sum()) if q.sum() > 0 else q
        return s._re(a, q)
    def parts(s, st): return list(range(s.N))                            # the 7 departments
    def merge(s, st, d):
        """Each named department's order from its action, in dict order = who is funded first from this week's budget;
        the unnamed departments take the standard (base-stock) order, rationed proportionally on what is left."""
        q = np.zeros(s.N); left = s._bu(st); std = np.maximum(s._S(st, Z) - st["stock"], 0.0)
        for p, a in d.items():
            x = min(max(float(np.asarray(s._q(a), float)[p]), 0.0), left); q[p] = x; left -= x
        rest = [i for i in range(s.N) if i not in d]; r = std[rest]
        if r.sum() > 0 and left > 0: q[rest] = r * min(1.0, left / r.sum())
        return q
    def _fc1(s, st):
        k = st["w0"] + st["t"]; return np.maximum(s._fc(st, k, 1)[0], 1e-9)
    def part_objective(s, st, p):
        """The department's forecast fill rate this week from stock on hand (stock / seasonal-naive forecast, capped at 1;
        the order placed now arrives next week)."""
        return float(min(1.0, st["stock"][p] / s._fc1(st)[p]))
    def _pre(s, st):
        k = st["w0"] + st["t"]; sd = s._hist(st, k, 13).std(0, ddof=1) * math.sqrt(2.0)
        return np.maximum(s._fc(st, k, 2).sum(0) + Z * sd - st["stock"], 0.0)
    def focus(s, st, p):
        """The week's whole capital on one department: its pre-build order (forecast of weeks t..t+1 + z sd - stock),
        up to the budget; the other departments order nothing."""
        q = np.zeros(s.N); q[p] = min(s._pre(st)[p], s._bu(st)); return q
    def map_part(s, st, a, pf, pt):
        """RE-HOST: the order on pf expressed as weeks of forecast demand, the same weeks of cover ordered for pt."""
        fc = s._fc1(st); q = np.zeros(s.N); q[pt] = float(np.asarray(s._q(a), float)[pf]) / fc[pf] * fc[pt]; return q
    def joint(s, st):
        """Native joint orders (one order serving several departments through the shared capital): the pair of most
        correlated departments pre-built together, and the capital-pooled newsvendor over all departments."""
        br = dict(s.branches(st)); return [("pair", br["pair"]), ("capital_pool", s._pool(st))]
    def carry(s, st, a):
        """CARRY (open-to-buy carry-over): a, with the week's unspent capital banked for the next weeks (bank <= one
        week's budget B; later weeks may spend B + bank)."""
        return ("carry", np.asarray(s._q(s.valid(st, a)), float))
    def shape(s, st):
        """Demand band (forecast this week / 13-week mean, total), stock band (stock / forecast this week, total) and
        whether the base-stock orders exceed the budget."""
        k = st["w0"] + st["t"]; fc = s._fc1(st); mu = s._hist(st, k, 13).mean(0)
        dr = fc.sum() / max(mu.sum(), 1e-9); cov = st["stock"].sum() / fc.sum()
        db = 0 if dr < 0.9 else (1 if dr < 1.15 else 2)
        sb = 0 if cov < 1.0 else (1 if cov < 1.5 else (2 if cov < 2.0 else 3))
        return (db, sb, bool(s.coupled(st)))
    OPMAP = {"focus_big": "beam", "focus_small": "beam", "focus_short": "beam", "pair": "fuse", "prebuild": "zoom",
             "lean": "contain", "F:pool": "fuse", "F:otrace": "heal"}
    def op_of(s, fam): return s.OPMAP.get(fam)

    def step(s, st, a):
        k = st["w0"] + st["t"]; d = s._d(st, k); q = np.asarray(s._q(a), float)
        sold = np.minimum(st["stock"], d)
        n = dict(st); n["stock"] = st["stock"] - sold + q                 # order arrives for next week
        if isinstance(a, tuple) or st.get("bank", 0.0) > 0.0:             # REAL3 v2 CARRY: open-to-buy bank (capital, $k)
            spend = C * float(q.sum()); bank = st.get("bank", 0.0) - max(0.0, spend - st["B"])
            if isinstance(a, tuple): bank += max(0.0, st["B"] - spend)
            n["bank"] = min(st["B"], max(0.0, bank))
        n["rev"] = st["rev"] + P * sold.sum(); n["buy"] = st["buy"] + C * q.sum()
        n["capw"] = st["capw"] + C * (st["stock"] - sold).sum() + C * q.sum()
        n["sold"] = st["sold"] + sold.sum(); n["dem"] = st["dem"] + d.sum(); n["t"] = st["t"] + 1
        return n

    def fork(s, st, j):
        k = st["w0"] + st["t"]; key = (st["cell"], st["t"], j)
        if key not in s._cache:
            if len(s._cache) > 64: s._cache.clear()
            rng = np.random.default_rng([st["cell"], st["t"], j, 7071])
            n = min(2 * s.horizon + 2, len(s.D) - k)              # REAL3 v2: forks reach 2H (Eagle room, ZOOM 2H)
            # standard_normal((n, N)) fills row by row: the first H + 2 weeks are the same draws as before, bit for bit
            f = s._fc(st, k, n) * np.exp(SIG_F * rng.standard_normal((n, s.N)) - SIG_F ** 2 / 2)
            s._cache[key] = (list(f), k)
        f = dict(st); f["src"] = s._cache[key]; return f

    def _profit(s, st): return st["rev"] - st["buy"] + C * (st["stock"].sum() - st["stock0"].sum())
    def _result(s, st): return s._profit(st) - H_RATE * st["capw"]      # profit after the carrying cost
    def objective(s, st): return s._result(st)                         # = the result exactly (rule 4)
    def report(s, st):
        return {"result": s._result(st), "resource": st["capw"] / max(1, st["t"]), "gross_profit": s._profit(st),
                "fill_rate": st["sold"] / max(st["dem"], 1e-9)}
