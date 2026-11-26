"""REAL1 row 8, robotics: Gymnasium Pendulum-v1 (the real physics step is gymnasium's own PendulumEnv.step).

TASK. Torque-limited pendulum swing-up and balance (g 10, m 1, l 1, dt 0.05, |u| <= 2 N m, 200 steps, random start
from env.reset(seed=cell)). Gymnasium's own reset and step are the real host; nothing in its dynamics is changed.

INJECTED NOISE (documented, so that no fork can be the exact future; layer-1 rule):
  actuation : the applied torque is u + N(0, 0.10) N m (5 % of max torque), then clipped to [-2, 2]
  observation: the controller sees theta + N(0, 0.01) rad and omega + N(0, 0.05) rad/s
  Both come from the real rng in the state (np.random.default_rng([cell, 8101])); a fork never touches it.

UNITS, BUDGET, RESOURCE, RESULT (row kind: FREE-RESOURCE, brief rule 4: pass per cell = Pareto, result >= standard
AND resource <= standard, at least one strictly)
  units    : the controlled parts of the one joint: energy, angle, velocity (and angle+velocity together)
  budget   : the standard method's own effort, as an effort bank: each step the bank is credited |u_std(state)|, the
             effort the standard controller would spend in this state; valid() clips |u| to min(2, bank + credit)
             (2 N m is the actuator limit); step() debits |u|. The seed can save effort in one step and spend it in a
             later one, never more than the standard's credit accumulated along its own trajectory.
  resource : control effort = sum over steps of |u_commanded| (N m x steps)
  result   : success steps = steps with the true pole upright, |angle| < 0.3 rad (the task's success measure)
  report   : also gives the Gymnasium return (sum of rewards) and the final upright flag, for the quality check
  objective(state) = the result only (success steps so far, in the fork), never divided by the resource

STANDARD METHOD (default): energy-based swing-up (Astrom & Furuta, "Swinging up a pendulum by energy control",
Automatica 36, 2000: u = sat(k (E_up - E) sign(omega)), E = 1/2 I omega^2 + m g l/2 cos(theta), I = m l^2 / 3)
switched to a discrete-time LQR inside |theta| < 0.8 rad. The LQR is designed on the exact linearisation of
gymnasium's semi-implicit Euler step (scipy solve_discrete_are) with the task's state weights Q = diag(1, 0.1) and an
EFFORT-AWARE input weight R = 10, because this row counts control effort as the resource. Tuning on cells 1000-1039
only (development cells 1-4 never used): first the swing-up for return (k in {0.25, 0.5, 1, 2} x switch in
{0.4 .. 1.0}: k = 1 best, return -157.5, upright 170/200 with the injected noise), then R and the switch for R at
equal quality (R_lqr in {0.001, 0.01, 0.1, 1, 10, 100} x k {0.5, 1} x switch {0.6, 0.8}): the task's own weight
R = 0.001 (gains 19.7, 5.3) chatters on the observation noise, effort 108, R 1.65; R = 10 (gains 9.13, 2.14, close to
the minimum-effort stabilising gain) gives the same upright 169.9 and return -157.7 with effort 70.0, R 2.72. That
stronger standard is the one used. Without noise the controller returns about -138, at the level of the best
published Pendulum-v1 returns.

BRANCHES (all clipped by valid() to the same effort bank):
  focused  : coast (u = 0, no effort), pump (energy term only, bang at u_max), angle (angle feedback only),
             damp (velocity feedback only), half (the standard action at half effort)
  coupled  : lqr (angle and velocity together, full-state LQR anywhere; the two states drive each other)

OWN FUTURE (fork): the host's model = a second gymnasium PendulumEnv started from the OBSERVED (noisy) state, never
the true state, with the same documented noise model drawn from np.random.default_rng([cell, t, j, 8177]).

SIZE (rule 5): episode 200 steps (the Pendulum-v1 time limit), horizon 100 steps (half the episode: a swing-up
takes 40-90 steps, so the fork sees the effect of a swing choice on the balance), samples 2. About 10 s per seed
episode on 1 CPU here; the quick check takes about 40 s. (REAL2: with seed.TREE = 8 forks the seed episode takes about
45 s without landing, about 60-70 s with it.)

LAW 4 LANDING (REAL2 A, 24 Nov; seed.land)
  landings : the control-effort chunks of the commanded torque, CH = 1 N m each (chunk k = [k CH, min((k+1) CH, |u|)];
             at most 2 per step at the 2 N m limit; coast u = 0 has none). 1 N m keeps the quick test in minutes
             (each landing is valued with and without, and at each target, over the 8 own futures of 100 steps).
  without  : |u| reduced by that chunk's size, same sign (the effort stays in the bank for a later step).
  targets  : the parts of the one joint (pump = energy, angle, damp = velocity) whose own control law asks for torque in
             the OTHER direction from the action, highest |need| first (parts already served by the action's direction
             are not "elsewhere").
  retarget : the chunk is applied in the target part's direction: u - sign(u) size + sign(need_T) size. On a single
             actuator a chunk pushed the other way nets against the rest, so the commanded effort |u| can only fall
             (never rise): the resource is <= the action's, which the free-resource (Pareto) row allows.

STRONGEST METHOD (REAL2 C): the standard above is the strongest standard for this task kept faithful to the row:
  energy-based swing-up + LQR is the textbook controller for the torque-limited pendulum (Astrom-Furuta 2000), tuned
  here for the row's effort measure; without noise it reaches the best published Pendulum-v1 returns (about -138 here).
  Nonlinear MPC / iLQR is the only family that could be stronger on swing-up time, but it is a planner with its own
  model rollouts (the same class of tool as the seed itself), it is not standard for this benchmark, and a faithful,
  tuned version under the same effort bank is not a quick build; it is not added.

REAL3 (24 Nov; seed3.run binds primitives / frame / coupled; REAL1/REAL2 modes unchanged, checked: default cells 1-2
42.492 / 50.042, seed cell 1 35.415 as in quick_logs/robotics_real2.txt)
  O-trace of disturbances: step() on REAL steps records the implied actuation residual (observed speed change minus the
    model's) -> bias estimate (shrunk mean) and noise sigma (variance minus the known observation-noise part), and a
    filtered state xf (own nonlinear step + steady-state Kalman gain). No rng draw: identical numbers in old modes.
  primitives: P1 counter-shift (standard action minus the estimated bias), P2 price on effort (LQR with R = 100; this
    gain is within 0.1 % of the R = 10 standard: the standard is already at the minimum-effort stabilising gain, so P2
    differs only in swing-up, half pump gain), P3 repair the energy part only while it is off (5 % deadband),
    P4P5 = cross-entropy trajectory optimisation (horizon 15, 64 samples x 3 iterations, 8 elites, mean initialised
    to the standard's own sequence) on the host's own model (gymnasium's equations in numpy) inside the same effort
    bank, first action; P8 = median first action of the CEM elites. P6/P7 are seed3's own (ordering, apoptosis).
  frame: F:trace (standard law on the trace's filtered state, bias countered), F:traj (the CEM from the filtered state
    with the trace's bias).
  coupled: True inside the balance basin (one full-state feedback), False in swing-up (per-chunk landing applies)."""
import math
import numpy as np
import gymnasium as gym
from scipy.linalg import solve_discrete_are

G, M, L, DT, UMAX, T = 10.0, 1.0, 1.0, 0.05, 2.0, 200
SIG_U, SIG_TH, SIG_W, UP = 0.10, 0.01, 0.05, 0.3
I_P, E_UP = M * L * L / 3, M * G * L / 2
KE, SW = 1.0, 0.8
CH = 1.0   # landing granularity: one control-effort chunk = 1 N m of the commanded torque (REAL2 A)
_A = np.array([[1 + 3 * G / (2 * L) * DT * DT, DT], [3 * G / (2 * L) * DT, 1]])
_B = np.array([[3 / (M * L * L) * DT * DT], [3 / (M * L * L) * DT]])
_Q, _R = np.diag([1.0, 0.1]), np.array([[10.0]])
_P = solve_discrete_are(_A, _B, _Q, _R)
K_LQR = np.linalg.solve(_R + _B.T @ _P @ _B, _B.T @ _P @ _A)[0]          # about [9.13, 2.14]

def an(x): return ((x + math.pi) % (2 * math.pi)) - math.pi
def clip(u): return max(-UMAX, min(UMAX, float(u)))
def energy(th, w): return 0.5 * I_P * w * w + M * G * L / 2 * math.cos(th)
def pump(th, w): return clip(KE * (E_UP - energy(th, w)) * (1.0 if w >= 0 else -1.0) * UMAX)
def lqr(th, w): return clip(-(K_LQR[0] * an(th) + K_LQR[1] * w))

class Robotics:
    horizon = 100; samples = 2
    def __init__(s):
        s.real_env = gym.make("Pendulum-v1").unwrapped; s.model_env = gym.make("Pendulum-v1").unwrapped

    def _observe(s, st):
        th, w = st["x"]; r = st["rng"]
        st["obs"] = (float(th + r.normal(0, SIG_TH)), float(w + r.normal(0, SIG_W)))

    def reset(s, cell):
        s.real_env.reset(seed=int(cell)); th, w = map(float, s.real_env.state)
        st = {"t": 0, "cell": int(cell), "x": (th, w), "rng": np.random.default_rng([int(cell), 8101]),
              "eff": 0.0, "bank": 0.0, "up": 0, "ret": 0.0, "model": False}
        s._observe(st); return st

    def done(s, st): return st["t"] >= T

    def default(s, st):                                         # energy swing-up + LQR (Astrom-Furuta 2000)
        th, w = st["obs"]
        return lqr(th, w) if abs(an(th)) < SW else pump(th, w)

    def branches(s, st):
        th, w = st["obs"]; d = s.default(st)
        return [("coast", 0.0), ("pump", pump(th, w)), ("angle", clip(-K_LQR[0] * an(th))),
                ("damp", clip(-K_LQR[1] * w)), ("half", 0.5 * d), ("lqr", lqr(th, w))]

    def _cap(s, st): return min(UMAX, st["bank"] + abs(s.default(st)))      # the standard's effort budget now

    def valid(s, st, a):
        c = s._cap(st); return max(-c, min(c, clip(a)))

    def step(s, st, a):
        credit = abs(s.default(st)); u = s.valid(st, a); env = s.model_env if st["model"] else s.real_env; r = st["rng"]
        st = dict(st); st["bank"] = max(0.0, st["bank"] + credit - abs(u)); env.state = np.array(st["x"], dtype=np.float64)
        _, rew, _, _, _ = env.step(np.array([clip(u + r.normal(0, SIG_U))], dtype=np.float32))
        th, w = map(float, env.state)
        st["x"] = (th, w); st["t"] += 1; st["eff"] += abs(u); st["ret"] += float(rew); st["up"] += int(abs(an(th)) < UP)
        o_prev = st["obs"]; s._observe(st)
        if not st["model"]: s._trace(st, o_prev, u)     # REAL3 O-trace of disturbances (real steps only; no rng draw)
        return st

    def fork(s, st, j):                     # the host's model from the OBSERVED state, independent noise (never real)
        f = dict(st); f["x"] = tuple(st["obs"]); f["model"] = True
        f["rng"] = np.random.default_rng([st["cell"], st["t"], j, 8177]); return f

    def objective(s, st): return (float(st["up"]), -float(st["eff"]))   # free-resource row: result first, then less effort (14:00)

    def report(s, st):
        return {"result": float(st["up"]), "resource": st["eff"], "return": st["ret"],
                "upright_end": int(abs(an(st["x"][0])) < UP)}

    # ---------------------------------------------------------------- LAW 4 LANDING (REAL2 A; seed.land)
    def _chunks(s, u):
        """Chunk k of |u| covers [k CH, min((k+1) CH, |u|)] N m (CH = 1 N m: at most 2 chunks at the 2 N m limit)."""
        m = abs(float(u)); n = int(math.ceil(m / CH - 1e-9)); return [min(CH, m - k * CH) for k in range(n)]

    def landings(s, st, a):
        return [k for k, size in enumerate(s._chunks(a)) if size > 1e-9]

    def without(s, st, a, L):
        size = s._chunks(a)[L]; return math.copysign(max(0.0, abs(float(a)) - size), float(a))

    def _needs(s, st):
        th, w = st["obs"]
        return {"pump": pump(th, w), "angle": clip(-K_LQR[0] * an(th)), "damp": clip(-K_LQR[1] * w)}

    def targets(s, st, a, L):
        """Parts whose own control law asks for torque in the OTHER direction from the action, highest need first."""
        sg = 1.0 if float(a) >= 0 else -1.0
        need = [(abs(v), k) for k, v in s._needs(st).items() if v * sg < -1e-9]
        return [k for _, k in sorted(need, reverse=True)][:3]

    def retarget(s, st, a, L, T):
        size = s._chunks(a)[L]; sg = 1.0 if float(a) >= 0 else -1.0
        dT = 1.0 if s._needs(st)[T] >= 0 else -1.0
        return float(a) - sg * size + dT * size

    # ---------------------------------------------------------------- REAL3 (seed3: primitives, frame, coupled)
    # O-trace of disturbances, on REAL steps only (written by step(); forks never read or write it; no rng is drawn, so
    # every REAL1/REAL2 mode gives identical numbers):
    #   implied actuation residual d = ((w'_obs - w_obs) / DT - 3 g / (2 l) sin(th_obs)) / (3 / (m l^2)) - u, kept for
    #   steps where neither the speed limit nor the torque limit is active (there the model's map is not invertible);
    #   bias b = shrunk running mean (sum / (n + 20)); noise sigma = sqrt(max(0, var(d) - obs-noise part)), the obs-noise
    #   part known from the documented observation noise (2 SIG_W^2 / (3 DT)^2 + (g/2 l SIG_TH / 3)^2 ... see _trace).
    #   Filtered state xf: the host's own nonlinear step from the previous xf with the applied u and b, corrected by
    #   the steady-state Kalman gain of the linearised step (process noise = actuation noise, measurement = obs noise).
    def _trace(s, st, o_prev, u):
        th0, w0 = o_prev; th1, w1 = st["obs"]
        d = ((w1 - w0) / DT - 3 * G / (2 * L) * math.sin(th0)) / (3 / (M * L * L)) - u
        tr = st.get("dtr", ())
        if abs(w1) < 7.5 and abs(u) < UMAX - 3 * SIG_U: tr = (tr + (d,))[-80:]
        st["dtr"] = tr
        xf = st.get("xf")
        if xf is None: xf = o_prev
        b = s._bias(st)
        wp = max(-8.0, min(8.0, xf[1] + (3 * G / (2 * L) * math.sin(xf[0]) + 3 / (M * L * L) * clip(u + b)) * DT))
        thp = xf[0] + wp * DT
        e = np.array([an(th1 - thp), w1 - wp]); x = np.array([thp, wp]) + _KF @ e
        st["xf"] = (float(x[0]), float(x[1]))

    def _bias(s, st):
        tr = st.get("dtr", ()); return float(sum(tr) / (len(tr) + 20.0))

    def _sigma(s, st):
        tr = st.get("dtr", ())
        if len(tr) < 10: return SIG_U
        obs = 2 * SIG_W ** 2 / (3 * DT) ** 2 + (G / 2 * SIG_TH) ** 2       # what the observation noise alone puts in d
        return float(math.sqrt(max(0.0, np.var(tr) - obs)))

    def disturbance(s, st):
        """The trace's current estimate: actuation bias, actuation noise sigma, samples used, filtered state."""
        return {"bias": s._bias(st), "sigma": s._sigma(st), "n": len(st.get("dtr", ())), "xf": st.get("xf")}

    def _law(s, th, w):                       # the standard law (swing-up + LQR) at any state estimate
        return lqr(th, w) if abs(an(th)) < SW else pump(th, w)

    # P5 over the whole short trajectory: cross-entropy method on the host's OWN model (gymnasium's step written in
    # numpy, the same equations), the same effort bank (credit = |standard action| in each model state), horizon CEM_H.
    def _cem(s, st, x0, bias):
        H, N, NE, IT = CEM_H, 64, 8, 3
        g = np.random.default_rng([st["cell"], st["t"], 8303])
        def sim(U):
            th = np.full(len(U), x0[0]); w = np.full(len(U), x0[1]); bank = np.full(len(U), st["bank"])
            cost = np.zeros(len(U)); Ua = np.zeros_like(U)
            for h in range(H):
                a_ = (th + np.pi) % (2 * np.pi) - np.pi
                std = np.where(np.abs(a_) < SW, np.clip(-(K_LQR[0] * a_ + K_LQR[1] * w), -UMAX, UMAX),
                               np.clip(KE * (E_UP - (0.5 * I_P * w * w + M * G * L / 2 * np.cos(th))) * np.where(w >= 0, 1.0, -1.0) * UMAX, -UMAX, UMAX))
                cap = np.minimum(UMAX, bank + np.abs(std)); u = np.clip(U[:, h], -cap, cap); Ua[:, h] = u
                bank = np.maximum(0.0, bank + np.abs(std) - np.abs(u))
                w = np.clip(w + (3 * G / (2 * L) * np.sin(th) + 3 / (M * L * L) * np.clip(u + bias, -UMAX, UMAX)) * DT, -8, 8)
                th = th + w * DT; a_ = (th + np.pi) % (2 * np.pi) - np.pi
                cost += -1.0 * (np.abs(a_) < UP) + 0.01 * np.abs(u) + 0.05 * (a_ ** 2 + 0.1 * w ** 2)
            E = 0.5 * I_P * w * w + M * G * L / 2 * np.cos(th)
            return cost + 0.5 * ((E_UP - E) / E_UP) ** 2 + 0.5 * a_ ** 2, Ua
        # mean = the standard's own sequence in the model (the plan to improve on)
        mean = np.zeros(H); th, w, bank = x0[0], x0[1], st["bank"]
        for h in range(H):
            sd = s._law(th, w); u = max(-min(UMAX, bank + abs(sd)), min(min(UMAX, bank + abs(sd)), sd)); mean[h] = u
            bank = max(0.0, bank + abs(sd) - abs(u))
            w = max(-8.0, min(8.0, w + (3 * G / (2 * L) * math.sin(th) + 3 / (M * L * L) * clip(u + bias)) * DT)); th = th + w * DT
        sig = np.full(H, 0.6); best = (np.inf, mean[0]); elite_first = np.array([mean[0]])
        for _ in range(IT):
            U = np.clip(mean + sig * g.normal(0, 1, (N, H)), -UMAX, UMAX); U[0] = mean
            c, Ua = sim(U); o = np.argsort(c)[:NE]
            if c[o[0]] < best[0]: best = (float(c[o[0]]), float(Ua[o[0], 0]))
            mean = Ua[o].mean(0); sig = np.maximum(0.05, Ua[o].std(0)); elite_first = Ua[o, 0]
        return best[1], float(np.median(elite_first))

    def _plans(s, st):
        key = (st["cell"], st["t"], st["bank"], st["obs"])
        if getattr(s, "_pk", None) != key:
            b = s._bias(st); xf = st.get("xf") or st["obs"]
            p5, p8 = s._cem(st, st["obs"], 0.0)
            f5, _ = s._cem(st, xf, b)
            s._pk, s._pv = key, (p5, p8, f5)
        return s._pv

    def primitives(s, st):
        th, w = st["obs"]; d = s.default(st); b = s._bias(st); p5, p8, _ = s._plans(st)
        ep = E_UP - energy(th, w)
        p2 = clip(-(K_P2[0] * an(th) + K_P2[1] * w)) if abs(an(th)) < SW else clip(0.5 * KE * ep * (1.0 if w >= 0 else -1.0) * UMAX)
        p3 = d if abs(an(th)) < SW else (0.0 if abs(ep) < 0.05 * E_UP else d)
        return [("P1", "P1:counter-shift", clip(d - b)),                 # the actuation disturbance pulls the action back
                ("P2", "P2:price-effort", p2),                           # effort priced 10x (LQR R = 100; half pump gain)
                ("P3", "P3:repair-energy", p3),                          # repair the energy part only while it is off
                ("P4P5", "P4P5:cem", p5),                                # trajectory optimisation, first action
                ("P8", "P8:elite-vote", p8)]                             # median first action of the CEM elites

    def frame(s, st):
        b = s._bias(st); xf = st.get("xf") or st["obs"]; _, _, f5 = s._plans(st)
        return [("F:trace", "F:trace-law", clip(s._law(*xf) - b)),       # the standard law on the trace's state, bias countered
                ("F:traj", "F:traj-cem", f5)]                            # P5 over the trajectory from the trace's state and bias

    def coupled(s, st):
        """Inside the balance basin the action is ONE full-state feedback (angle and velocity drive each other): land it
        as a whole. In swing-up the effort chunks pump one part (energy): per-chunk landing applies."""
        return abs(an(st["obs"][0])) < SW

    # ---------------------------------------------------------------- REAL3 v2 (seed3_ops hooks; HOST_INTERFACE_REAL3v2)
    # Read only by seed3 mode "seed3" (v2); nothing above is changed (REAL1/REAL2 modes and seed3v1 give identical numbers).
    # ONE joint, ONE actuator: the step's torque is the sum of the joint's three control PARTS, the same parts the Law 4
    # landing already uses (targets/retarget): pump = the energy part (swing-up law), angle = angle feedback, damp =
    # velocity feedback (each part's own law = _needs). A part's share of the joint now = |need_p| / sum |need_q|.
    #   parts        : ("pump", "angle", "damp"). No sub-parts (one actuator): ENTER runs at depth 1.
    #   merge        : u = u_std + sum over named parts, in dict order, of (a_p - u_std) * share_p, clipped to the effort
    #                  bank's cap after each part (who comes first gets the cap first); parts not named keep the standard.
    #   part_objective: the part's own error now, negative, on [-1, 0]: pump -|E_up - E| / (2 E_up); angle -|theta| / pi;
    #                  damp -|omega| / 8 (higher = better).
    #   focus        : the whole step's effort (the bank's cap) in the direction of the part's own need: bang on one part.
    #   shape        : (angle band pi/4, velocity band 2 rad/s, energy band E_up/4): where in the swing-up the state is
    #                  (INHERIT: a swing-up sequence that worked is reused at the same band; COMPRESS: the operator that
    #                  worked there).
    #   joint        : the full-state LQR anywhere (angle and velocity served by one feedback).
    #   carry        : a limited to this step's own credit |u_std| (the bank is not drawn now; everything unused is banked
    #                  for a later step: the swing-up's last pumps or the catch).
    #   map_part     : a's deviation from the standard as a fraction of pf's need, re-expressed as the same fraction of
    #                  pt's need.
    #   op_of        : pump/angle/damp -> beam (one part), coast/half -> carry (effort banked), lqr -> fuse (joint).
    PARTS = ("pump", "angle", "damp")

    def parts(s, st): return list(s.PARTS)

    def _share(s, st):
        n = s._needs(st); tot = sum(abs(v) for v in n.values())
        return {p: (abs(n[p]) / tot if tot > 1e-12 else 1.0 / 3) for p in s.PARTS}

    def merge(s, st, d):
        u0 = s.default(st); sh = s._share(st); c = s._cap(st); u = u0
        for p, a in d.items():
            u = max(-c, min(c, u + (float(a) - u0) * sh[p]))
        return float(u)

    def part_objective(s, st, p):
        th, w = st["obs"]
        if p == "pump": return -min(1.0, abs(E_UP - energy(th, w)) / (2 * E_UP))
        if p == "angle": return -abs(an(th)) / math.pi
        return -min(1.0, abs(w) / 8.0)

    def focus(s, st, p):
        v = s._needs(st)[p]; return math.copysign(s._cap(st), v) if abs(v) > 1e-12 else 0.0

    def shape(s, st):
        th, w = st["obs"]
        return (int((an(th) + math.pi) // (math.pi / 4)), int(max(-8.0, min(7.99, w)) // 2),
                int(round((energy(th, w) - E_UP) / (E_UP / 4))))

    def joint(s, st):
        th, w = st["obs"]; return [("lqr", lqr(th, w))]

    def carry(s, st, a):
        return math.copysign(min(abs(float(a)), abs(s.default(st))), float(a))

    def map_part(s, st, a, pf, pt):
        n = s._needs(st); u0 = s.default(st)
        if abs(n[pf]) < 1e-12: return u0
        r = (float(a) - u0) * (1.0 if n[pf] >= 0 else -1.0) / abs(n[pf])
        return u0 + r * n[pt]

    def op_of(s, fam):
        return {"pump": "beam", "angle": "beam", "damp": "beam", "coast": "carry", "half": "carry", "lqr": "fuse"}.get(fam)


CEM_H = 15   # trajectory optimisation horizon (0.75 s): about one pump half-swing; the seed values the result over 100 steps
_P2R = np.array([[100.0]]); _P2P = solve_discrete_are(_A, _B, _Q, _P2R)
K_P2 = np.linalg.solve(_P2R + _B.T @ _P2P @ _B, _B.T @ _P2P @ _A)[0]            # effort priced 10x the standard's R
_QN = (_B @ _B.T) * (SIG_U ** 2) + 1e-8 * np.eye(2); _RN = np.diag([SIG_TH ** 2, SIG_W ** 2])
_PK = solve_discrete_are(_A.T, np.eye(2), _QN, _RN); _KF = _PK @ np.linalg.inv(_PK + _RN)   # steady-state Kalman gain
