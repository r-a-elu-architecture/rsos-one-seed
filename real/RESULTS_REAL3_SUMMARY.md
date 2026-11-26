# REAL3 results after stage 2 (25 Nov 2026, 11:50, UTC+02:00). Biology still pending.

Source of truth: `real/RESULTS_REAL3.md` / `.json`, written by the sealed `real/analyze_real3.py` (seal `ed5a2f5`,
FIX1 `7e4b14b`; all 41 hashes in `real/SEAL_REAL3_FIX1.txt` verified unchanged on 25 Nov 11:45) over `real/out3/`.
`real/out3/` = `real/results_cloud/real3/stage1/` (incl. FIX1 Llama pair 3 and biology pair 0) +
`real/results_cloud/real3/stage2/` (= `cloud-results:real3_fix1/45561450173/`, run 45561450173, committed 09:02 UTC).
Rerun: `cp real/results_cloud/real3/stage*/*.json real/out3/ && python real/analyze_real3.py`.

## Final status per domain

| Domain | Status | Cells | Deciding result (97.5 % interval) | vs strongest |
|---|---|---|---|---|
| AI agents, gpt-oss-20b (ReAct / self-consistency) | SHOWN (stage 1) | 8 | 51.3 % / 68.4 % fewer tokens, accuracy ≥ | 74.0 % / 56.3 % fewer tokens, accuracy ≥ |
| AI agents, Llama 8B self-consistency | SHOWN (stage 1) | 8 (+8 replication) | 50.5 % fewer tokens (stage 1); **fresh stage-2 cells: 42.6 %, 8/8, interval > 0** | 40.0 % fewer tokens |
| AI agents, Llama 8B ReAct | **SHOWN (stage 2)** | 16 | 25.4 % fewer tokens (+0.32, +13), accuracy ≥ | 43.9 % fewer tokens |
| AI–AI communication | SHOWN | 8 | 36.9 % fewer tokens, same answers | – |
| AI–human, Llama / Mistral | SHOWN | 8 / 8 | 41.0 % / 43.6 % fewer tokens, coverage ≥ | – |
| Economics (inventory) | SHOWN | 8 | +1.36 % (8/8) | level (+0.00 %) |
| **Energy** | **SHOWN (stage 2)** | 16 | **+5.79 % (+0.116, +1.12), 12/16** | −1.53 %, not shown |
| Space (real orbit) | SHOWN | 8 | +1.50 % (8/8) | **+0.89 % (+0.33, +8.18), 8/8** |
| Robotics | SHOWN | 8 | +1.80 % result, 14.3 % less effort | – |
| Quantum | **NOT SHOWN (stage 2)** | 16 | −0.39 % (−0.0096, +0.0020), 6/16 | – |
| Neuroscience (DANDI) | NOT SHOWN | 8 windows | +5.85 % (−0.015, +0.030), 4/8 | – |
| Biology | **PENDING** | 2 of 8 | 1/2 cells; 96.7 % fewer labels; accuracy −0.9 % | – |

**Count: 7 of 10 domains SHOWN against the standard method (up from 6 after stage 1), 2 NOT SHOWN, biology pending.
Beats the strongest method in 2 domains: space (result) and AI agents (fewer tokens at equal or higher accuracy, all
four model × standard units).** The count can only end at 7 or 8.

## After independent review (25 Nov 12:30)
The paper (`paper/WHITEPAPER_DRAFT.md`, revision 2, Appendix A) qualifies this table: Holm across the 13 decided units
keeps 4 domains (AI agents via gpt-oss, AI–human, inventory, satellite); the Llama 8B agent baseline is at 0.047
accuracy, so the Llama rows below do not carry the claim; the AI-agent gain is mainly the `F:blind` plan-then-execute
lever; AI-agent plan stores were not cleared between jobs (`PLAN_POOL`, `EXEC`, `TRACE`). The reading in the next
section is superseded where it conflicts.

## Strongest new finding from stage 2 (superseded in part, see above)
The Llama self-consistency row was already SHOWN at stage 1, so under the pre-registration its stage-2 cells do not
decide it. They are, however, 8 fresh cells run blind to the stage-1 result, and they **replicate it independently**:
42.6 % fewer tokens, interval (+11.4, +29.4), 8 of 8 cells won, accuracy +0.156. Llama ReAct, undecided at stage 1
(12.6 %, interval crossing 0), won 8 of 8 fresh cells (27.6 %) and is SHOWN on all 16. On the weakest model in the
study, the saving is no longer one lucky stage.

Energy moved from a REAL3-v1 development regression (2/4) to SHOWN on 16 sealed cells: +5.8 % over the standard. It
does not beat the strongest method (−1.5 %, interval touching 0).

## Disclosures
- FIX1 (commit `7e4b14b`): 5 of 48 stage-1 units crashed on code errors and were re-run with no sealed file edited
  (`real/PREREG_REAL3_FIX1.md`). Stage 2 ran through the FIX1 unit.
- Economics and space are fixed-budget rows judged on result only; the seed used 3.5 % (economics) and 13.5 % (space)
  more of the logged resource column, which the sealed rule does not count. Report it.
- Quantum: joint-setting shots pay their hardware width (fairness decision before the seal); the width-free variant
  is not part of the seal.
- `real/RESULTS_REAL3.md` currently marks biology UNDECIDED because only pair 0 (cells 201–202) is in; it is not a
  stage-2 decision. `real/REAL3_STAGE2_UNITS.json` was restored to the list actually used for stage 2.

## Still to do for the final table
Biology re-run (run 45549039454, pairs 1–3, cells 203–208) had not reached `cloud-results` at 11:45; its job limit
(345 min) puts the end at about 12:45 UTC+02:00. When it lands at `cloud-results:real3_fix1/45549039454/`:
copy into `real/results_cloud/real3/stage1/` and `real/out3/`, rerun `real/analyze_real3.py`, update this file.
Biology is a result row (accuracy at the fixed budget); on pair 0 the seed matched within 1 point using 4 % of the
labels, so the accuracy-only rule makes it a close call, not an expected win.
