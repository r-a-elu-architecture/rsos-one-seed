# H1 pre-registration: predictive healing at the greatest lack, before drift

Written before the run. S1 found that heal and anticipation never meet in the 2025 ledger; the owner's 17 Nov
image fills that gap: the golden light finds the path, the green particle lands where the lack is greatest, the
white light heals. Test: heal before use, aimed at the greatest expected lack, against healing after drift is
detected and against healing evenly.

## Model (`experiments/h1_predictive_heal.py`)

Palace of 200 books shared by sender and receiver. Each step the receiver's copy of book i drifts with hazard
h_i ~ Beta(0.3, 12) (most books stable, a few volatile). Each step 20 messages use books chosen by Zipf
popularity (exponent 1.1). A use with a drifted book is caught by the green dot (C1) and costs a heal plus a
resend.

| Policy | Before use | Budget |
|---|---|---|
| R reactive | nothing | — |
| U even | check-and-heal K books chosen at random | K per step |
| G golden | check-and-heal the K books with the greatest expected lack: P(drifted since last sync) × use rate, hazard learnt from past detections (Beta(1, 20) prior) | K per step |

Costs (bytes, from C1): message 65; check of an in-sync book 60; heal of a drifted book 300; failed first use
adds heal 300 + resend 65 and two round trips. 500 steps, 20 seeds, K ∈ {5, 10}.

## Predictions

- P1: first-use success: G(K=5) ≥ R + 0.05 and ≥ U(K=5) + 0.03.
- P2: bytes per use: G(K=5) ≤ R.
- P3: efficiency: G(K=5) first-use success ≥ U(K=10).
