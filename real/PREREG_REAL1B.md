# PREREG REAL1b: addendum to REAL1 (24 Nov 2026 ~17:45, UTC+02:00). Owner OK 17:38. Pushed before the run.
Why: in both development cloud runs the AI-agents row on Llama 3.1 8B failed after ~5 minutes; the error was not kept.
Likely cause (not yet seen): native tool calls unsupported by its OpenRouter providers. REAL1 itself is NOT changed; its
Llama 3.1 8B AI-agents jobs are reported as they come.
Addendum: (1) preflight: one native tool call each to Llama 3.1 8B, Llama 4 Scout, gpt-oss-20b, output in the log
(diagnostic only); (2) the AI-agents row on Llama 4 Scout (meta-llama/llama-4-scout, the Llama model of phase 3), with
the sealed REAL1 code, cells 101-120 (4 chunks of 5), the same standards (ReAct, self-consistency), measures and pass
rules as PREREG_REAL1.md, analysed with real/analyze_real1.py. Step output is kept even on failure.
