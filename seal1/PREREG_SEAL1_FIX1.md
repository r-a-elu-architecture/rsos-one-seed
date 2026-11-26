# SEAL1 FIX1 (25 Nov 2026 ~09:30, UTC+02:00), written before the re-run

At analysis (`python seal1.py analyze`), the laws step stopped with `KeyError: 'v3'`. Cause: in `seal1.py`, a
`verify` unit sets `laws6.ARMS = ["v5m"]` (the noise-free Law 4 check needs only that arm) and does not restore it.
Every `laws_collect` unit that ran later in the same window process therefore collected only the v5m arm, so the
comparison arms (v3, report+popular, round+round, random+random, B) are missing.
Fix, with no sealed file edited: `seal1/seal1_fix1.py` finds the laws_collect units whose trace lacks any arm, keeps
their old folders as evidence (`seal1/out/_fix1_old/`), and re-runs each in a fresh Python process with the sealed
code, seed (5340) and arms. Nothing else is re-run. Road 8 (beam) and road 10 (partners) results were already produced
by the sealed analysis before the stop and are unaffected (road 8 ROW_PASS true; road 10 ROW_PASS false: R4 9/10).
Analysis afterwards: `python seal1.py analyze`, unchanged (the `*_merged` working folders are deleted first, because
the sealed analysis copies `beam_*` into `beam_merged` and fails on a second run when that folder exists).
Disclosed in the results and the paper.
