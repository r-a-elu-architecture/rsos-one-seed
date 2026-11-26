"""REAL1 row 9, neuroscience: which recording channels to read under a sensing budget, to reconstruct the whole population.

HOST
  A population of N channels (binned spike counts, 50 ms bins; signal y = 2*sqrt(count + 3/8), Anscombe). Each episode
  (cell) = one window: CAL calibration bins fully recorded, then T sensing steps in which only K of the N channels can be
  read per step (the sensing budget). The host's model is fitted on the calibration bins ONLY (data up to now): a
  linear-Gaussian latent model (PCA subspace fit, L = 3 latents): y = d + C z + e, e ~ N(0, diag R); z' = A z + q,
  q ~ N(0, Q); A by least squares on the calibration latents. A Kalman filter tracks z from the channels read.
  Reconstruction at step t: a read channel = its read value; an unread channel = d_c + C_c z_hat(t|t).
  Action: the list of K channel indices to read now; valid() dedups, clips to K and pads with the unread channels of
  largest model variance.

DATA
  Neuro(data=None)        : STAND-IN for the interface check only, never for results. Generated per cell from a documented
                            model with realistic structure: 4 shanks x 8 channels; 4 true latents (two damped rotations at
                            ~1.5 and ~3 Hz, one slow AR(1) drift, one fast AR(1)); loadings with shank structure
                            (each shank loads mainly on two latents) plus channel-specific weights; baseline rates
                            log-normal (about 2-40 Hz); counts ~ Poisson(exp(b + C z) dt). The host's model (L = 3) is
                            deliberately misspecified against it (4 latents), as with real data.
  Neuro(data="x.npz")     : real recording produced by real/hosts/neuro_fetch.py on the laptop (DANDI:000140,
                            MC_Maze_Small, Neural Latents Benchmark; sorted units used as channels). Cell c = the c-th
                            non-overlapping window of CAL + T bins.

STANDARD METHOD (default; also the membrane bound)
  Variance-based (uncertainty) channel sampling for a Kalman filter: greedy sensor selection that each step picks, one
  channel at a time, the channel whose reading most reduces the model's expected reconstruction error of the whole
  population, sum_c E[(y_hat_c - y_c)^2] (unread: C_c P C_c^T + R_c; read: 0), with exact rank-1 covariance updates.
  Source: greedy sensor selection for Kalman filtering, Shamaiah, Banerjee, Vikalo, IEEE CDC 2010; uncertainty sampling
  in active sensing. This is the strongest form of "variance-based sampling" (it uses cross-channel covariance, not only
  each channel's own variance). Second baseline: uniform = round robin over channels (Neuro(standard="uniform")).

BRANCHES
  focused (4): focus_shank_g = the greedy selection restricted to the 8 channels of shank g.
  coupled (1): latent = the K channels with the largest loading on the latent direction of largest posterior variance
               (channels driven together by one latent: parts that drive each other).

OWN FUTURE (fork; layer-1 rule). 24 Nov (owner): the own future is read from the REAL TREE, not from a fitted model.
  Diagnosis of the first real run (DANDI 000140, 8/8 exact ties): inside the fitted linear-Gaussian model, greedy Kalman
  sensor selection is already (near) optimal, so every branch valued in that model looked no better than the standard.
  The fork therefore draws its future from the recording's OWN REAL PAST and values each branch by the reconstruction
  error it actually gives on those real futures, with the same Kalman filter (same z, P, d, C, A, Q, R) as the real
  estimate:
    real past used = the calibration bins (the only bins fully recorded before now; bins of the sensing steps are only
      read on K channels, so using their unread entries would read past the sensing budget). Nothing after the current
      time is ever touched; the calibration window is unchanged.
    alignment = analog block bootstrap: candidate starts i are calibration bins whose own latent Z[i] (calibration PCA
      projection) is among the NN = 16 nearest to the current estimate z_hat(t-1|t-1) (Mahalanobis, metric P0^-1), and
      whose block i+1 .. i+1+horizon lies inside the calibration window. Fork j picks one start uniformly, rng seeded
      from (cell, t, j, 9091); the fork's signal at its step h = Y[i+1+h] (a real past population vector, all N channels).
    value = the result on the fork: SSE of the actual reconstruction (read channel = its value, unread = d + C z_hat)
      against the real past block, the same formula as the real result. All branches of one decision share the same
      blocks (common random numbers).
  Neuro(future="model") keeps the previous own future (fitted linear-Gaussian model, expected error) for comparison.
  Why this can differ from greedy: greedy maximises the error reduction the FITTED model expects (Gaussian, L = 3,
  diagonal R, stationary A). On real blocks the error includes what the model does not hold: residual cross-channel
  correlation outside the 3-D subspace, Poisson/heavy-tailed and rate-dependent noise, non-stationary or nonlinear
  dynamics, channels whose real residual is larger or smaller than R says. A focused/coupled/past/plan branch whose
  reading actually reconstructs those real futures better passes the membrane; with the model future it never could.

MEASURE
  result   = 1 - SSE / (T * sum_c var_cal_c): fraction of the population signal's variance reconstructed over the
             sensing steps (var_cal from the calibration bins; fixed per cell).
  resource = channel samples read in the sensing steps (K * T; the calibration bins are identical for every method and
             are not counted).
  R = result / resource. objective(state) = the same formula on the state's own SSE (in a fork: errors against the fork's
  real past block); fixed-budget row: value = the result only.

SIZES (rule 5): N = 32, K = 4, CAL = 400 bins (20 s), T = 60 sensing steps (3 s), horizon = 12 (0.6 s; beyond that the
  fitted latent dynamics have decayed to the mean, so a longer look-ahead adds cost and no information), samples = 4.
  Quick test (4 cells x seed + default + uniform) runs in about a minute here.

CELLS THAT EXIST (REAL2, 24 Nov). A cell is one complete non-overlapping window of CAL + T = 460 bins (23 s).
  MC_Maze_Small (train file, 32 most active units, 50 ms bins) has 5874 bins (cloud log rq_neuro.txt) = 12 windows:
  cells 1-12 exist, 13+ do not. Neuro(...).windows gives the count; Neuro(...).cells(wanted) keeps the existing ones.
  A cell beyond the recording raises IndexError (with the bin and window count). REAL1 cause of failure: the old code
  raised AssertionError, which cloud/real1_unit.py does not catch (it catches IndexError/ValueError as "beyond
  recording"), so chunk 0 (cells 9-13) died at cell 13 after 9-12 and chunks 1-3 died at their first cell (14, 19, 24);
  the unit writes its JSON only at the end, so no neuro output survived. The preregistered windows 9-28 therefore hold
  only 4 existing windows (9-12) at this window size.

LAW 4 LANDING (REAL2 A, 24 Nov; seed.land)
  landings : one channel read among the K = 4 of the step.
  without  : that budget slot left unread (marked -1; valid() keeps -1 slots unread and does not pad them; step() reads
             only channels >= 0; resource = channels actually read). Fixed-budget row: the slot is lost, not banked.
  targets  : up to 3 unread channels, highest need first = the largest expected error reduction of reading them given
             the action's other reads (the standard's own greedy formula, on the current Kalman posterior).
  retarget : the read moved from channel L to channel T (same resource).

STRONGEST METHOD (REAL2 C): greedy Kalman sensor selection (Shamaiah et al. 2010) stays the standard. Each step it
  maximises the model's expected error reduction channel by channel with exact rank-1 updates; for this objective the
  greedy choice is near-optimal (submodular-type bound; the convex relaxation of Joshi & Boyd 2009 targets the same
  one-step criterion). Non-myopic sensor scheduling (multi-step tree search) is the only stronger family and is the same
  class of tool as the seed itself; a faithful version is not a quick standard build. Checked here (24 Nov, stand-in,
  cells 1-3, all 180 decision states of the standard's trajectory): exhaustive search over all C(32, 4) = 35960 subsets
  on the one-step criterion finds nothing better than greedy in any state (greedy = exact optimum, 180/180).


REAL3 (24 Nov; seed3.run binds primitives / frame / coupled; see the REAL3 block at the end of the class. REAL1/REAL2
modes unchanged, checked: default cell 1 0.64801, seed cell 3 0.30523 as in quick_logs/neuro_real2.txt)
  O-trace from REAL past reads only: innovation ratio per channel, last surprise, last read step, residual
    cross-products of channels read together.
  frame: F:rel (RELATIONS: ridge map read -> unread residuals, fitted on calibration residuals + past reads; leave-fold-
    out inside the own future; reads chosen greedily on C P C^T + Sig, i.e. where the whole learns most; marker -2 in
    the action switches the relations read-out on), F:rel-std (the standard's reads + relations read-out), F:otrace
    (greedy with R corrected by the innovation trace), F:otrace-rel.
  primitives: P1 surprise-weighted greedy, P2 age price (staleness), P3 worst shank, P4P5 3-step joint look-ahead,
    P8 vote of the 16 nearest real-past blocks.
  coupled: True (one joint read design)."""
import numpy as np

DT = 0.05


def standin_counts(cell, N=32, bins=460):
    """STAND-IN for the interface check only, never for results (documented generative model above)."""
    rng = np.random.default_rng([cell, 9090])
    def rot(f, r):
        a = 2 * np.pi * f * DT; return r * np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    A = np.zeros((4, 4)); A[:2, :2] = rot(rng.uniform(1.0, 2.0), 0.97); A[2, 2] = 0.995; A[3, 3] = 0.7
    qs = np.array([0.25, 0.25, 0.1, 0.5])
    z = np.zeros((bins, 4)); x = rng.normal(0, 1, 4)
    for t in range(bins):
        x = A @ x + qs * rng.normal(0, 1, 4); z[t] = x
    z = z / z.std(0)
    shank = np.repeat(np.arange(4), N // 4)
    prim = [(0, 1), (1, 2), (2, 3), (0, 3)]
    C = rng.normal(0, 0.15, (N, 4))
    for c in range(N):
        for k in prim[shank[c]]: C[c, k] += rng.normal(0, 0.45)
    b = np.log(rng.lognormal(np.log(10.0), 0.7, N))
    lam = np.exp(b + z @ C.T) * DT
    return rng.poisson(lam).astype(float), shank


class Neuro:
    horizon = 12; samples = 16   # = NN: every branch is valued on all 16 nearest real-past blocks (the tree)

    NN = 16   # analog block bootstrap: candidate real past blocks per decision (nearest calibration latents)

    def __init__(s, data=None, N=32, K=4, CAL=400, T=60, L=3, standard="greedy", future="real"):
        s.K, s.CAL, s.T, s.L, s.standard, s.future = K, CAL, T, L, standard, future
        s.data = None; s._cells = {}; s.windows = None
        if data is not None:
            d = np.load(data); s.data = d["counts"].astype(float)[:, :N]
            s.shank = d["group"][:N] if "group" in d.files else np.arange(s.data.shape[1]) * 4 // s.data.shape[1]
            N = s.data.shape[1]
            s.windows = s.data.shape[0] // (CAL + T)   # complete non-overlapping windows = the cells that exist
        s.N = N

    def cells(s, wanted):
        """The cells of `wanted` that exist in the recording (all of them for the stand-in)."""
        return [int(c) for c in wanted if s.windows is None or 1 <= int(c) <= s.windows]

    # ---------------------------------------------------------------- cell: data window and model fit (calibration only)
    def _cell(s, cell):
        if cell in s._cells: return s._cells[cell]
        if s.data is None:
            counts, shank = standin_counts(cell, s.N, s.CAL + s.T)
        else:
            w = s.CAL + s.T
            if not 1 <= int(cell) <= s.windows:   # IndexError: the sealed unit records it as "beyond recording" (an
                # assert here raised AssertionError, which the unit does not catch: every REAL1 neuro job died on it)
                raise IndexError(f"cell {cell} beyond recording: {s.data.shape[0]} bins = {s.windows} windows of {w}")
            counts = s.data[(cell - 1) * w: cell * w]; shank = s.shank
        Y = 2.0 * np.sqrt(counts + 0.375)
        cal = Y[: s.CAL]; d = cal.mean(0); Xc = cal - d
        U = np.linalg.svd(Xc, full_matrices=False)[2][: s.L].T            # N x L loadings (PCA subspace)
        Z = Xc @ U
        A = np.linalg.lstsq(Z[:-1], Z[1:], rcond=None)[0].T
        Q = np.cov((Z[1:] - Z[:-1] @ A.T).T) + 1e-6 * np.eye(s.L)
        R = np.maximum((Xc - Z @ U.T).var(0), 0.05)
        P0 = np.cov(Z.T)
        m = {"Y": Y, "d": d, "C": U, "A": A, "Q": Q, "R": R, "P0": P0, "z0": Z[-1], "var": cal.var(0), "Z": Z,
             "P0i": np.linalg.inv(P0 + 1e-9 * np.eye(s.L)),
             "shank": np.asarray(shank)}
        s._cells[cell] = m; return m

    # ---------------------------------------------------------------- interface
    def reset(s, cell):
        m = s._cell(cell)
        return {"t": 0, "cell": cell, "z": m["z0"].copy(), "P": np.zeros((s.L, s.L)) + 1e-6 * np.eye(s.L),
                "sse": 0.0, "read": 0, "model": False}

    def done(s, st):
        # REAL3 v2 (25 Nov): a REAL-TREE fork also ends where its real past block ends (the calibration window): the seed's
        # operators value some candidates at 2H (ZOOM scales, the Eagle room) and a block has room for H + 1 bins only.
        # Within H steps this never triggers (block start <= CAL - 1 - H), so every REAL1/REAL2/seed3v1 number is unchanged.
        return st["t"] >= s.T or (st.get("model") == "real" and st["blk"] + st["h"] >= s.CAL)

    def _prior(s, st):
        m = s._cell(st["cell"]); return m["A"] @ st["z"], m["A"] @ st["P"] @ m["A"].T + m["Q"]

    def _greedy(s, st, allowed=None):
        m = s._cell(st["cell"]); _, P = s._prior(st); C, R = m["C"], m["R"]
        S = C @ P @ C.T; unread = np.ones(s.N, bool); pick = []
        ok = np.ones(s.N, bool) if allowed is None else np.isin(np.arange(s.N), allowed)
        for _ in range(s.K):
            dS = np.diag(S); den = dS + R
            red = ((S ** 2) * unread[:, None]).sum(0) / den - (dS ** 2) / den + dS + R   # gain of reading c
            red[~(unread & ok)] = -np.inf
            if not np.isfinite(red).any(): break
            c = int(np.argmax(red)); pick.append(c); unread[c] = False
            S = S - np.outer(S[:, c], S[c, :]) / den[c]
        return pick

    def default(s, st):
        if s.standard == "uniform":
            return [int((st["t"] * s.K + i) % s.N) for i in range(s.K)]
        return s._greedy(st)

    def branches(s, st):
        m = s._cell(st["cell"]); out = []
        for g in np.unique(m["shank"])[:4]:
            out.append((f"focus_shank{int(g)}", s._greedy(st, np.where(m["shank"] == g)[0])))
        _, P = s._prior(st); v = np.linalg.eigh(P)[1][:, -1]
        out.append(("latent", [int(c) for c in np.argsort(-np.abs(m["C"] @ v))[: s.K]]))
        return out

    def valid(s, st, a):
        a0 = a
        skip = min(sum(1 for c in a if int(c) == -1), s.K)   # -1 = a budget slot deliberately left unread (landing)
        a = [int(c) for c in dict.fromkeys(int(c) for c in a) if 0 <= int(c) < s.N][: s.K - skip]
        if len(a) < s.K - skip:
            m = s._cell(st["cell"]); _, P = s._prior(st)
            var = np.einsum("ij,jk,ik->i", m["C"], P, m["C"]) + m["R"]
            for c in np.argsort(-var):
                if len(a) >= s.K - skip: break
                if int(c) not in a: a.append(int(c))
        return a + [-1] * skip + ([-2] if any(int(c) == -2 for c in a0) else [])

    def step(s, st, a):
        m = s._cell(st["cell"]); C, R, d = m["C"], m["R"], m["d"]
        st = dict(st); zp, Pp = s._prior(st)
        if st["model"] == "real":   # own future on the REAL TREE: the recording's own past block (calibration bins)
            assert st["blk"] + st["h"] < s.CAL, "own future may read only the calibration past"
            y = m["Y"][st["blk"] + st["h"]]; st["h"] += 1
        elif st["model"]:   # own model: synthetic signal from the fitted latent model (all noises drawn every step: CRN)
            rng = st["rng"]
            zt = m["A"] @ st["ztrue"] + rng.multivariate_normal(np.zeros(s.L), m["Q"])
            y = d + C @ zt + np.sqrt(R) * rng.normal(0, 1, s.N); st["ztrue"] = zt
        else:             # real host: the recording at the current bin (only read entries enter the filter)
            y = m["Y"][s.CAL + st["t"]]
        idx = np.array([c for c in a if int(c) >= 0], dtype=int); Cs = C[idx]
        if len(idx):
            Sm = Cs @ Pp @ Cs.T + np.diag(R[idx]); G = Pp @ Cs.T @ np.linalg.inv(Sm)
            z = zp + G @ (y[idx] - d[idx] - Cs @ zp); P = Pp - G @ Cs @ Pp
        else:
            z, P = zp, Pp
        yhat = d + C @ z
        if len(idx) and any(int(c) == -2 for c in a):   # REAL3 RELATIONS read-out (frame lever; marker -2 in the action)
            yhat = yhat + s._relmap(st, idx) @ (y[idx] - yhat[idx])
        if len(idx) and not st["model"]: s._otrace(st, idx, y, zp, Pp, z)   # REAL3 O-trace (real steps only)
        yhat[idx] = y[idx]
        st["z"], st["P"] = z, P
        if st["model"] is True:   # 14:05 (owner 13:38): the own future reads the TREE, not one leaf: the model's expected
            # reconstruction error after this read (unread channels: posterior variance + noise; read channels: 0)
            ev = np.einsum("ij,jk,ik->i", C, P, C) + R; ev[idx] = 0.0; st["sse"] = st["sse"] + float(ev.sum())
        else:
            st["sse"] = st["sse"] + float(((yhat - y) ** 2).sum())
        st["read"] += len(idx); st["t"] += 1
        return st

    def fork(s, st, j):
        if s.future == "model": return s._fork_model(st, j)
        m = s._cell(st["cell"]); f = dict(st); f["model"] = "real"
        rng = np.random.default_rng([st["cell"], st["t"], j, 9091])
        last = s.CAL - 1 - (s.horizon + 1)                       # block i+1 .. i+1+horizon stays inside calibration
        D = m["Z"][: last + 1] - st["z"]; dist = np.einsum("ij,jk,ik->i", D, m["P0i"], D)
        near = np.argsort(dist)[: s.NN]
        f["blk"] = int(near[j % len(near)]) + 1; f["h"] = 0   # 17:30 (lead review): the TREE: fork j = the j-th of all NN nearest real blocks, no random draw
        return f

    def _fork_model(s, st, j):   # previous own future (fitted linear-Gaussian model), kept for comparison only
        f = dict(st); f["model"] = True; f["rng"] = rng = np.random.default_rng([st["cell"], st["t"], j, 9091])
        P = st["P"] + 1e-9 * np.eye(s.L)
        f["ztrue"] = rng.multivariate_normal(st["z"], P); return f

    def _result(s, st):
        m = s._cell(st["cell"]); return 1.0 - st["sse"] / (max(st["t"], 1) * m["var"].sum())

    def objective(s, st): return s._result(st)   # fixed-budget row: the result only (rule 4; aligned 14:05)

    def report(s, st):
        return {"result": s._result(st), "resource": float(st["read"]), "sse": st["sse"],
                "data": "STAND-IN (interface check only)" if s.data is None else "recording"}

    # ---------------------------------------------------------------- LAW 4 LANDING (REAL2 A; seed.land)
    def landings(s, st, a): return [int(c) for c in a if int(c) >= 0]   # one landing = one channel read

    def without(s, st, a, L): return [(-1 if int(c) == L else int(c)) for c in a]   # the slot stays unread

    def _gain(s, st, picked):
        """Greedy gain of reading each channel next, given the channels already picked (the standard's own formula)."""
        m = s._cell(st["cell"]); _, P = s._prior(st); C, R = m["C"], m["R"]
        S = C @ P @ C.T; unread = np.ones(s.N, bool)
        for c in picked:
            den = S[c, c] + R[c]; S = S - np.outer(S[:, c], S[c, :]) / den; unread[c] = False
        dS = np.diag(S); den = dS + R
        red = ((S ** 2) * unread[:, None]).sum(0) / den - (dS ** 2) / den + dS + R
        red[~unread] = -np.inf; return red

    def targets(s, st, a, L):
        """Unread channels, highest need first = largest expected error reduction given the action's other reads."""
        rest = [int(c) for c in a if int(c) >= 0 and int(c) != L]; red = s._gain(st, rest); red[L] = -np.inf
        return [int(c) for c in np.argsort(-red)[:3] if np.isfinite(red[c])]

    def retarget(s, st, a, L, T): return [(T if int(c) == L else int(c)) for c in a]

    # ---------------------------------------------------------------- REAL3 (seed3: primitives, frame, coupled)
    # Everything below is read only by seed3. REAL1/REAL2 actions never carry the marker -2 and the O-trace fields are
    # written on real steps only without touching any computed number, so seed / seed_noland / rollout / default /
    # uniform give identical results.
    #   O-TRACE (real past reads only, data up to now): per channel the innovation ratio (y_c - d_c - C_c z_prior)^2 /
    #     (C_c P_prior C_c^T + R_c) (sum, count), the last surprise (decayed 0.8 per step), the step it was last read,
    #     and the cross-products of the posterior residuals of channels read together (for RELATIONS).
    #   RELATIONS (frame lever): cross-channel ridge map from the read channels' residuals to every other channel's,
    #     B = Sig[:, S] (Sig[S, S] + 0.2 diag Sig[S, S])^-1, Sig = residual covariance outside the latent subspace,
    #     fitted on the calibration residuals (Xc - Z U^T) plus the residual cross-products of past reads. Read-out:
    #     unread y_hat = d + C z + B (y_S - d_S - C_S z) (marker -2 in the action). Own future on the REAL TREE: the
    #     fork's block is calibration data, so there Sig is refitted WITHOUT the calibration folds (5 x 80 bins) that
    #     the block touches (no in-sample advantage for the lever inside the seed's own valuation).
    #   READ WHERE THE WHOLE LEARNS MOST: greedy on the joint error covariance C P C^T + Sig (Sig full, not diag R).
    FOLDS = 5

    def _sig(s, st):
        m = s._cell(st["cell"])
        if "E" not in m:
            m["E"] = (m["Y"][: s.CAL] - m["d"]) - m["Z"] @ m["C"].T; m["sig"] = {}
        drop = ()
        if st["model"] == "real":
            fl = s.CAL // s.FOLDS; lo, hi = st["blk"], st["blk"] + s.horizon + 1
            drop = tuple(f for f in range(s.FOLDS) if f * fl < hi and (f + 1) * fl > lo)
        if drop not in m["sig"]:
            keep = np.ones(s.CAL, bool); fl = s.CAL // s.FOLDS
            for f in drop: keep[f * fl:(f + 1) * fl] = False
            E = m["E"][keep]; m["sig"][drop] = (E.T @ E, float(len(E)))
        EE, n = m["sig"][drop]
        rs, rc = st.get("rel", (0.0, 0.0))
        return (EE + rs) / (n + rc)

    def _relmap(s, st, idx):
        Sg = s._sig(st); Ss = Sg[np.ix_(idx, idx)]
        return Sg[:, idx] @ np.linalg.inv(Ss + 0.2 * np.diag(np.diag(Ss)) + 1e-9 * np.eye(len(idx)))

    def _otrace(s, st, idx, y, zp, Pp, z):
        m = s._cell(st["cell"]); C, R, d = m["C"], m["R"], m["d"]
        inn = y[idx] - d[idx] - C[idx] @ zp; pv = np.einsum("ij,jk,ik->i", C[idx], Pp, C[idx]) + R[idx]
        os_, oc = st.get("otr", (np.zeros(s.N), np.zeros(s.N))); os_, oc = os_.copy(), oc.copy()
        os_[idx] += inn ** 2 / pv; oc[idx] += 1; st["otr"] = (os_, oc)
        sur = st.get("sur", np.zeros(s.N)) * 0.8; sur = sur.copy(); sur[idx] = inn ** 2 / pv; st["sur"] = sur
        last = st.get("last", np.full(s.N, -1.0)).copy(); last[idx] = st["t"]; st["last"] = last
        r = y[idx] - d[idx] - C[idx] @ z
        rs, rc = st.get("rel", (np.zeros((s.N, s.N)), np.zeros((s.N, s.N))))
        rs, rc = rs.copy(), rc.copy(); rs[np.ix_(idx, idx)] += np.outer(r, r); rc[np.ix_(idx, idx)] += 1
        st["rel"] = (rs, rc)

    def _greedy_full(s, Sf, ok=None, bonus=None):
        """Greedy reads on a full joint error covariance Sf (reading c removes sum_i Sf_ic^2 / Sf_cc of unread error).
        With Sf = C P C^T + diag R this is exactly the standard's greedy; bonus(c, red) reshapes the score (primitives)."""
        Sf = Sf.copy(); unread = np.ones(s.N, bool); pick = []
        ok = np.ones(s.N, bool) if ok is None else ok
        for _ in range(s.K):
            dS = np.maximum(np.diag(Sf), 1e-12); red = ((Sf ** 2) * unread[:, None]).sum(0) / dS
            if bonus is not None: red = bonus(red)
            red[~(unread & ok)] = -np.inf
            if not np.isfinite(red).any(): break
            c = int(np.argmax(red)); pick.append(c); unread[c] = False
            Sf = Sf - np.outer(Sf[:, c], Sf[c, :]) / dS[c]
        return pick

    def _S(s, st, noise=None):
        m = s._cell(st["cell"]); _, P = s._prior(st); C = m["C"]
        return C @ P @ C.T + (np.diag(m["R"]) if noise is None else noise)

    def _ratio(s, st):
        os_, oc = st.get("otr", (np.zeros(s.N), np.zeros(s.N))); return (os_ + 5.0) / (oc + 5.0)   # shrunk to 1

    def _lookahead(s, st, H=3):
        """P4+P5: reads chosen jointly by the whole-population error summed over this step and H-1 steps after it
        (no further reads assumed: the value of a read carried forward through the latent dynamics)."""
        m = s._cell(st["cell"]); C, R, A, Q = m["C"], m["R"], m["A"], m["Q"]; _, P0 = s._prior(st); pick = []
        def val(sel):
            P = P0.copy()
            for c in sel:
                Cc = C[c:c + 1]; Sc = Cc @ P @ Cc.T + R[c]; P = P - (P @ Cc.T @ Cc @ P) / Sc
            tot = 0.0
            for h in range(H):
                ev = np.einsum("ij,jk,ik->i", C, P, C) + R
                if h == 0: ev[list(sel)] = 0.0
                tot += ev.sum(); P = A @ P @ A.T + Q
            return tot
        for _ in range(s.K):
            best = min((val(pick + [c]), c) for c in range(s.N) if c not in pick); pick.append(best[1])
        return pick

    def _vote(s, st):
        """P8: each of the NN nearest real-past blocks (the seed's own tree) votes for the K channels whose real
        one-step error d + C A Z[i] -> Y[i+1] was largest there; the K most voted are read (ties: summed error)."""
        m = s._cell(st["cell"]); last = s.CAL - 1 - (s.horizon + 1)
        D = m["Z"][: last + 1] - st["z"]; near = np.argsort(np.einsum("ij,jk,ik->i", D, m["P0i"], D))[: s.NN]
        E = (m["Y"][near + 1] - m["d"] - (m["Z"][near] @ m["A"].T) @ m["C"].T) ** 2
        votes = np.zeros(s.N)
        for e in E: votes[np.argsort(-e)[: s.K]] += 1
        return [int(c) for c in np.lexsort((-E.sum(0), -votes))[: s.K]]

    def primitives(s, st):
        m = s._cell(st["cell"]); S0 = s._S(st)
        sur = st.get("sur", np.zeros(s.N)); last = st.get("last", np.full(s.N, -1.0)); age = st["t"] - last
        ev = np.diag(S0); g = m["shank"]; worst = max(np.unique(g), key=lambda k: ev[g == k].sum())
        return [("P1", "P1:surprise", s._greedy_full(S0, bonus=lambda r: r * (1 + np.minimum(sur, 4.0)))),
                ("P2", "P2:age-price", s._greedy_full(S0, bonus=lambda r: r * (1 + 0.05 * np.minimum(age, 20)))),
                ("P3", "P3:worst-shank", s._greedy_full(S0, ok=(g == worst))),
                ("P4P5", "P4P5:lookahead", s._lookahead(st)),
                ("P8", "P8:vote", s._vote(st))]

    def frame(s, st):
        m = s._cell(st["cell"]); Sg = s._sig(st)
        rel = s._greedy_full(s._S(st, noise=Sg))                     # read where the whole learns most (relations)
        otr = s._greedy_full(s._S(st, noise=np.diag(m["R"] * s._ratio(st))))   # O-trace: R corrected by the real past
        return [("F:rel", "F:rel-reads", rel + [-2]),                # relations reads + relations read-out
                ("F:rel", "F:rel-std", s.default(st) + [-2]),         # the standard's reads + relations read-out
                ("F:otrace", "F:otrace", otr),
                ("F:otrace", "F:otrace-rel", otr + [-2])]

    def coupled(s, st):
        """True: the channels drive each other through the shared latents and (RELATIONS) through each other's
        residuals; the K reads are one joint design, so the action lands as a whole (a withheld read on this
        fixed-budget row is lost, not banked)."""
        return True

    # ---------------------------------------------------------------- REAL3 v2 (seed3_ops hooks; HOST_INTERFACE_REAL3v2)
    # Read only by seed3 mode "seed3" (v2). Nothing above is changed: REAL1/REAL2 modes and seed3v1 give identical numbers.
    #   parts        : the shanks (stand-in: 4 x 8); on a recording with one electrode group (MC_Maze_Small) 4 functional
    #                  channel groups from the calibration bins (see _groups); a part
    #                  id = the tuple of its channel indices. within = a shank: its channels, each a sub-part (c,) (ENTER
    #                  depth 2: the seed's choice run again channel by channel inside the bottleneck shank).
    #   merge        : the named parts' reads first (dict order = who gets the K slots first), then the standard's reads
    #                  on the parts not named; valid() truncates to K. The RELATIONS read-out (marker -2) is kept if a
    #                  named part's action carries it (it is a read-out of the whole, not a read).
    #   part_objective: minus the shank's expected unexplained fraction of variance now: sum over its channels of the
    #                  model's error variance (C P_prior C^T + R) corrected by the O-trace innovation ratio of the real
    #                  past reads, over the channels' calibration variance (higher = better).
    #   focus        : all K reads inside one shank (the standard's greedy restricted to it; = branch focus_shank).
    #   shape        : residual-error band per group (part_objective minus the groups' mean, in steps of 0.02, capped at
    #                  +-3; the unexplained fractions are 0.6-0.99, so absolute bands would not separate) + the groups' rank.
    #   joint        : one read per group (the best greedy gain in each group), with and without the relations read-out.
    #   map_part     : RE-HOST: each channel a reads on shank pf -> the channel of shank pt with the largest |residual
    #                  correlation| to it (calibration residual covariance outside the latent subspace; no duplicates).
    #   carry        : NOT bound (fixed-budget row: a read not used this step is lost, the host has no bank).
    #   op_of        : focus_shank* -> beam, latent -> fuse; F:* -> frame and P* stay with the seed's table.
    def _groups(s, st):
        """Channel groups: the recording's shanks when it has >= 2; else (MC_Maze_Small: all 32 units in one electrode
        group) 4 FUNCTIONAL groups formed from the calibration bins only (data up to now): k-means (k = 4, seed 0) on
        each channel's correlation profile with all channels (channels that co-vary = one group)."""
        m = s._cell(st["cell"])
        if "parts" not in m:
            g = m["shank"]
            if len(np.unique(g)) >= 2:
                m["parts"] = [tuple(int(c) for c in np.where(g == k)[0]) for k in np.unique(g)]
            else:
                from sklearn.cluster import KMeans
                Cr = np.corrcoef(m["Y"][: s.CAL].T); Cr = np.nan_to_num(Cr)
                lab = KMeans(n_clusters=4, random_state=0, n_init=10).fit_predict(Cr)
                m["parts"] = [tuple(int(c) for c in np.where(lab == k)[0]) for k in np.unique(lab)]
        return m["parts"]

    def parts(s, st, within=None):
        if within is not None: return [(int(c),) for c in within]
        return list(s._groups(st))

    def merge(s, st, d):
        out, named, rel = [], set(), False
        for p, a in d.items():
            out += [int(c) for c in a if int(c) >= 0 and int(c) in p]; named |= set(p)
            rel = rel or any(int(c) == -2 for c in a)
        out += [int(c) for c in s.default(st) if int(c) not in named]
        return list(dict.fromkeys(out))[: s.K] + ([-2] if rel else [])

    def _ev(s, st):
        m = s._cell(st["cell"]); _, P = s._prior(st)
        return (np.einsum("ij,jk,ik->i", m["C"], P, m["C"]) + m["R"]) * s._ratio(st)

    def part_objective(s, st, p):
        m = s._cell(st["cell"]); idx = list(p); return -float(s._ev(st)[idx].sum() / max(m["var"][idx].sum(), 1e-9))

    def focus(s, st, p): return s._greedy(st, list(p))

    def shape(s, st):
        po = np.array([s.part_objective(st, p) for p in s.parts(st)]); mu = po.mean()
        return (tuple(int(np.clip(np.round((x - mu) / 0.02), -3, 3)) for x in po), tuple(int(i) for i in np.argsort(po)))

    def joint(s, st):
        red = s._gain(st, []); one = []
        for p in s._groups(st):
            cs = np.array(p); one.append(int(cs[np.argmax(red[cs])]))
        one = sorted(one, key=lambda c: -red[c])[: s.K]
        return [("one-per-shank", one), ("one-per-shank-rel", one + [-2])]

    def map_part(s, st, a, pf, pt):
        Sg = s._sig(st); dg = np.sqrt(np.maximum(np.diag(Sg), 1e-12)); Cr = np.abs(Sg / np.outer(dg, dg))
        out = []
        for c in a:
            c = int(c)
            if c < 0 or c not in pf: continue
            free = [q for q in pt if q not in out]
            if free: out.append(int(max(free, key=lambda q: Cr[c, q])))
        return out + ([-2] if any(int(c) == -2 for c in a) else [])

    def op_of(s, fam):
        if fam.startswith("focus_shank"): return "beam"
        return {"latent": "fuse"}.get(fam)
