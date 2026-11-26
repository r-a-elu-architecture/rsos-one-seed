# REAL1 row 5 (space): run on the laptop (PowerShell)

CelesTrak is not reachable from the build machine; the check there used the marked stand-in (FLOCK 2E-1 elements of
2018 from Skyfield's own test file). On the laptop, fetch current elements first, then run.

```powershell
cd <your clone of RSOS-Multimodal-World>
git pull
pip install skyfield numpy
cd real/hosts
python space_fetch.py                 # CelesTrak GP group "planet" -> data/space_tle.txt + data/space_tle.meta.json
python space_quick.py --edf | Tee-Object -FilePath space_quick_laptop.txt
```
The output must show `stand_in=False`. Commit `data/space_tle.txt`, `data/space_tle.meta.json` and
`space_quick_laptop.txt` (the elements file is the dataset of record: its sha256 goes into the seal).
Optional: `$env:REAL1_SPACE_SAT = "FLOCK 4X-1"` picks a named satellite from the file instead of the first one.
