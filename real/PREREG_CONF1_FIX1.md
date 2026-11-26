# CONF1 FIX1: dated addendum (25 Nov 2026, ~15:10, UTC+02:00). Changes no rule, no level, no cell, no code.

Owner instruction 14:28. Three disclosed changes to WHERE and ON WHAT DATA sealed CONF1 cells run:
1. **Satellite, data-source outage.** Run 45612652839 failed in all 12 jobs before any cell ran: CelesTrak answered
   "HTTP 503 Service Unavailable" to every job's orbit fetch. No result was produced. The orbit elements were then
   fetched ONCE by `.github/workflows/rsos_tle_freeze.yml` (retrying until CelesTrak answered), committed as
   `real/hosts/data/space_tle_frozen.txt` (+ `.meta.json`: source URL, UTC fetch time) and fingerprinted in
   `real/SEAL_CONF1_FIX1.txt`. The 12 satellite cells 501–512 run on that frozen file (copied to the path the sealed
   host reads, `real/hosts/data/space_tle.txt`); nothing else differs. CONF2 uses the same frozen file.
2. **Inventory moved to the cloud.** The workspace run of cells 501–512 was stopped before any cell finished; no result
   was read. The 12 cells run in the cloud, one per job, with the same sealed unit.
3. **AI–human crash.** The job for cells 537–540 crashed: Topical-Chat `test_freq` has 539 conversations, so cells 539
   and 540 do not exist (the sealed host indexes conversations by cell). Cells 537–538 are re-run; AI–human has 38
   cells. 539–540 cannot exist and are reported as such.
Workflow `.github/workflows/rsos_conf1_fix1.yml`; the sealed unit `cloud/conf1_unit.py` and analysis are unchanged
(seal A still checked by every job; seal B for the AI-human re-run).
