"""REAL1 row 10, "life science": the 8 real hosts of ORG-REAL1 (experiments/allnodes/real6.py, sealed f80259e) bound
to the seed interface.

WHAT THE 8 HOSTS ARE (read from real6.py / PREREG_REAL1.md, not assumed): noisy-label supervised learning on four
offline scikit-learn datasets x two label-noise kinds = 8 hosts: breast cancer (Wisconsin diagnostic, biology),
iris (Fisher, biology), wine (chemical analysis of three cultivars, agricultural chemistry) and digits (handwritten
digits, NOT biology), each x sym25 / asym30. The datasets are made hard by real6.hard() exactly as sealed (train split
only: every second class cut by 70 %, then 25 % symmetric or 30 % next-class label noise; validation and test clean).
The learner is the sealed one: SGDClassifier log loss, constant rate 0.05, warm start of 2 examples per class
(sec1_real_v4.new), 300 steps, batch of 16 drawn uniformly. "Biology" in ORG-REAL1 named the organism-structure
family that was tested (Level C / Biology), not the data domain: only cancer and iris are life-science data.

UNITS, BUDGET, RESOURCE, RESULT (row kind: FREE-RESOURCE, compute; brief rule 4: pass per cell = Pareto, result >=
standard AND resource <= standard, at least one strictly. valid() caps every step at the standard's own count, so
resource <= standard holds by construction and a pass needs a strictly higher result, or the same result with fewer
examples)
  units    : the training examples (grouped in parts = classes; the noise couples classes)
  budget   : examples landed per step = round(16 (1 - r)) with r the true noise rate (12 for sym25, 11 for asym30),
             i.e. exactly what the standard method trains on per step; valid() keeps the first `budget` distinct
             in-range indices
  resource : examples landed in gradient steps over the episode (training compute; the standard spends 300 x budget)
  result   : test accuracy at the end (clean test split, the ORG-REAL1 measure)
  objective(state) = validation accuracy only (the result's own measure on the clean validation split the ORG-REAL1
             methods already use; never divided by the resource; the test split is never read before report)

STANDARD METHOD (default) = the best native method of ORG-REAL1: small-loss selection + decaying rate
("smallloss_decay" in real6.BASE: keep the round(16 (1 - r)) lowest-loss examples of the batch, rate 0.05 / (1 + t/100),
given the TRUE noise rate, as in ORG-REAL1). Source: RESULTS_REAL1.md "best single method 0.838 (small-loss+decay)"
over the 64 evaluation rows (recomputed from RAW6_eval_p*.json: smallloss_decay 0.8376, coteach_decay 0.8366,
smallloss 0.8342, coteach 0.8252, cl_decay 0.8208, cl 0.8133, decay 0.7444, plain 0.719, ohem 0.6614). Reproduction
check: Biology(data_seed=11100).run in "default" mode gives exactly the RAW6 smallloss_decay values for seed 11100
(same split, same warm start, same batches drawn in the same order from default_rng(seed)).
Not used as the standard: the "oracle best of 9 per run" bar of ORG-REAL1 (a post-hoc choice, not a method).
Disclosed: on iris confident learning is better per host (0.725 / 0.828 vs 0.653 / 0.753), on cancer/asym30
co-teaching+decay is marginally better; one standard for all 8 hosts is used, as ORG-REAL1's "best single method".

BRANCHES (all exactly `budget` examples, same rate schedule as the standard):
  focused : weak1 / weak2 = the budget lowest-loss examples labelled as the weakest / second weakest class on
            validation (pool: the batch plus 2 x budget examples of that class drawn from rng [cell, t, c, 1031]);
            barrier = small-loss inside the batch after removing examples the memory marks as suspicious (memory
            of past mistakes > 3: the ORG-REAL1 barrier role); clean = the budget lowest loss x (1 + memory) over
            the whole training set
  coupled : pair = the most confused class pair on validation (a -> b), half the budget small-loss from each of a and b
            (the noise drives classes into each other; asym30 is a next-class flip)

OWN FUTURE (fork): a copy of the learner (the host's own model, fitted only on data seen up to now; the training set
is the host's present data, nothing from the test split) continued on batches drawn from an independent rng
np.random.default_rng([cell, t, j, 1077]), never from the real batch sampler. The current batch (already drawn,
present) is known to both.

CELLS: cell c -> host HOSTS[(c - 1) % 8] (cancer/sym25, cancer/asym30, wine/sym25, wine/asym30, digits/sym25,
digits/asym30, iris/sym25, iris/asym30), data seed 12000 + c (fresh: ORG-REAL1 used 11000-11001 and 11100-11107).
Development cells 1-4 therefore cover cancer and wine only; cells 5-8 cover digits and iris.

SIZE (rule 5): the sealed episode (300 steps of 16) is kept; horizon 3 steps (ORG-REAL1's own forks looked 10 ahead;
horizon 5 took 4 min for the quick check, over the 3-minute limit), samples 2; forks skip the memory update
(default() does not read it). About 30 s per seed episode here; the laptop run can use horizon 10. (REAL2: with
seed.TREE = 8 forks the seed episode takes about 110 s without landing and about 2.5-3 min with it, cancer/wine.)

LAW 4 LANDING (REAL2 A, 24 Nov; seed.land)
  landings : one batch group per class in the step = the examples of the action that carry one (noisy) label
             (2 landings on cancer, up to 3 on wine/iris, up to 10 on digits).
  without  : the action without that class's group (fewer examples trained on: resource saved).
  targets  : up to 3 other classes, highest need first = lowest per-class accuracy on the clean validation split
             (the split the objective and the weak branches already read; the test split is never read).
  retarget : the group's count of examples moved to class T: the lowest-loss examples labelled T from the batch plus
             the weak-branch pool of T (rng [cell, t, T, 1031], never the real batch sampler); same count.

STRONGEST METHOD (REAL2 C): the standard (small-loss + decay) is the strongest single method measured in ORG-REAL1 on
  these hosts (0.8376 mean test accuracy over 64 rows, ahead of co-teaching + decay 0.8366 and confident learning +
  decay 0.8208). Stronger noisy-label methods in the literature (DivideMix, ELR, SOP) are semi-supervised / regularised
  schemes built for deep networks with augmentation; they are not standard for a linear SGD learner at a fixed
  per-step example budget and could not be implemented faithfully and quickly here. The standard is kept.

REAL3 (24 Nov; seed3.run binds primitives / frame / coupled; REAL1/REAL2 modes unchanged, checked: default cell 1
0.8713). Check of the REAL2 landing artefact: real/hosts/biology_landing_check.py (see the REAL3 block in the class).
  primitives: P1 deficit share (budget split by per-class validation deficit), P2 price on repeated mistakes,
    P8 vote of futures on the data landing (withhold a class group only if withholding wins strictly in most of the
    TREE futures; ties keep it).
  frame: F:need (DATA LANDING: train only the classes not yet perfect on validation; fewer examples) and F:need-fill.
  coupled: True on asym30 (next-class flip), False on sym25."""
import os, sys, copy
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__)); _ALL = os.path.join(_HERE, "..", "..", "experiments", "allnodes")
_cwd = os.getcwd(); sys.path.insert(0, os.path.abspath(_ALL))
try:
    import real6 as R6                                      # sealed ORG-REAL1 code (hash-checked on import)
finally:
    os.chdir(_cwd)
R, V4 = R6.R, R6.V4

class Biology:
    horizon = 3; samples = 2
    HOSTS = R6.HOSTS
    def __init__(s, data_seed=None): s.data_seed = data_seed     # data_seed only for the reproduction check

    def reset(s, cell):
        cell = int(cell); host = s.HOSTS[(cell - 1) % 8]; seed = s.data_seed if s.data_seed is not None else 12000 + cell
        D = R6.hard(*host, seed); Xtr, ytr, Xva, yva, Xte, yte, classes = D
        rng = np.random.default_rng(seed); r = R6.RATE[host[1]]
        st = {"t": 0, "cell": cell, "host": host, "D": D, "rng": rng, "r": r, "k": int(round(R.B * (1 - r))),
              "clf": V4.new(classes, seed, Xtr, ytr), "mem": np.zeros(len(Xtr)), "used": 0, "model": False}
        st["batch"] = rng.choice(len(Xtr), R.B, replace=False); return st

    def done(s, st): return st["t"] >= R.STEPS

    def _loss(s, st, idx):
        D = st["D"]; return R.loss(st["clf"], D[0][idx], D[1][idx], D[6])

    def _small(s, st, pool, k):
        pool = np.asarray(pool); return [int(i) for i in pool[np.argsort(s._loss(st, pool), kind="stable")[:k]]]

    def default(s, st):                                     # small-loss + decay (real6 baseline "smallloss_decay")
        return s._small(st, st["batch"], st["k"])

    def branches(s, st):
        Xtr, ytr, Xva, yva, Xte, yte, classes = st["D"]; k = st["k"]; clf = st["clf"]
        pc = R.per_class(clf, Xva, yva, classes); out = []
        for name, c in zip(("weak1", "weak2"), classes[np.argsort(pc, kind="stable")[:2]]):
            cls = np.where(ytr == c)[0]; g = np.random.default_rng([st["cell"], st["t"], int(c), 1031])
            pool = np.unique(np.concatenate([st["batch"][ytr[st["batch"]] == c], g.choice(cls, min(len(cls), 2 * k), replace=False)]))
            out.append((name, s._small(st, pool, k)))
        sus = st["mem"] > 3; b = st["batch"][~sus[st["batch"]]]
        if len(b) >= k: out.append(("barrier", s._small(st, b, k)))
        lack = R.loss(clf, Xtr, ytr, classes) * (1 + st["mem"])
        out.append(("clean", [int(i) for i in np.argsort(lack, kind="stable")[:k]]))
        pr = clf.predict(Xva); C = np.zeros((len(classes), len(classes)))
        for a_, p_ in zip(np.searchsorted(classes, yva), np.searchsorted(classes, pr)):
            if a_ != p_: C[a_, p_] += 1
        a_, b_ = np.unravel_index(np.argmax(C), C.shape)
        if C[a_, b_] > 0:
            g = np.random.default_rng([st["cell"], st["t"], 77, 1031]); half = []
            for c, n in ((classes[a_], k - k // 2), (classes[b_], k // 2)):
                cls = np.where(ytr == c)[0]; half += s._small(st, g.choice(cls, min(len(cls), 2 * k), replace=False), n)
            out.append(("pair", half))
        return out

    def valid(s, st, a):
        n = len(st["D"][0]); return [i for i in dict.fromkeys(int(i) for i in a) if 0 <= i < n][:st["k"]]

    def step(s, st, a):
        Xtr, ytr = st["D"][0], st["D"][1]; a = np.asarray(s.valid(st, a), dtype=int)
        if not st["model"]: st = dict(st); st["clf"] = copy.deepcopy(st["clf"])   # model forks are already private copies
        clf = st["clf"]; clf.eta0 = R.LR / (1 + st["t"] / 100)
        if len(a): clf.partial_fit(Xtr[a], ytr[a])
        st["used"] += len(a); st["t"] += 1
        if not st["model"]: st["mem"] = 0.9 * st["mem"] + (clf.predict(Xtr) != ytr)
        st["batch"] = st["rng"].choice(len(Xtr), R.B, replace=False); return st

    def fork(s, st, j):
        f = dict(st); f["clf"] = copy.deepcopy(st["clf"]); f["model"] = True
        f["rng"] = np.random.default_rng([st["cell"], st["t"], j, 1077]); return f

    def objective(s, st):
        D = st["D"]; return float(np.mean(st["clf"].predict(D[2]) == D[3]))   # the result only (rule 4, 13:45)

    def report(s, st):
        D = st["D"]; return {"result": float(np.mean(st["clf"].predict(D[4]) == D[5])), "resource": float(st["used"]),
                             "host": "/".join(st["host"])}

    # ---------------------------------------------------------------- LAW 4 LANDING (REAL2 A; seed.land)
    def landings(s, st, a):
        """One landing = the batch group of one class: the examples of the action carrying that (noisy) label."""
        ytr = st["D"][1]; return [int(c) for c in sorted(set(int(ytr[i]) for i in a))]

    def without(s, st, a, L):
        ytr = st["D"][1]; return [int(i) for i in a if int(ytr[i]) != L]

    def targets(s, st, a, L):
        """Other classes, highest need first = lowest per-class accuracy on the clean validation split."""
        Xtr, ytr, Xva, yva, Xte, yte, classes = st["D"]
        pc = R.per_class(st["clf"], Xva, yva, classes)
        return [int(c) for c in classes[np.argsort(pc, kind="stable")] if int(c) != L][:3]

    def retarget(s, st, a, L, T):
        """The class-L group is replaced by as many small-loss examples labelled T (pool: T in the batch plus 2 x budget
        examples of T drawn from rng [cell, t, T, 1031], the same pool as the weak branches); same count."""
        Xtr, ytr = st["D"][0], st["D"][1]; keep = [int(i) for i in a if int(ytr[i]) != L]; n = len(a) - len(keep)
        cls = np.where(ytr == T)[0]; g = np.random.default_rng([st["cell"], st["t"], int(T), 1031])
        pool = np.unique(np.concatenate([st["batch"][ytr[st["batch"]] == T], g.choice(cls, min(len(cls), 2 * st["k"]), replace=False)]))
        pool = np.array([i for i in pool if int(i) not in keep], dtype=int)
        return keep + (s._small(st, pool, n) if len(pool) and n else [])

    # ---------------------------------------------------------------- REAL3 (seed3: primitives, frame, coupled)
    # Read only by seed3; nothing above is changed, so every REAL1/REAL2 mode gives identical numbers.
    # CHECK of the REAL2 artefact first (real/hosts/biology_landing_check.py, log quick_logs/biology_landing_check.txt):
    # the landing seed's gain is real on held-out test data on cell 2 (cancer/asym30: 0.9708 vs default 0.9181; the
    # same per-step counts at random 0.6503 mean of 5; small-loss truncated 0.9006; warm start alone 0.1228), but on
    # cell 1 (cancer/sym25) the warm start alone (2 examples per class, nothing trained after) already scores 0.9649
    # against the standard's 0.8713: there most of the "gain" is not training on noisy labels at all.
    def _pool(s, st, c):
        ytr = st["D"][1]; k = st["k"]; cls = np.where(ytr == c)[0]; g = np.random.default_rng([st["cell"], st["t"], int(c), 1031])
        return np.unique(np.concatenate([st["batch"][ytr[st["batch"]] == c], g.choice(cls, min(len(cls), 2 * k), replace=False)]))

    def _vote(s, st, a, H=None):
        """P8 VOTE OF FUTURES on the data landing: a class group of the action is withheld only if the action without it
        wins (strictly higher validation accuracy after H own steps) in MOST of the seed's TREE futures (same forks
        j = 0..TREE-1 as seed._rollout, continuation = the standard); ties keep the group (REAL2 land() withheld on
        ties, which is where almost all of its withholding came from)."""
        import seed as S
        H = s.horizon if H is None else H; n = max(S.TREE, s.samples)
        def vals(act):
            out = []
            for j in range(n):
                f = s.fork(st, j); f = s.step(f, s.valid(f, act)); h = 0
                while not s.done(f) and h < H: f = s.step(f, s.valid(f, s.default(f))); h += 1
                out.append(s.objective(f))
            return np.array(out)
        cur = s.valid(st, a); v = vals(cur)
        for L in s.landings(st, cur):
            wo = s.valid(st, s.without(st, cur, L)); vw = vals(wo)
            if (vw > v).sum() > n // 2: cur, v = wo, vw
        return cur

    def primitives(s, st):
        Xtr, ytr, Xva, yva, Xte, yte, classes = st["D"]; k = st["k"]
        pc = R.per_class(st["clf"], Xva, yva, classes); deficit = 1.0 - np.asarray(pc)
        p1 = []
        if deficit.sum() > 0:                                # P1: each class pulls budget in proportion to its deficit
            share = np.floor(k * deficit / deficit.sum()).astype(int); share[np.argmax(deficit)] += k - share.sum()
            for c, n_ in zip(classes, share):
                if n_ > 0: p1 += s._small(st, s._pool(st, c), int(n_))
        lack = s._loss(st, st["batch"]) * (1 + st["mem"][st["batch"]])          # P2: price on repeated mistakes
        p2 = [int(i) for i in st["batch"][np.argsort(lack, kind="stable")[:k]]]
        out = [("P2", "P2:price-mistakes", p2), ("P8", "P8:vote-landing", s._vote(st, s.default(st)))]
        if p1: out.insert(0, ("P1", "P1:deficit-share", p1))
        return out

    def frame(s, st):
        """DATA LANDING (train only where needed): classes already perfect on validation get no examples.
        F:need = the standard's small-loss examples of the needed classes only (fewer examples: resource saved);
        F:need-fill = the full budget, small-loss, drawn only from the needed classes (batch + the weak-branch pool)."""
        Xtr, ytr, Xva, yva, Xte, yte, classes = st["D"]; k = st["k"]
        pc = np.asarray(R.per_class(st["clf"], Xva, yva, classes)); need = set(int(c) for c, p in zip(classes, pc) if p < 1.0 - 1e-9)
        b = np.array([i for i in st["batch"] if int(ytr[i]) in need], dtype=int)
        f1 = s._small(st, b, k) if len(b) else []
        pool = np.unique(np.concatenate([s._pool(st, c) for c in need])) if need else np.array([], dtype=int)
        f2 = s._small(st, pool, k) if len(pool) else []
        return [("F:need", "F:need", f1), ("F:need", "F:need-fill", f2)]

    def coupled(s, st):
        """asym30 = next-class flip: each class's labels are driven by the previous class (parts drive each other):
        land as a whole. sym25: the flips are spread over all classes, per-class landing applies."""
        return False   # REAL3 24 Nov 21:58 (before any REAL3 seal): the landing check showed per-class landing works on
                       # asym30 too (beats random and small-loss at equal count, cells 2 and 4), so it is used everywhere

    # ---------------------------------------------------------------- REAL3 v2 (seed3_ops hooks; HOST_INTERFACE_REAL3v2)
    # Read only by seed3 mode "seed3" (v2); nothing above is changed (REAL1/REAL2 modes and seed3v1 give identical numbers).
    #   parts        : the classes (int labels). within = a class: its two sub-parts by the real-step memory of past
    #                  mistakes (st["mem"], written on real steps only): (c, "trusted") mem <= 1 and (c, "suspect") mem > 1
    #                  (ENTER depth 2: the choice run again inside the bottleneck class, trusted vs suspect examples).
    #   merge        : the named parts' examples first (dict order = who gets the per-step budget first), then the
    #                  standard's small-loss examples not in any named part; valid() keeps the first `budget`.
    #   part_objective: the class's accuracy on the clean validation split (the objective's own measure, per class).
    #   focus        : the whole budget on one class: the budget lowest-loss examples labelled c from the batch plus the
    #                  weak-branch pool of c (rng [cell, t, c, 1031], never the real sampler); a sub-part: the same pool
    #                  restricted to its memory side (else the class pool).
    #   shape        : per-class validation-accuracy band (steps of 0.1; 10 = perfect).
    #   joint        : "balanced" = budget split evenly over the classes (small-loss in each class's pool); "pair" = the
    #                  most confused class pair half/half (the v1 branch, when a confusion exists).
    #   map_part     : a's examples of class pf, by their loss rank in pf's pool, re-expressed as the examples of the same
    #                  loss ranks in pt's pool.
    #   carry        : NOT bound. The row's budget is per step by construction (valid() caps every step at the
    #                  standard's own count); banking examples for a later step would change the row's budget rule.
    #   CONTAIN (generic seed operator): a failing class is kept at the standard (served last) while the others take a*.
    #   op_of        : weak1/weak2 -> heal (weakest class served first), barrier/clean -> contain (suspicious examples kept
    #                  out), pair -> fuse (joint); P* and F:* stay with the seed's table.
    def _pc(s, st):
        Xtr, ytr, Xva, yva, Xte, yte, classes = st["D"]
        return dict(zip((int(c) for c in classes), R.per_class(st["clf"], Xva, yva, classes)))

    def parts(s, st, within=None):
        if within is not None:
            c = within if isinstance(within, int) else within[0]; return [(c, "trusted"), (c, "suspect")]
        return [int(c) for c in st["D"][6]]

    def _in(s, st, i, p):
        if int(st["D"][1][i]) != (p if isinstance(p, int) else p[0]): return False
        if isinstance(p, int): return True
        return (st["mem"][i] > 1) == (p[1] == "suspect")

    def merge(s, st, d):
        out = []
        for p, a in d.items(): out += [int(i) for i in a if s._in(st, int(i), p)]
        out += [int(i) for i in s.default(st) if not any(s._in(st, int(i), p) for p in d)]
        return list(dict.fromkeys(out))

    def part_objective(s, st, p): return float(s._pc(st)[p if isinstance(p, int) else p[0]])

    def focus(s, st, p):
        c = p if isinstance(p, int) else p[0]; pool = s._pool(st, c)
        if not isinstance(p, int):
            sub = np.array([i for i in pool if s._in(st, int(i), p)], dtype=int)
            if len(sub): pool = sub
        return s._small(st, pool, st["k"])

    def shape(s, st):
        return tuple(min(10, int(v * 10 + 1e-9)) for _, v in sorted(s._pc(st).items()))

    def joint(s, st):
        classes = [int(c) for c in st["D"][6]]; k = st["k"]; n = len(classes); out = []; bal = []
        for j, c in enumerate(classes):
            bal += s._small(st, s._pool(st, c), k // n + (1 if j < k % n else 0))
        out.append(("balanced", bal))
        pair = [a for nm, a in s.branches(st) if nm == "pair"]
        if pair: out.append(("pair", pair[0]))
        return out

    def map_part(s, st, a, pf, pt):
        cf = pf if isinstance(pf, int) else pf[0]; ct = pt if isinstance(pt, int) else pt[0]
        rank = lambda c: [int(i) for i in (lambda pool: pool[np.argsort(s._loss(st, pool), kind="stable")])(s._pool(st, c))]
        rf, rt = rank(cf), rank(ct)
        return [rt[min(rf.index(int(i)), len(rt) - 1)] for i in a if int(i) in rf and s._in(st, int(i), pf)]

    def op_of(s, fam):
        return {"weak1": "heal", "weak2": "heal", "barrier": "contain", "clean": "contain", "pair": "fuse"}.get(fam)
