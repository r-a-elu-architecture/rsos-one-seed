# One Selector, Many Domains

One shared decision selector, the *seed*, choosing among candidate actions written for each domain, tested across
ten real domains against each domain's standard method. Every claim is sealed (pre-registered, fingerprinted, pushed before the run) and can be rerun.

**Paper:** [`paper/WHITEPAPER_DRAFT.md`](paper/WHITEPAPER_DRAFT.md)

## Headline: against RSOS-free planning (plain rollout), fresh cells, levels fixed before each run (paper §5.7)
| Host | Sealed test | RSOS vs plain rollout | Pre-registered criteria |
|---|---|---|---|
| AI–AI (two real models, split facts, 4-hop question) | CONF6, 200 cells | accuracy **1.000 vs 0.875**, **51 % fewer tokens** (Holm p 1.3e-7, 5.1e-28) | all criteria met |
| AI agents (self-consistency) | CONF5, 48 cells | **43 % fewer tokens** at accuracy 0.95 vs 0.83 (p 1.9e-13, 44/48) | criteria met in 2 of 3 rows |
| Satellite downlink | CONF5, 20 cells | +0.74 %, **20 of 20** cells (p 1.5e-8) | (same test) |

Three unrelated hosts beat plain rollout at p < 1e-5, each in its own sealed test. Check it in seconds:
`pip install numpy scipy && bash reproduce_conf6.sh` (fingerprints + table), `bash reproduce_conf5.sh`.

**The open record:** every sealed test here is also a record in the SRC-X.5 log (an open record of sealed claims), which anyone can verify, copy
as a node, and add to: [`protocol/`](protocol/) (specification, reference node, viewer). Its launch proofs, sealed
before they ran: 600 of 600 violations quarantined with 0 of 200 valid records blocked; three live nodes converged moving
only what each lacked.

## Result (REAL3, the main confirmatory run)
Under the pre-registered rule the seed beats the standard method in **seven of ten real domains** (biology undecided: 6 of 8 cells, one pair timed out and was not re-run);
with a Holm correction across units, **four** (AI agents, AI–human, inventory, satellite downlink). Most of the gain
comes from the domain-written candidates, chiefly a plan-then-execute lever in AI agents. Not shown: neural sensing,
quantum measurement. Read the qualifications in paper §5.1 and §7 before quoting any number.

**Ablation (STRUCT1, sealed, fresh cells 301–308): NOT SHOWN.** With every domain-written lever switched off, the
general structure did not beat plain rollout in any of five rows, so the gains come from the domain-written candidates.
In the same run, with the AI-agent leak fixed, the full seed replicated: 45–57 % fewer tokens in AI agents (accuracy
+0.19), 43 % in AI–human, +1.3 % in inventory and satellite. Paper §5.4,
[`real/results_cloud/struct1/RESULTS_STRUCT1.md`](real/results_cloud/struct1/RESULTS_STRUCT1.md).

| Domain | Status | Headline | Paper | Sealed files |
|---|---|---|---|---|
| AI agents (gpt-oss-20b) | SHOWN | 51–68 % fewer tokens, accuracy not worse (wide intervals); Llama 8B rows reported, baseline near zero accuracy | [§5.1](paper/WHITEPAPER_DRAFT.md#51-real3-main-confirmatory-run) | [`real/RESULTS_REAL3.md`](real/RESULTS_REAL3.md) |
| AI–AI messaging | SHOWN (not after Holm) | 36.9 % fewer tokens; both arms at ceiling | §5.1 | same |
| AI–human replies | SHOWN | 41–44 % fewer tokens; word-overlap proxy, which the seed targets | §5.1 | same |
| Inventory | SHOWN | +1.36 %, 8/8 cells | §5.1 | same |
| Energy | SHOWN (not after Holm) | +5.79 %, 12/16 cells | §5.1 | same |
| Satellite downlink | SHOWN | +1.50 % vs standard; +0.89 % vs a deterministic MILP (unequal information, see paper) | §5.1 | same |
| Robotics | SHOWN (not after Holm) | 14.3 % less effort, result +1.80 % | §5.1 | same |
| Quantum measurement | not met | −0.39 % | §5.1 | same |
| Neural sensing | not met | +5.85 %, interval crosses 0 | §5.1 | same |
| Life-science classification | undecided | 6 of 8 cells; better in 5 of 6, accuracy +5.1 % with 90.9 % fewer labels, interval includes 0 | §5.1 | same |

**What is claimed:** one sealed selection discipline across domains. **What is not claimed:** the best method in any field,
production-scale savings, or anything beyond the sealed runs. Limits, every disclosed fix and the independent review: paper §8 and Appendix A.

## All confirmations on fresh cells (levels fixed before each run; paper §5.6–5.7)
| Test | Claim | Pre-registered criteria | Headline |
|---|---|---|---|
| CONF1 | full seed beats the standard in AI agents, AI–human, inventory, satellite at Holm p < 1e-5, all levers traced to RSOS operators | all criteria met | p from 5e-27 to 1e-9 |
| CONF2 | cross-domain (5 rows) / communication / one-move generated | partly / partly / not met | AI–AI short of 1e-5 at 40 cells |
| CONF3 | cross-domain / communication (p < 1e-7) / moves composed in the RSOS language | partly / all met / all met | 25–61 % fewer tokens in 3 AI rows; composed moves win in AI–AI and satellite (and, mostly through the shared structure, AI agents) |
| CONF4 | programs by an AI given the RSOS sources vs the same AI without them | not met (1 of 4) | AI agents −44 % tokens (p 4.9e-16); other rows no difference |
| ABL1 | one operator switched off per row | not met | the switched operators were barely used (design error, disclosed) |
| CONF5 | identified RSOS structure vs plain rollout | met in 2 of 3 rows | see the headline |
| CONF6 | whole AI–AI system bound to one structure vs plain rollout | all criteria met | see the headline |

Pass criteria are fixed before each run; the table says whether they were met (all, partly, not), with the numbers, and ranks nothing. The sealed files use the internal labels UNPRECEDENTED / STRONG / NOT SHOWN for all / partly / not met. The individual mechanisms
have relatives in recent work ([`paper/PRIOR_ART_26NOV.md`](paper/PRIOR_ART_26NOV.md)); what has no precedent found is one
operator language bound across hosts this unrelated. Results: [`real/RESULTS_CONF1.md`](real/RESULTS_CONF1.md),
[`RESULTS_CONF2.md`](real/RESULTS_CONF2.md), [`RESULTS_CONF3.md`](real/RESULTS_CONF3.md), [`RESULTS_CONF4.md`](real/RESULTS_CONF4.md),
[`RESULTS_ABL1.md`](real/RESULTS_ABL1.md), [`RESULTS_CONF5.md`](real/RESULTS_CONF5.md), [`RESULTS_CONF6.md`](real/RESULTS_CONF6.md).

## Start where you are
The seed carries no field of its own, so it can be planted in any field. Where it has been grown, the sealed results
are above. Everywhere else it is ready on the first day, and every field that grows it adds its results to the same open
record (SRC-X.5, `protocol/`), linked by lineage, so the fields grow together.

| Who | What it gives on day one | First step | Status |
|---|---|---|---|
| AI labs, agent and ML teams | Fewer tokens and higher accuracy in agent and multi-agent work | `bash reproduce_conf6.sh`, then one workload of your own | Grown: CONF5, CONF6 |
| Space, satellite and operations teams | Better schedules where one per cent is large | Rerun the satellite row, then seal your own schedule test | Grown: +0.74 %, 20 of 20 cells |
| Universities and research centres, in every science | Pre-register a study, seal it, receive replications | `python srcx5.py create`, then submit the record | Ready: protocol proven at launch |
| Companies and corporations | Benchmark and vendor claims anyone can check | Seal the claim before the run; publish the record | Ready: protocol proven at launch |
| Institutions and public bodies | A forecast sealed before a decision, audited after it | Create a forecast record | Ready: protocol proven at launch |
| Individuals | Check any record in the browser; add a replication | Open the viewer | Ready at launch |
| Distributed and delay-tolerant networks, up to interplanetary links | A shared log where each node syncs only what it lacks | `python srcx5.py serve --peer <node>` | Ready: a full copy moved 50.3 % of the bytes, a re-check 0.86 % (local nodes) |
| Every other field: biology, chemistry, physics, mathematics, robotics, socio-technical and cybernetic systems, discovery and invention | The same seed on your own problem, sealed to the same standard | Bring one workload | Seed ready for your field |

## Evidence in this repository
| Run | What | Pre-registration and seal | Results |
|---|---|---|---|
| REAL3 | composed seed, 10 domains, fresh cells 201–216 | [`real/PREREG_REAL3.md`](real/PREREG_REAL3.md), [`real/SEAL_REAL3.txt`](real/SEAL_REAL3.txt), [FIX1](real/PREREG_REAL3_FIX1.md) | [`real/RESULTS_REAL3.md`](real/RESULTS_REAL3.md), [summary](real/RESULTS_REAL3_SUMMARY.md), cells in `real/results_cloud/real3/` |
| REAL1, REAL1b | earlier seed, 10 domains, cells 101–120 | [`real/PREREG_REAL1.md`](real/PREREG_REAL1.md), [`real/PREREG_REAL1B.md`](real/PREREG_REAL1B.md) | [`RESULTS_REAL1.md`](real/results_cloud/RESULTS_REAL1.md), [`RESULTS_REAL1B.md`](real/results_cloud/RESULTS_REAL1B.md) |
| SEAL2 | controlled simulated world | [`seal2/PREREG_SEAL2.md`](seal2/PREREG_SEAL2.md) | [`seal2/RESULTS_SEAL2_cloud.md`](seal2/RESULTS_SEAL2_cloud.md) |
| SEAL1 | controlled simulated world | [`seal1/PREREG_SEAL1.md`](seal1/PREREG_SEAL1.md), [FIX1](seal1/PREREG_SEAL1_FIX1.md) | [`seal1/RESULTS_SEAL1.md`](seal1/RESULTS_SEAL1.md) |
| STRUCT1 | ablation: structure alone vs plain rollout; full seed replication, fresh cells 301–308 | [`real/PREREG_STRUCT1.md`](real/PREREG_STRUCT1.md), [`real/SEAL_STRUCT1.txt`](real/SEAL_STRUCT1.txt) | [`RESULTS_STRUCT1.md`](real/results_cloud/struct1/RESULTS_STRUCT1.md) |
| Blind planning | exact shared state for agents | [`README_LANGUAGE.md`](README_LANGUAGE.md) | 256/256 exact across six models |

Prior art: [`real/PRIOR_ART_REAL.md`](real/PRIOR_ART_REAL.md). Data and licences: [`DATA_LICENCES.md`](DATA_LICENCES.md).

## Rerun
```
python real/hosts/economics_fetch.py && python real/hosts/energy_fetch.py   # the two third-party files (sha256-checked); without them their fingerprints cannot be read
sha256sum -c <(grep -v '^#' real/SEAL_REAL3_FIX1.txt)        # every sealed file unchanged
cp real/results_cloud/real3/stage*/*.json real/out3/ && python real/analyze_real3.py   # the table
PYTHONPATH=experiments/sec1 python cloud/real3_unit_fix1.py <row> <model> <pair> <stage>   # one unit
bash reproduce_conf6.sh        # CONF6: fingerprints + table; 'mock' checks every arm without a model
bash reproduce_conf5.sh space  # CONF5: also re-runs the satellite row offline (slow: 30-65 min per cell)
```
AI domains need an OpenRouter key (`OPENROUTER_API_KEY`); the other domains run offline after their fetch scripts.

## Licence
Code: Apache 2.0 ([`LICENSE`](LICENSE)). Third-party data is not redistributed; see [`DATA_LICENCES.md`](DATA_LICENCES.md).
The RSOS Language (blind planning, exact shared state): [`README_LANGUAGE.md`](README_LANGUAGE.md).
