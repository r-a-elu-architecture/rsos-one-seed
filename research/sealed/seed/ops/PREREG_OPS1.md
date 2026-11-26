# OPS1: the seed operators executed under Law 0, and Law 1 on three hosts (layer 2), sealed before any code

Written 20 Nov 2026, ~05:25 Vilnius. Private. Seed: `../SEED_V3.md`. Plan: `../MISSION_100X.md` levers 1, 3 and 2.
Operator definitions taken from the dev branch only where needed (D109): CARRY, READY, LAND (replacing ABSORB),
ISOLATE, GROW, SEE, LOOP. World in every test: `sc1_tasks.make_task(seed)["init"]` (50 objects × 6 fields = 300
facts); safe range of a component = its set of allowed values.

## Law 0 monitor (all parts)

Every effect (write, landing, opening a message, serving a read) passes a monitor **before** it takes effect. It
refuses: a value outside the safe range; a write beyond the budget; opening a message whose hash fails (READY);
a landing where no need is measured; serving from an isolated part. Each operator's test includes injected violations.

- **Z1.** 100 % of injected violations refused before effect, in every operator.
- **Z2.** 0 refusals of legitimate actions.

## Part 1: the operators executed

| # | Operator | Test | Prediction |
|---|---|---|---|
| O1 | CARRY + READY | 2,000 messages over 3 hops along the roots; each hop tampers with a value with p = 5 %, and the receiver's book is outdated with p = 5 %; the message carries keys and the Merkle root of its book; the receiver verifies before opening; a refused message is resent (≤ 3 times) | 0 wrong adoptions; delivered ≥ 99.5 % |
| O2 | LAND | hologram (T2c LivNR store), 10 % silent flips, no damage map; need = a stored bit that the relational reconstruction contradicts with margin; LAND rewrites only those | precision of landings (share that land on flipped bits) ≥ 0.90; recall ≥ 0.40; facts read after landing ≥ before |
| O3 | ISOLATE | Merkle tree over 4,096 leaves; breach = k ∈ {1, 4, 16} tampered leaves; the subtree whose hash fails is isolated; forensic descent locates the leaves; heal from a replica; then alive | located 100 %; checks ≤ 2·k·log₂(4096); 0 reads served from an isolated part before healing |
| O4 | GROW | rule 6 selection (T2b R6) as an operator, budget fixed at 10,000 bits | at 50 % erasure ≥ plain + 2 pp; budget never exceeded |
| O5 | SEE | seer 1 = plain read at 50 % erasure; seer 2 flags seer 1's reads with gap < 2·√support; witness re-reads the flagged facts through relations and stops (≤ 3 passes) | seer 2 flags ≥ 80 % of seer 1's errors with precision ≥ 0.20; the witness always stops; accuracy after the witness ≥ seer 1 + 4 pp |
| O6 | LOOP (see → build → decide) | calibrate the T2c gate: see = errors on calibration scenes 800–807 for gate thresholds 0.5, 0.7, 0.9 (share of weak facts); build = pick the best; decide = accept only if on held-out scenes 920–927 the 70 % result improves and the 90 % result does not drop by more than 1 pp | the loop accepts a threshold; held-out LivNRg at 70 % ≥ 99 % |

## Part 2: Law 1 (read scope) on three hosts

An operation reads n elements: one key (n = 1), two keys (2), condition (one field of all 50 objects, 50), scan (all
300). It fails if any element it needs is misread or not delivered. ε = the failure rate of one-key operations,
measured in the same run. **Law 1 predicts** P(fail) = 1 − (1 − ε)^n.

| Host | How it naturally fails |
|---|---|
| Memory | hologram, plain read, 30 % erasure (crosstalk) |
| Network | each element is a packet over a Gilbert–Elliott burst-loss channel (good: 1 % loss; bad: 50 %; good → bad 0.05, bad → good 0.30), one retry |
| Ledger | 5 replicas in two racks (3 + 2); per epoch a rack fails with p = 0.05 and stays down with p = 0.8; each replica down with p = 0.1; a read needs 3 of 5 |

**Law 2 (blind operation), network and ledger:** the operation's structure (keys only) is sent to where the data
lives and executed there deterministically; one request and one reply.

Predictions (16 scenes, 200 operations per family per scene and host):

- **L1a.** Ordering key < pair < condition < scan on all three hosts.
- **L1b.** Memory: observed pair and condition failure within max(3 pp, 30 % relative) of Law 1's prediction.
- **L1c.** Network and ledger: failures cluster in time, so Law 1 over-predicts: observed condition failure below the
  prediction on both.
- **L2a.** Blind scan failure ≤ 2 × one-key failure on network and ledger; pulled scan failure ≥ 10 × one-key failure.

Every prediction reported pass or fail; nothing changed after the run; fixes after the start disclosed.

## Honest notes

- On a host whose errors are independent, L1b is the arithmetic of compounding; the real tests are L1c (correlated
  hosts) and Law 2. Moving computation to the data (L2) is established practice in databases and networks; what is
  tested is that the same seed law holds on hosts that share nothing.
- O3 repeats roots v1 under the monitor; its new part is Z1/Z2 and "no reads from an isolated part".
