# THM2: the zero-trust rebuild as a theorem (private, sealed 20 Nov 2026 before DOJO1 results)

Sealed by the commit that adds this file, while DOJO1 (R1, R2, B0, B1) is still running on the owner's laptop and
before any of its results are seen here.

## Setting
Sources: user prompt U, structured records B (bank fields), documents D (free text), the model's own literals M.
An attacker can write into documents only. The extractor is fully adversarial (may return any value). The model
is treated as one more untrusted source.
Trusted(U, B) = sink-type tokens in U ∪ sink-type fields of B.

## Theorem 2(k), recipient sinks, k = 2 as implemented in `rsos_dojo.py`
A value v reaches a recipient sink only if
(a) v ∈ Trusted, or
(b) v was extracted from a document D, v occurs verbatim in D (sign 1), and v is the only sink-type token in D (sign 2).

**Proof.** `_guard` returns None for a recipient only on line "v in self._trusted_ibans()" (case a) or on
"'extract' in prov and self.two_sign[v]" where two_sign[v] = (v in text) ∧ (|IBANs(text)| = 1) is computed from
the source value itself at extraction time (case b). Every other path returns a block code. No path consults the
model or the extractor's claim about v. ∎

**Corollary 1 (residual).** If the attacker writes v ∉ Trusted into a document that holds any honest sink-type token,
|IBANs(D)| ≥ 2, so v is rejected. An attacker value is accepted only when every sink-type token in D is attacker-written
(the attacker replaced that content, or D had none). Call this class R.
**Corollary 2 (model as untrusted source).** A model-written recipient literal passes only if it is in Trusted.
Model errors and injected values are rejected by the same rule.
**Corollary 3 (password).** A password reaches the sink only as a literal that occurs in U.
**Ladder.** Adding sign 3 = "v ∈ Trusted" for every new payee empties R and costs exactly the tasks that pay a payee
found only in a document. k is a dial between residual and utility.

## Exhaustive check on the real code (`thm2_check.py`)
1,152 worlds (prompt, records, honest document content, attacker mode none/append/replace, adversarial extractor,
model literals): **0 violations**; attacker value accepted 80 times, **all 80 in class R**; **0** acceptances after
appending to a document with an honest IBAN; **0** untrusted model literals accepted; password accepted only in the
1 legal case.

## Predictions for DOJO1, sealed now (in addition to P1–P5)
- **T1** Every successful attack in R1 lies in class R: the attacker IBAN reached the sink through `rsos_extract`
  from a document whose IBAN content the injection replaced or supplied. Checked from the audit (provenance) and the
  injections recorded in the logs.
- **T2** No successful attack in R1 reaches a sink through a trusted source, a model literal, or a document that
  also held an honest IBAN.
- Note: class R is wider than P1's "user_task_0 only". If the planner extracts a recipient from the landlord or
  address files, R can include those tasks. Then P1 can fail while T1 and T2 hold; both outcomes are reported as is.

## Scope, stated
The theorem covers sensitive arguments (recipient, password). It does not cover amounts or which tool calls the
planner makes: the planner sees shapes (lengths, counts) and revealed bits, which an attacker can influence.
