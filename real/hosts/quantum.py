"""REAL1 row 4, quantum computing: shot allocation for estimating several observables on real Qiskit benchmark circuits.

HOST
  Six estimation tasks on 4-qubit circuits from qiskit.circuit.library (GHZ, qaoa_ansatz on a 4-ring MaxCut, efficient_su2,
  real_amplitudes, n_local(ry, cz), QFTGate on a random basis state). Each task = (circuit, measurement basis, observable
  O_i = weighted sum of Pauli strings diagonal in that basis, |O_i| <= 1). Circuit parameters, the QFT input state and the
  importance weights w_i (sum 1) are drawn from the cell number. Truth mu_i = exact Statevector expectation (used ONLY by
  report(), never by the seed, default or fork).
  Real step: the chosen shots per task are run on qiskit-aer AerSimulator (seed_simulator from the host's real rng); each
  shot's bitstring gives one value of O_i; the host keeps the per-task histogram of values.
  Start: a pilot of PILOT shots per task (counted as resource). Then T steps of B shots each.
  Action: integer shots per task (length 6); valid() makes it non-negative and sum exactly B (largest remainder).

STANDARD METHOD (default; also the membrane bound)
  Weighted Neyman (variance-proportional) shot allocation with plug-in sample variances, applied sequentially: each step's
  B shots go in chunks of B/20 to the task with the largest reduction of sum_i w_i s_i^2 / n_i (discrete Neyman:
  n_i -> proportional to sqrt(w_i) s_i). Source: Neyman (1934) optimum allocation; in quantum estimation
  Wecker, Hastings, Troyer, PRA 92, 042303 (2015) and Rubin, Babbush, McClean, NJP 20, 053020 (2018) (shots per term
  proportional to |c_i| sigma_i). Variance floor s_i^2 >= 1/(n_i+1) so that a task seen with zero spread is not starved
  forever (standard plug-in safeguard). Second baseline: uniform (Quantum(standard="uniform")), B split equally.

BRANCHES (2-6 focused): focus_i = all B shots of this step on task i, for the 4 tasks with the largest current marginal
  error reduction. No coupled action: the six estimators are statistically independent (separate circuits or bases), so
  no part drives another; offering a fake coupling would be a hidden bonus.

OWN FUTURE (fork; layer-1 rule): the host's model only. Each task's future shots are drawn by bootstrap from the task's
  OWN observed value histogram (its current estimate and spread), with an rng seeded from (cell, t, j, 4041). The fork
  never calls Aer and never sees mu_i.

MEASURE
  result   = 1 - RMSE, RMSE = sqrt(sum_i w_i (est_i - mu_i)^2)  (true error vs exact statevector values)
  resource = shots used (pilot + steps); R = result / resource.
  objective(state) = (1 - sqrt(sum_i w_i s_i^2 / n_i)) / shots used: the same quantity, with the error replaced by the
  model's own expected error (the host cannot know mu_i); this is the expectation of 1 - RMSE under the model.

SIZES (rule 5): 6 tasks, PILOT=20, B=200, T=12, horizon=12 (the whole remaining episode), samples=4. Real steps call Aer
  6 times per step (72 calls per episode); forks are numpy-only. Quick test (4 cells x seed + default + uniform) runs in
  well under a minute here.

REAL2 ADDITIONS (24 Nov; HOST_BRIEF.md REAL2 A and C)
LANDINGS (Law 4, seed.land): one landing = ONE BLOCK OF UP TO 50 SHOTS ON ONE OBSERVABLE: id (i, k) = shots
  [50k, min(50(k+1), a_i)) of task i in this step's action (B=200 -> at most 4 + 6 = 10 landings, usually 5-7).
  without(L): those shots are not taken (fixed-budget row: the unused shots are lost; resource falls).
  targets(L): up to 3 other tasks, highest need first = the largest weighted Neyman marginal error reduction
    w_j s_j^2 (1/(n_j+a_j) - 1/(n_j+a_j+|L|)) with the action already counted (the standard's own criterion).
  retarget(L, T): the block's shots move from task i to task T (same shots).
  To make "without" possible valid() now keeps an action that spends LESS than B (it only scales down an action over
  B, or an empty one up to B); every REAL1 action (default, branches, past, own plan) spends exactly B, so REAL1 modes
  are unchanged.
  objective(state) = 1 - sqrt(sum_i w_i s_i^2 / n_i) (the RESULT only, rule 4). REAL1's version divided this by the
  shots used; with every action at exactly B the shots used at the horizon are the same for every branch of a
  decision, so the ranking (and seed_noland) is unchanged, but with landings the division would reward withholding
  shots (a hidden bonus), so it is removed.
STRONGEST (Quantum(standard="strongest") = the Neyman standard above, the same code): for a fixed shot budget over
  independent estimators, Neyman / variance-proportional allocation (n_i ~ sqrt(w_i) sigma_i) minimises the weighted
  variance sum_i w_i sigma_i^2 / n_i exactly (Neyman 1934; Cochran, Sampling Techniques, 3rd ed. 1977, ch. 5.5), and it
  is the allocation used for shot budgets in quantum estimation (Wecker et al. 2015; Rubin et al. 2018, cited above). Applied
  sequentially with plug-in variances it is already the strongest standard available; no new method is added.
  Check (24 Nov, cells 1-8): with the TRUE variances (statevector) the expected RMSE of the shots default ends with
  equals the oracle Neyman allocation to 4 digits in every cell (e.g. cell 1: 0.0218 vs 0.0218; uniform 0.0230), so
  in expectation this host leaves almost no headroom above the standard; per-cell realised RMSE differences (uniform
  beat Neyman in 6/8 single realisations) are realisation noise of one Aer run.

REAL3 (24 Nov; HOST_BRIEF.md REAL3; seed3.py binding). REAL1/REAL2 modes are unchanged (every REAL2 action has length K
  and takes the old code paths verbatim; checked: cell 1 seed/seed_noland/rollout/default equal quick_logs/quantum_real2.txt).
WHAT SHARES (stated precisely). Within one task the observable is already a qubit-wise commuting (QWC) group: all its
  Pauli terms are diagonal in the task's one basis, so every shot already informs every term, and the standard (Neyman
  over the six groups) already uses that joint measurement. ACROSS tasks no two observables share a state: the six
  circuits differ (and same-basis tasks ghz/realamp/qft or qaoa/su2 are different states), so no shot of one 4-qubit
  circuit can inform another task. The joint setting that does exist with the same tool: place several tasks' rotated
  circuits on DISJOINT 4-qubit blocks of one wider circuit and measure all qubits in one shot. The prepared state is the
  product of the blocks, so each block's marginal is exactly its task's state (truth mu_i unchanged, scored the same way),
  and the observables O_i (x) I are QWC on the joint register (disjoint supports; each qubit in one Pauli basis). One shot
  of the joint setting = one shot of the budget and one sample for EVERY member.
  GROUPS: X = {ghz_X, realamp_XX, qft_X} (12 qubits, one global X basis), Z = {qaoa_ring_ZZ, su2_Z} (8 qubits, global Z),
  ALL = all six (24 qubits; per-block basis, still one Pauli setting). Joint circuits run on AerSimulator
  method="matrix_product_state" (exact for these product states; statevector on 24 qubits takes ~4 s per call vs 0.05 s).
  Frame change made explicit: register width 4 -> 8/12/24 qubits per shot; shots (the counted resource) are the same B
  per step and the same total 2520. Width is not a counted resource of this row; on hardware, crosstalk between blocks
  would be the cost (here: none, Aer is ideal).
ACTION (joint form): length K + G = [shots on each task's own circuit (6), shots on each group setting X, Z, ALL (3)];
  valid() keeps a non-negative integer joint action within B, else scales it to B (largest remainder); resource = shots.
  step(): own circuits as before, then one Aer run per used group, the bitstring split into blocks. fork(): the joint
  state is a product, so the model bootstraps every member independently from its own histogram (same model as REAL2).
  Landings: blocks of 50 shots on any setting (task circuit or group); targets = settings by summed marginal reduction.
FRAME (family "F:joint"): F:joint-greedy = discrete Neyman greedy over all 9 settings, a setting's gain = the summed
  weighted variance reduction of every task its shots inform (it chooses ALL whenever every task still has variance);
  F:joint-basis = the same greedy over own circuits + X + Z only (the brief's literal "shared basis" grouping);
  F:joint-all = all B shots on ALL.
PRIMITIVES (REAL2 form, own circuits only): P1 counter-shift (shots proportional to each task's error share
  w s^2/n); P2 price on harm (Neyman greedy with gains x (1 + error share / mean share)); P3 repair (half the Neyman
  action, the rest to the worst task); P4P5 horizon Neyman (the final optimal allocation over ALL remaining shots,
  this step fills the deficits: joint choice over the horizon, value carried back from the end); P8 vote of futures
  (mean of the Neyman actions under 8 bootstrap resamples of the variances, rng (cell, t, 4043)). P6/P7 are seed3's own
  (pool order, apoptosis). O trace across steps = seed3's POOL. coupled() = False: the estimators are independent; a
  joint setting is one landing unit (whole block), so per-part landing never splits a shared shot.
"""
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import library as L
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_aer import AerSimulator

NQ = 4


def _ghz(rng):
    qc = QuantumCircuit(NQ); qc.h(0)
    for q in range(NQ - 1): qc.cx(q, q + 1)
    return qc


def _bind(circ, rng):
    return circ.assign_parameters(rng.uniform(0, 2 * np.pi, circ.num_parameters))


def _qaoa(rng):
    ring = SparsePauliOp.from_sparse_list([("ZZ", [i, (i + 1) % NQ], 1.0) for i in range(NQ)], NQ)
    return _bind(L.qaoa_ansatz(ring, reps=2).decompose(reps=3), rng)


def _su2(rng): return _bind(L.efficient_su2(NQ, reps=2), rng)
def _ra(rng): return _bind(L.real_amplitudes(NQ, reps=2), rng)
def _nl(rng): return _bind(L.n_local(NQ, "ry", "cz", reps=2), rng)


def _qft(rng):
    qc = QuantumCircuit(NQ); x = int(rng.integers(1, 2 ** NQ))
    for q in range(NQ):
        if (x >> q) & 1: qc.x(q)
    qc.append(L.QFTGate(NQ), range(NQ)); return qc.decompose(reps=2)


def _zz(i, j, c): return ("ZZ", [i, j], c)
def _z(i, c): return ("Z", [i], c)
def _zzzz(c): return ("ZZZZ", [0, 1, 2, 3], c)


# (name, circuit builder, basis 'Z'|'X'|'Y', observable terms written in Z form = Pauli of that basis after rotation)
TASKS = [
    ("ghz_X", _ghz, "X", [_zzzz(0.5), _zz(0, 1, 0.5)]),
    ("qaoa_ring_ZZ", _qaoa, "Z", [_zz(i, (i + 1) % NQ, 0.25) for i in range(NQ)]),
    ("su2_Z", _su2, "Z", [_z(i, 0.25) for i in range(NQ)]),
    ("realamp_XX", _ra, "X", [_zz(0, 1, 0.34), _zz(1, 2, 0.33), _zz(2, 3, 0.33)]),
    ("nlocal_Y", _nl, "Y", [_zz(0, 1, 0.5), _zz(2, 3, 0.5)]),
    ("qft_X", _qft, "X", [_z(i, 0.25) for i in range(NQ)]),
]
K = len(TASKS)
# REAL3 JOINT SETTINGS (docstring): each group = tasks placed on disjoint 4-qubit blocks of ONE wider circuit, measured
# in one shot; the group's observables are qubit-wise commuting (disjoint supports, each qubit in one Pauli basis).
GROUPS = [("X", (0, 3, 5)), ("Z", (1, 2)), ("ALL", (0, 1, 2, 3, 4, 5))]
G = len(GROUPS)
# REAL3 FAIRNESS (24 Nov 21:55, before any REAL3 seal): a group shot uses len(idx) 4-qubit blocks of hardware, so by
# default it is COUNTED as len(idx) shots (equal hardware use = 4-qubit-shots). REAL3_QUANTUM_WIDTH_FREE=1 restores the
# width-free frame (reported only as a labelled frame-change variant, never as the sealed comparison).
import os as _os
WIDTH_FREE = _os.environ.get("REAL3_QUANTUM_WIDTH_FREE", "0") == "1"
COST = np.array([1] * K + [1 if WIDTH_FREE else len(idx) for _, idx in GROUPS])


def _rotate(qc, basis):
    m = qc.copy()
    if basis == "X":
        m.h(range(NQ))
    elif basis == "Y":
        m.sdg(range(NQ)); m.h(range(NQ))
    return m


def _values_table(terms):
    """value of the observable for each of the 2^NQ outcomes (integer outcome, qubit q = bit q)."""
    v = np.zeros(2 ** NQ)
    for k in range(2 ** NQ):
        for _, qubits, c in terms:
            v[k] += c * (-1) ** sum((k >> q) & 1 for q in qubits)
    return v


class Quantum:
    horizon = 12; samples = 4

    def __init__(s, B=200, T=12, PILOT=20, standard="neyman"):
        s.B, s.T, s.PILOT, s.standard = B, T, PILOT, standard
        s.sim = AerSimulator(); s._cells = {}

    # ---------------------------------------------------------------- cell setup (circuits, truth, Aer circuits)
    def _cell(s, cell):
        if cell in s._cells: return s._cells[cell]
        rng = np.random.default_rng([cell, 4040]); tasks = []
        w = rng.uniform(0.5, 2.0, K); w = w / w.sum()
        for (name, build, basis, terms) in TASKS:
            qc = build(rng); rot = _rotate(qc, basis)
            op = SparsePauliOp.from_sparse_list(terms, NQ)
            mu = float(np.real(Statevector(rot).expectation_value(op)))   # truth: report() only
            meas = rot.copy(); meas.measure_all()
            tasks.append({"name": name, "circ": transpile(meas, s.sim, optimization_level=1),
                          "vals": _values_table(terms), "mu": mu, "rot": rot})   # REAL3: rot kept for joint settings
        s._cells[cell] = (tasks, w); return s._cells[cell]

    def _shots(s, st, i, n, seed):
        if n <= 0: return np.zeros(2 ** NQ)
        tasks, _ = s._cell(st["cell"])
        counts = s.sim.run(tasks[i]["circ"], shots=int(n), seed_simulator=int(seed)).result().get_counts()
        h = np.zeros(2 ** NQ)
        for key, c in counts.items(): h[int(key.replace(" ", ""), 2)] += c
        return h

    # ---------------------------------------------------------------- interface
    def reset(s, cell):
        tasks, w = s._cell(cell)
        st = {"t": 0, "cell": cell, "rng": np.random.default_rng([cell, 4042]), "model": False,
              "hist": np.zeros((K, 2 ** NQ)), "used": 0}
        for i in range(K):
            st["hist"][i] += s._shots(st, i, s.PILOT, st["rng"].integers(2 ** 31)); st["used"] += s.PILOT
        return st

    def done(s, st): return st["t"] >= s.T

    def _stats(s, st):
        tasks, w = s._cell(st["cell"]); n = st["hist"].sum(1); est = np.zeros(K); var = np.zeros(K)
        for i in range(K):
            p = st["hist"][i] / max(n[i], 1); v = tasks[i]["vals"]
            est[i] = p @ v; var[i] = max(p @ (v - est[i]) ** 2 * n[i] / max(n[i] - 1, 1), 0.0)
        return n, est, np.maximum(var, 1.0 / (n + 1)), w

    def default(s, st):
        if s.standard == "uniform":
            return [s.B // K + (1 if i < s.B % K else 0) for i in range(K)]
        n, _, var, w = s._stats(st); x = np.zeros(K, dtype=int); c = s.B // 20
        for _ in range(20):
            gain = w * var * (1.0 / (n + x) - 1.0 / (n + x + c)); x[int(np.argmax(gain))] += c
        x[int(np.argmax(w * var / (n + x)))] += s.B - x.sum()
        return list(x)

    def branches(s, st):
        n, _, var, w = s._stats(st); gain = w * var * (1.0 / n - 1.0 / (n + s.B))
        out = []
        for i in np.argsort(-gain)[:4]:
            a = [0] * K; a[int(i)] = s.B; out.append((f"focus_{TASKS[int(i)][0]}", a))
        return out

    def valid(s, st, a):
        if np.asarray(a).reshape(-1).size == K + G + 1:                       # REAL3 v2 carry form (CARRY hook)
            return s._valid_joint(list(a)[:K + G]) + [int(list(a)[-1] != 0)]
        if np.asarray(a).reshape(-1).size == K + G: return s._valid_joint(a)   # REAL3 joint form (docstring)
        x = np.maximum(np.asarray(a, dtype=float).reshape(-1)[:K], 0)
        if x.sum() <= 0: x = np.ones(K)
        elif x.size == K and x.sum() <= s.B and np.all(x == np.floor(x)):
            return [int(v) for v in x]   # REAL2: an integer action within B is kept (a landed action may spend < B)
        x = x * s.B / x.sum(); f = np.floor(x).astype(int)
        for i in np.argsort(-(x - f))[: s.B - f.sum()]: f[i] += 1
        return [int(v) for v in f]

    # ---- REAL2 Law 4 landing interface (seed.land): one landing = a block of up to 50 shots on one observable ----
    BLOCK = 50

    def landings(s, st, a):
        return [(i, k) for i in range(min(len(a), K + G)) for k in range(-(-int(a[i]) // s.BLOCK))]   # K or K+G (+ flag)

    def _block(s, a, L):
        i, k = L; return max(0, min(s.BLOCK, int(a[i]) - s.BLOCK * k))

    def without(s, st, a, L):
        b = [int(v) for v in a]; b[L[0]] -= s._block(a, L); return b

    def targets(s, st, a, L):
        if len(a) >= K + G: return s._targets_joint(st, list(a)[:K + G], L)        # REAL3 joint form (+ carry flag)
        n, _, var, w = s._stats(st); m = s._block(a, L); x = np.asarray(a, dtype=float)
        gain = w * var * (1.0 / (n + x) - 1.0 / (n + x + m))
        return [int(j) for j in np.argsort(-gain) if int(j) != L[0]][:3]

    def retarget(s, st, a, L, T):
        b = [int(v) for v in a]; m = s._block(a, L); b[L[0]] -= m; b[T] += m; return b

    def step(s, st, a):
        if len(a) == K + G + 1 or st.get("bank", 0): return s._step_carry(st, a)    # REAL3 v2 carry / bank
        if len(a) == K + G: return s._step_joint(st, a)                             # REAL3 joint form
        st = dict(st); st["hist"] = st["hist"].copy()
        for i, n in enumerate(a):
            if n <= 0: continue
            if st["model"]:   # own model: bootstrap from the task's own observed histogram
                p = st["hist0"][i] / st["hist0"][i].sum(); st["hist"][i] += st["rng"].multinomial(n, p)
            else:             # real host: Aer shots
                st["hist"][i] += s._shots(st, i, n, st["rng"].integers(2 ** 31))
        st["used"] += int(sum(a)); st["t"] += 1; return st

    def fork(s, st, j):
        f = dict(st); f["hist"] = st["hist"].copy(); f["hist0"] = st["hist"].copy(); f["model"] = True
        f["rng"] = np.random.default_rng([st["cell"], st["t"], j, 4041]); return f

    def objective(s, st):
        n, _, var, w = s._stats(st)
        return 1.0 - np.sqrt(np.sum(w * var / n))   # REAL2: result only (REAL1 divided by the shots used; docstring)

    def report(s, st):
        tasks, w = s._cell(st["cell"]); _, est, _, _ = s._stats(st)
        mu = np.array([t["mu"] for t in tasks])
        rmse = float(np.sqrt(np.sum(w * (est - mu) ** 2)))
        return {"result": 1.0 - rmse, "resource": float(st["used"]), "rmse": rmse,
                "shots_per_task": [int(v) for v in st["hist"].sum(1)], "joint_shots": int(st.get("joint_shots", 0)),
                "carried_shots": int(st.get("carried", 0))}

    # ================================================================ REAL3 (seed3 binding; docstring "REAL3")
    def _joint_circ(s, cell, g):
        key = ("joint", cell, g)
        if key not in s._cells:
            tasks, _ = s._cell(cell); idx = GROUPS[g][1]; qc = QuantumCircuit(NQ * len(idx))
            for b, i in enumerate(idx): qc.compose(tasks[i]["rot"], qubits=range(NQ * b, NQ * b + NQ), inplace=True)
            qc.measure_all()
            if not hasattr(s, "sim_joint"): s.sim_joint = AerSimulator(method="matrix_product_state")
            s._cells[key] = transpile(qc, s.sim_joint, optimization_level=1)
        return s._cells[key]

    def _joint_shots(s, st, g, n, seed):
        """Aer shots of the joint setting g; each shot's bitstring split into the blocks = one outcome per member task."""
        circ = s._joint_circ(st["cell"], g)
        counts = s.sim_joint.run(circ, shots=int(n), seed_simulator=int(seed)).result().get_counts()
        idx = GROUPS[g][1]; h = np.zeros((len(idx), 2 ** NQ))
        for key, c in counts.items():
            k = int(key.replace(" ", ""), 2)
            for b in range(len(idx)): h[b, (k >> (NQ * b)) & (2 ** NQ - 1)] += c
        return h

    def _samples(s, a):
        """samples each task receives from an action (REAL2 form: = a; joint form: own shots + shots of its groups)."""
        a = np.asarray(a, dtype=float); x = a[:K].copy()
        if a.size == K + G:
            for g, (_, idx) in enumerate(GROUPS): x[list(idx)] += a[K + g]
        return x

    def _step_joint(s, st, a):
        st = dict(st); st["hist"] = st["hist"].copy()
        for i in range(K):
            n = int(a[i])
            if n <= 0: continue
            if st["model"]:
                p = st["hist0"][i] / st["hist0"][i].sum(); st["hist"][i] += st["rng"].multinomial(n, p)
            else:
                st["hist"][i] += s._shots(st, i, n, st["rng"].integers(2 ** 31))
        for g, (_, idx) in enumerate(GROUPS):
            n = int(a[K + g])
            if n <= 0: continue
            if st["model"]:   # own model: the joint state is a product of the blocks -> independent bootstrap per member
                for i in idx:
                    p = st["hist0"][i] / st["hist0"][i].sum(); st["hist"][i] += st["rng"].multinomial(n, p)
            else:             # real host: one Aer run of the joint circuit; one shot informs every member
                h = s._joint_shots(st, g, n, st["rng"].integers(2 ** 31))
                for b, i in enumerate(idx): st["hist"][i] += h[b]
        st["used"] += int(sum(int(v) * int(c) for v, c in zip(a, COST))); st["t"] += 1
        st["joint_shots"] = st.get("joint_shots", 0) + int(sum(int(v) for v in a[K:])); return st

    def _valid_joint(s, a):
        x = np.maximum(np.asarray(a, dtype=float).reshape(-1), 0)
        if x.sum() <= 0: x = np.ones(K + G)
        elif x @ COST <= s.B and np.all(x == np.floor(x)): return [int(v) for v in x]
        x = x * s.B / (x @ COST); f = np.floor(x).astype(int)
        for i in np.argsort(-(x - f)):                       # largest remainder, within the cost-weighted budget
            if f @ COST + COST[i] <= s.B: f[i] += 1
        return [int(v) for v in f]

    def _targets_joint(s, st, a, L):
        n, _, var, w = s._stats(st); m = s._block(a, L); x = s._samples(a)
        d = w * var * (1.0 / (n + x) - 1.0 / (n + x + m))
        gain = np.array(list(d) + [d[list(idx)].sum() for _, idx in GROUPS])
        return [int(j) for j in np.argsort(-gain) if int(j) != L[0]][:3]

    def _greedy(s, st, settings, var=None, mult=None):
        """discrete Neyman greedy over 'settings' (indices into the joint form; < K = a task's own circuit, >= K = a
        group); a setting's gain = the summed weighted variance reduction of every task its shots inform."""
        n, _, v0, w = s._stats(st); var = v0 if var is None else var; mult = np.ones(K) if mult is None else mult
        a = np.zeros(K + G, dtype=int); c = s.B // 20
        mem = [[j] if j < K else list(GROUPS[j - K][1]) for j in range(K + G)]
        kk = [max(1, c // int(COST[j])) for j in range(K + G)]   # shots of one increment: same counted cost c
        while True:                                                 # gain per counted shot (COST: equal hardware use)
            x = s._samples(a)
            ok = [j for j in settings if a @ COST + kk[j] * COST[j] <= s.B]
            if not ok: break
            j = max(ok, key=lambda j: (mult * w * var * (1.0 / (n + x) - 1.0 / (n + x + kk[j])))[mem[j]].sum())
            a[j] += kk[j]
        x = s._samples(a); left = s.B - int(a @ COST)
        j = max(settings, key=lambda j: (mult * w * var / (n + x))[mem[j]].sum() / COST[j]); a[j] += left // int(COST[j])
        left = s.B - int(a @ COST)
        if left > 0: a[int(np.argmax([(mult * w * var / (n + x))[i] for i in range(K)]))] += left
        return [int(v) for v in a]

    def primitives(s, st):
        """Library primitives (map Part I.2) bound to the shot levers; all in the REAL2 form (own circuits only)."""
        if s.done(st): return []
        n, _, var, w = s._stats(st); e = w * var / n; out = []
        out.append(("P1", "P1:counter-shift", list(e / e.sum() * s.B)))                       # shots pulled by error share
        lam = e / e.mean()
        out.append(("P2", "P2:price-on-harm", s._greedy(st, range(K), mult=1.0 + lam)[:K]))  # price rises with the harm
        worst = int(np.argmax(e)); half = s._greedy(st, range(K))[:K]
        rep = [int(v) // 2 for v in half]; rep[worst] += s.B - sum(rep)
        out.append(("P3", "P3:repair-worst", rep))                                            # repair only the worst part
        N = n.sum() + s.B * (s.T - st["t"]); tgt = N * np.sqrt(w * var) / np.sqrt(w * var).sum()
        deficit = np.maximum(tgt - n, 0)
        if deficit.sum() > 0:                                                                 # joint choice over the horizon
            out.append(("P4P5", "P4P5:horizon-neyman", list(deficit / deficit.sum() * s.B)))
        rng = np.random.default_rng([st["cell"], st["t"], 4043]); acc = np.zeros(K)
        for _ in range(8):                                                                    # vote of 8 resampled futures
            vb = np.zeros(K)
            for i in range(K):
                p = st["hist"][i] / n[i]; hb = rng.multinomial(int(n[i]), p) / n[i]; vals = s._cell(st["cell"])[0][i]["vals"]
                m = hb @ vals; vb[i] = max(hb @ (vals - m) ** 2 * n[i] / max(n[i] - 1, 1), 1.0 / (n[i] + 1))
            acc += np.array(s._greedy(st, range(K), var=vb)[:K])
        out.append(("P8", "P8:vote-of-futures", list(acc / 8)))
        return out

    def frame(s, st):
        """F:joint = JOINT MEASUREMENT (docstring REAL3): shots on a shared setting inform every observable of the group."""
        if s.done(st): return []
        allg = s._greedy(st, range(K + G))
        basis = s._greedy(st, [j for j in range(K + G) if j < K or GROUPS[j - K][0] != "ALL"])
        whole = [0] * (K + G); gi = [g for g, (nm, _) in enumerate(GROUPS) if nm == "ALL"][0]; whole[K + gi] = s.B // int(COST[K + gi])
        return [("F:joint", "F:joint-greedy", allg), ("F:joint", "F:joint-basis", basis), ("F:joint", "F:joint-all", whole)]

    def coupled(s, st):
        return False   # the six estimators are independent; a joint setting is landed as whole blocks (docstring)

    # ================================================================ REAL3 v2 hooks (real/HOST_INTERFACE_REAL3v2.md)
    # PARTS = the six estimation tasks (ids 0..5). SUB-PARTS of task p (ENTER depth 2) = the measurement settings by which
    # samples reach p: ("own", p) = p's own circuit, ("grp", g, p) = joint setting g (X / Z / ALL) that contains p. A
    # sub-part is a real lever: the same samples of p can come from its own circuit (1 counted shot each) or from a group
    # setting (len(group) counted shots each by default, but informing the other members too). The Pauli terms of one
    # observable and its qubits are NOT offered as sub-parts: every shot of a task's circuit already measures all its
    # terms on all 4 qubits (one QWC basis), so there is no separate lever for a term or a qubit block.
    # MERGE: in dict order, each named part takes the settings of its action that inform it (own circuit + its groups;
    # a setting already taken by an earlier part is shared, max not sum: one joint shot serves every member), within the
    # step budget B (cost-weighted; COST table, width counted by default); the rest of B goes to the standard rule
    # (Neyman greedy, own circuits) over the parts not named (all parts if every part is named), counting the samples the
    # named settings already give them. merge(s, {}) == default(s) exactly.
    # CARRY: action form length K + G + 1, last entry 1 = "bank this step's unspent shots" (the host's state holds the
    # bank; it is spent at the next step by the standard rule on top of that step's action; forced spent at the last
    # step). Only an action spending < B has anything to carry (a landed action with withheld blocks; a group-only action
    # whose width does not divide B). Every REAL1/REAL2 action spends exactly B and never sets the flag or the bank.
    def _task_of(s, p): return p if not isinstance(p, tuple) else p[-1]

    def _settings_of(s, p):
        if not isinstance(p, tuple): return [p] + [K + g for g, (_, idx) in enumerate(GROUPS) if p in idx]
        return [p[1]] if p[0] == "own" else [K + p[1]]

    def _asjoint(s, a):
        x = np.asarray(a, dtype=float).reshape(-1)[:K + G]
        return np.concatenate([x, np.zeros(K + G - x.size)]) if x.size < K + G else x

    def _fill(s, st, x, tasks, rem):
        """the standard's rule (discrete Neyman greedy, chunks of B/20, own circuits) for `rem` counted shots over
        `tasks`, counting the samples x already gives; the remainder to the task with the largest w s^2/n."""
        n, _, var, w = s._stats(st); x = np.array(x, dtype=int); c = s.B // 20; mask = np.full(K, -np.inf)
        mask[list(tasks)] = 0.0
        while rem >= c and c > 0:
            sm = s._samples(x); gain = w * var * (1.0 / (n + sm) - 1.0 / (n + sm + c)) + mask
            x[int(np.argmax(gain))] += c; rem -= c
        if rem > 0:
            sm = s._samples(x); x[int(np.argmax(w * var / (n + sm) + mask))] += rem
        return x

    def _out(s, x):
        x = [int(v) for v in x]
        return x[:K] if sum(x[K:]) == 0 else x

    def parts(s, st, within=None):
        if within is None: return list(range(K))
        p = s._task_of(within)
        return [("own", p)] + [("grp", g, p) for g, (_, idx) in enumerate(GROUPS) if p in idx]

    def merge(s, st, d):
        x = np.zeros(K + G, dtype=int); rem = s.B; named = set()
        for p, a in d.items():
            aj = s._asjoint(a); named.add(s._task_of(p))
            for j in s._settings_of(p):
                add = min(max(0, int(round(aj[j])) - int(x[j])), rem // int(COST[j]))
                x[j] += add; rem -= add * int(COST[j])
        tasks = [i for i in range(K) if i not in named] or list(range(K))
        return s._out(s._fill(st, x, tasks, rem))

    def part_objective(s, st, p):
        n, _, var, w = s._stats(st); i = s._task_of(p)
        return -float(w[i] * var[i] / n[i])      # minus the task's share of the model's weighted error (higher = better)

    def focus(s, st, p):
        a = [0] * K; a[s._task_of(p)] = s.B; return a   # all B shots on the task's own circuit (cheapest per sample)

    def shape(s, st):
        n, _, var, w = s._stats(st); e = w * var / n; share = e / e.sum()
        return (int(st["t"]), tuple(int(min(4, v * 10)) for v in share))   # step + per-task error-share band (0.1 wide)

    def joint(s, st):
        out = []
        for g, (nm, _) in enumerate(GROUPS):
            x = np.zeros(K + G, dtype=int); x[K + g] = s.B // int(COST[K + g])
            out.append((f"joint-{nm}", s._out(s._fill(st, x, range(K), s.B - int(x @ COST)))))
        return out

    def carry(s, st, a):
        aj = s._asjoint(s.valid(st, a)); return [int(v) for v in aj] + [1]

    def map_part(s, st, a, pf, pt):
        b = [0] * K; b[s._task_of(pt)] = int(round(s._samples(s._asjoint(a))[s._task_of(pf)])); return b

    def op_of(s, fam):
        if fam.startswith("focus_"): return "beam"      # all B shots on one task = BEAM 1
        if fam == "F:joint": return "fuse"              # one shot serves several observables = FUSE
        return None

    def _step_carry(s, st, a):
        """REAL3 v2 CARRY: a carry-form action spends its settings and banks B - its cost; a banked amount is spent at
        the next step by the standard rule (_fill over all tasks) on top of that step's action; at the last step
        everything is spent. The bank never exceeds B."""
        flag = len(a) == K + G + 1 and int(a[-1]) != 0; x = np.array([int(v) for v in s._asjoint(a)], dtype=int)
        bank = int(st.get("bank", 0)); last = st["t"] >= s.T - 1
        unused = max(0, s.B - int(x @ COST)) if flag else 0
        if flag and not last: spend, new_bank = 0, min(s.B, bank + unused)   # carry again: the bank keeps growing
        else: spend, new_bank = bank + unused, 0
        if spend > 0: x = s._fill(st, x, range(K), spend)
        st2 = s._step_joint(st, [int(v) for v in x]); st2["bank"] = new_bank
        st2["carried"] = st.get("carried", 0) + (new_bank - bank if new_bank > bank else 0); return st2
