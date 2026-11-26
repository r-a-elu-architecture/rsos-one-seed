# Prior-art check, 26 Nov 2026 (web search on four mechanisms)

Purpose: test, before any public text, whether four mechanisms used in the sealed tests are new. Result: each has close
relatives published in 2025–2026; none of them applies the same operator set across unrelated hosts. The claim that can
be made is the combination and its application across hosts, not any single mechanism. Full citations: paper 1,
References.

| Mechanism | Closest prior art found | Assessment |
|---|---|---|
| Compact-state messages encoded relative to what the receiver already holds | Receiver-relative bounded coordination: message utility is the receiver's gain minus the protocol cost (Xie et al., NeurIPS 2026, arXiv:2610.03769); action-state communication, PACT (Huang et al., arXiv:2606.05304); multi-order communication, MOC (Guan et al., ICML 2026); latent communication, Interlat (Du et al., ACL 2026) | **Not new as a concept.** Here the same operator is also applied on a non-LLM host (the satellite pass plan) |
| Commit an answer only when the evidence chain is complete | Answer abstention until evidence suffices, R2-KG (Jo et al., IJCNLP-AACL 2025 Findings, arXiv:2502.12767); explicit sufficiency checks, PAR²-RAG (Li et al., ACL 2026 Industry Track) | **Not new as a mechanism.** Here it is applied as a system invariant (invariant, check, response) across a two-agent system |
| Evaluation modes chosen by the state of the decision (horizon 1 near the end; two horizons when predicted futures disagree; trace-ordered when the trace is confident) | Perspective as a first-class element of the agent architecture, Observer–Situation Lattice (Alqithami, AAMAS 2026, arXiv:2603.01407); perspective-taking agents, PerspAct (Patania et al., arXiv:2511.08098) | **Partly anticipated.** Routing operators by these decision-state modes was not found |
| One operator vocabulary across unrelated hosts | Domain-independent planning (STRIPS operators across many domains; Fikes and Nilsson, 1971); operads for system design (Foley et al., Proc. R. Soc. A, 2021, arXiv:2101.11115) | **Precedent exists for the concept.** No system was found that applies one operator set (`FUSE`, `PIERCE`, `ENTER`, `ZOOM`, `HEAL`, `BEAM`, …) to LLM agents, an AI–AI channel and a satellite scheduler and measures it against each host's standard and against plain rollout |

A source noted during the search ("skill programs that verify completeness", arXiv:2605.17734) could not be confirmed on
re-checking and is not cited.

Statement used in the paper: the elements each have relatives in recent work; no precedent was found for one operator
language applied unchanged across unrelated hosts and tested under seal against each host's standard and against plain
rollout. Search depth: four web searches on 26 Nov and source verification on the same day; not a systematic review.
