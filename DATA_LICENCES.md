# Data used by the sealed runs, and its licences

**Correction (25 Nov 12:55):** the private repository commits two third-party data files in `real/hosts/data/`
(`walmart_sales_weekly.csv`, `household_load_uci_hourly.csv`). The staged public tree **excludes them**
(`tools/stage_public_seed.sh`) until their licences are confirmed; the fetch scripts (`real/hosts/economics_fetch.py`,
`real/hosts/energy_fetch.py`) recreate them, and the STRUCT1 fingerprints let anyone check that the fetched files are
identical. Topical-Chat is fetched at run time (`real/hosts/data/topical_chat/` holds only a `.gitignore`).
`real/hosts/data/ai_agents_tree.json` is this project's own calibration data, not third-party. The result files contain
only derived numbers (scores, token counts, resource totals per cell).

**Still to confirm before publication (four):** Walmart / Kaggle competition rules; UCI dataset 235 licence page;
DANDI 000140 licence (CC0 or CC-BY-4.0); CelesTrak terms of use. Topical-Chat is confirmed (CDLA-Sharing 1.0).

**Addendum 26 Nov 2026:** two confirmed from the source pages. UCI dataset 235 is CC BY 4.0; cite Hebrail, G., &
Berard, A. (2006). *Individual Household Electric Power Consumption* [Dataset]. UCI Machine Learning Repository.
https://doi.org/10.24432/C58K54. DANDI 000140 ("MC_Maze_Small", Churchland and Kaufman) is CC-BY-4.0; DOI
10.48324/dandi.000140/0.220113.0408. Still to confirm: the Walmart / Kaggle competition rules (fetch only, never
redistributed) and the CelesTrak usage policy (celestrak.org/usage-policy.php). With both fetch scripts run, every
sealed fingerprint of CONF4, ABL1, CONF5 and CONF6 matches, and all 10 records of the open log verify.

Checked 25 Nov 2026. Items marked **to confirm** must be confirmed before publication.

| Data | Used in | Fetched from | Licence | Status |
|---|---|---|---|---|
| Topical-Chat (Amazon Alexa AI), `conversations/test_freq.json`, `train.json` | AI–human communication | `github.com/alexa/Topical-Chat` (original) | Community Data License Agreement – Sharing 1.0 (`DATALICENSE` in the original repository) | Confirmed by the AWS Open Data registry entry and citing papers. Fetch only; attribution in the paper. |
| Walmart Recruiting – Store Sales Forecasting (Kaggle, 2014), 7 weekly series sampled by the timetk / pytimetk packages | Inventory | `raw.githubusercontent.com/business-science/pytimetk/.../datasets/` (a third-party copy) | Kaggle competition data; the competition rules govern use | **To confirm.** Kaggle competition rules usually limit use of competition data; the rules page was not reachable from this session. Do not redistribute. Before publication, confirm that research use and publishing derived results are allowed, and prefer fetching from Kaggle with the user's own account rather than from the third-party copy. |
| Individual Household Electric Power Consumption (UCI ML Repository, dataset 235; Hebrail and Berard, 2012) | Energy (load) | `raw.githubusercontent.com/marcopeix/AppliedTimeSeriesForecastingInPython/...` (a third-party copy) | UCI datasets are generally published under CC BY 4.0 | **To confirm** the licence on the dataset page. Switch the fetch to the UCI original (DOI 10.24432/C58K54), and cite it. |
| DANDI Archive, Dandiset 000140 | Neural sensing | DANDI Archive via the `dandi` client (original) | DANDI requires every dandiset to be CC0 or CC-BY-4.0 | **To confirm** which of the two this dandiset uses, and cite it as its metadata asks. |
| pvlib TMY3 sample files (NREL typical meteorological year) | Energy (solar) | shipped with the `pvlib` Python package | pvlib: BSD-3-Clause; TMY3: NREL public data | **To confirm** NREL's attribution request. |
| CelesTrak orbital elements (GP / TLE) | Satellite downlink | `celestrak.org` (original) | Public orbital data; CelesTrak asks for attribution | **To confirm** the current terms of use. |
| ORG-REAL1 biology hosts (`experiments/sec1/`) | Life-science classification | per host (see `experiments/sec1/`) | per source dataset | **To confirm** per dataset before publication. |

Model access (OpenRouter; gpt-oss-20b, Llama 3.1 8B, Llama 4 Scout, Mistral Small 3.2) is governed by each model's
own licence and the provider's terms; model outputs in the result files are counts and scores, not text.
