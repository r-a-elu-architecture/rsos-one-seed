# RSOS Core 1.0: State Operations

| | |
|---|---|
| **Status** | Stable (Core 1.0.0, shipped in `rsoslang` 0.4.0) |
| **Editor** | R. A. Elu ([ORCID 0009-0000-1456-2467](https://orcid.org/0009-0000-1456-2467)) |
| **Reference implementation** | `rsoslang.core` (Python, standard library only) |
| **Machine-readable** | [`ir.schema.json`](ir.schema.json) (the IR), [`../../registry/operators.json`](../../registry/operators.json) (operators), [`OPERATORS.md`](OPERATORS.md) (generated reference) |
| **Conformance tests** | [`tests/core/`](../../tests/core/) |
| **License** | Apache 2.0 |

## Abstract

RSOS Core defines a small set of deterministic operations on a shared key–value state, a compiled form for programs
of those operations (the IR), a state digest, and a reconciliation procedure for replicas. It is designed for
multi-agent LLM workflows in which a model **plans** changes by naming keys and relations, and a runtime **computes**
every value. The planner does not need to read state values, and in the measured configuration ("blind planning") it
is shown none. Core is the technical layer of RSOS: the symbolic RSOS language compiles to it, and nothing in Core
depends on the symbolic layer.

## Status of this document

This is version 1.0.0 of the Core specification. It covers eight state operations and two state functions. Every
operation listed as part of the Core layer has an implementation, conformance tests and experimental evidence
(publication rule, §9). Changes follow semantic versioning (§10).

## 1. Conventions

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT and MAY are to be interpreted as described in RFC 2119 and
RFC 8174 when, and only when, they appear in all capitals.

## 2. Data model

2.1. A **state** is a finite map from keys to values.

2.2. A **key** MUST match `^[A-Za-z_][\w-]*(\.[A-Za-z_][\w-]*)+$`: two or more dot-separated segments, each starting
with a letter or underscore (for example `auth.timeout_ms`). The last segment is the key's **field** (`timeout_ms`).

2.3. A **value** is text (a Unicode string). Operations that do arithmetic read the value as a base-10 integer and
write the result back as decimal text without leading zeros or a plus sign. A value that cannot be read as an integer
causes `E_NOT_INTEGER` in an arithmetic operation.

2.4. Implementations MUST compare values as text. Two states are **equal** if they have the same keys with the same
values.

## 3. Programs and the IR

3.1. A **program** is a non-empty ordered list of operations. Its compiled form is the **IR**: a JSON array of
operation objects that MUST validate against [`ir.schema.json`](ir.schema.json).

3.2. A **step** applies one program to a state. A step is **atomic**: either every operation succeeds and the new state
replaces the old one, or the first failing operation's error is returned and the state MUST remain unchanged.

3.3. Operations within a step apply in order; each sees the result of the previous one.

3.4. **IR digest.** The digest of a program is the SHA-256 (lowercase hex) of its IR encoded as JSON with keys
sorted, no insignificant whitespace (separators `,` and `:`), UTF-8, non-ASCII characters not escaped. Two programs
are the same program if and only if their IR digests are equal, whatever surface syntax produced them.

3.5. **Surface syntaxes.** Core defines one surface syntax (§5.1). The RSOS language (§5.2) is a second surface syntax
for the same IR. A conforming compiler MUST produce identical IR digests for the corresponding forms listed in
[`tests/core/test_ir_equivalence.py`](../../tests/core/test_ir_equivalence.py).

## 4. Operations

In each signature, `Key` follows §2.2, `Text` is any string, `Int` is a JSON integer and `null` means "absent".
`max` (when not null) caps the result: `result := min(result, max)`.

| Core | RSOS | Signature | Effect | Errors |
|---|---|---|---|---|
| `set` | `SET k "text"` | `set(key, value: Text)` | `key := value` (literal, never read as a key) | `E_NOT_KEY` |
| `copy` | `SET k other.key` | `copy(key, from: Key)` | `key := state[from]` | `E_NOT_KEY`, `E_MISSING_KEY` |
| `delete` | `DEL k` | `delete(key)` | remove `key` | `E_NOT_KEY`, `E_MISSING_KEY` |
| `derive` | `INHERIT d s [+n] [CAP m]` | `derive(dst, src, add: Int = 0, max: Int\|null)` | if `add = 0` and `max` is null: `dst := state[src]` (any text); else `dst := min(int(state[src]) + add, max)` | `E_NOT_KEY`, `E_MISSING_KEY`, `E_NOT_INTEGER` |
| `sum_into` | `FUSE d a b [CAP m]` | `sum_into(dst, a, b, max)` | `dst := min(int(state[a]) + int(state[b]), max)` | `E_NOT_KEY`, `E_MISSING_KEY`, `E_NOT_INTEGER` |
| `multiply` | `SCALE k f [CAP m]` | `multiply(key, factor ≥ 0, max)` | `key := min(int(state[key]) × factor, max)`; the product MUST be a whole number | `E_NOT_KEY`, `E_MISSING_KEY`, `E_NOT_INTEGER`, `E_FRACTION` |
| `select_if` | `ROUTE s = x : d v1 \| v2` | `select_if(cond_key, equals: Text, dst, then: Text, else: Text)` | `dst := then` if `state[cond_key] = equals`, else `dst := else` | `E_NOT_KEY`, `E_MISSING_KEY` |
| `reassign_where` | `REHOST field a b` | `reassign_where(field, from: Text, to: Text)` | for every key whose field is `field` and whose value is `from`: value `:= to` | none (no match is not an error) |

4.1. Destination keys (`key` in `set`/`copy`, `dst`) MAY be absent before the operation; they are created.

4.2. `reassign_where` scans the whole state. It is the operation that one-call JSON Patch agents most often got wrong
in the experiments (the model must find every matching key itself); in Core the runtime performs the scan.

4.3. An implementation MUST NOT read state values in the planner's place, guess missing keys or coerce non-integers.

4.4. **Proposed for Core 1.1: `derive_where` (RSOS `FLOW field OVER cond_field x [+n] [CAP m]`).** For every object
whose `cond_field` equals `x`: `field := min(int(field) + n, max)`; objects without `field` are skipped; no match is not
an error; `E_NOT_INTEGER` if a matched value is not an integer. Implemented and tested (registry C-009, status
`tested`); it enters the Core layer under §9 only after its pre-registered experiment
([`PREREGISTRATION_SC2.md`](../../experiments/PREREGISTRATION_SC2.md)), whose predictions were published before it was
built.

## 5. Surface syntaxes

5.1. **Core syntax.** One call per line: `name(field=value, ...)`. Values are bare words without commas or
parentheses, or JSON strings in double quotes. Optional integer fields MAY be omitted. Blank lines and lines starting
with `#` are ignored. Example:

```
reassign_where(field=owner, from=bruno, to=chen)
derive(dst=auth.timeout_ms, src=auth.timeout_ms, add=100, max=900)
set(key=auth.note, value="see a.b")
```

5.2. **RSOS syntax.** One operation per line, as listed in the RSOS column of §4. In `SET k v`, an unquoted `v`
that matches the key pattern is a **copy**; any other `v`, or a quoted one, is a literal **set**. Text containing a dot
MUST therefore be quoted (`SET k "a.b"`). Lines that do not begin with an operation keyword are ignored, so planner
replies MAY contain prose.

5.3. **JSON.** The IR itself (§3) MAY be exchanged directly; it is the canonical interchange form.

## 6. State functions

6.1. **`state_digest(state)`** ("green dot"): the first 12 lowercase hex digits of SHA-256 over the state encoded as a
JSON object with keys sorted, all values as strings, separators `,` and `:`, UTF-8, non-ASCII not escaped. Test vectors:

| State | Digest |
|---|---|
| `{}` | `44136fa355b3` |
| `{"a.b": "1"}` | `737a6b803cf8` |
| `{"a.b": "1", "c.d": "two words"}` | `daae52c2238c` |
| `{"k.x": "é"}` | `04d8868891da` |

The 12-digit prefix is a replica-consistency check, not a security boundary (§11).

6.2. **`reconcile(replica)`** ("heal"/"sync"): if `state_digest(replica)` equals the agreed digest, nothing changes;
otherwise the result lists every key whose value differs or which is present in only one of the two, and returns the
agreed state. It MUST NOT call a model.

## 7. Errors

Errors are returned with a stable code and a human-readable message (the message is suitable to send back to the
planning model). Codes are stable within a major version.

| Code | Meaning |
|---|---|
| `E_PARSE` | The program or one operation cannot be read (unknown name, missing or unexpected field, wrong type). |
| `E_NOT_KEY` | A field that must be a key does not match §2.2. |
| `E_EMPTY` | The program has no operations. |
| `E_MISSING_KEY` | A key that must exist does not (a source, `delete`'s key, `select_if`'s condition). |
| `E_NOT_INTEGER` | An arithmetic operation read a value that is not an integer. |
| `E_FRACTION` | `multiply` produced a value that is not a whole number. |

## 8. Planning protocol (informative)

The measured protocol ("blind planning", experiments A7 and A8): the planner receives the change requests and the
list of key names, never values, and replies with one program per request; the runtime executes each step atomically;
an auditor model checks the runtime's reported diffs and may send a step back once. The reference prompts are
`rsoslang.core.plan_prompt` and the MCP tools `rsos_state_new`, `rsos_state_prompt`, `rsos_state_apply`,
`rsos_state_sync`, `rsos_state_get`. Results: 256/256 tasks exact across six models from four companies
([A8 report](../../experiments/A8_FAMILIES_REPORT.md)).

## 9. Publication rule and status

An operation is part of the Core layer only if its registry status is `tested` or `executed` **and** it has at least
one experiment as evidence. In Core 1.0.0, seven operations and both functions qualify. `copy` is specified,
implemented and tested but was not used in any experiment, so it is documented and supported but listed outside the
Core layer until it is ([`OPERATORS.md`](OPERATORS.md)).

## 10. Versioning and compatibility

10.1. Core follows semantic versioning. Adding an operation is a minor change; changing an operation's semantics, an
error code or an encoding is a major change.

10.2. `rsoslang` 0.4.0 changed `state_digest` to the encoding in §6.1. Digests computed by 0.3.x do not match and
MUST NOT be compared with 0.4.0 digests.

10.3. The Python module path `rsoslang.state` remains available as an alias of `rsoslang.core.state`.

## 11. Security and privacy considerations

11.1. **The planner never needs state values.** In the blind configuration the planning model sees key names only. In the
measured protocol (A7, A8, SC1) an auditor model checks each step and is shown the values of the keys the step read and
changed; deployments that must keep every value from every model need an audit without values (not yet measured). The
blind planner limits
what a prompt-injected or curious model can disclose. Key names themselves may be sensitive; treat them accordingly.

11.2. **Digests are not authentication.** The 12-digit `state_digest` detects accidental drift between replicas; it
does not protect against an adversary who can choose values. Use a full-length hash or a signature where tampering
is a threat.

11.3. **Determinism.** Every operation is a pure function of the state and the program. Implementations MUST NOT
depend on time, randomness, locale or the order of keys in memory.

11.4. Core contains no person-facing operations. Person-facing operations (the RSOS cue framework) are outside Core and
require consent and the seven governance checks.

## 12. Conformance

An implementation conforms to Core 1.0.0 if it accepts every valid IR, rejects every invalid one with the specified
error code, produces the results of [`tests/core/test_conformance.py`](../../tests/core/test_conformance.py) and the
digest vectors of §6.1, and keeps steps atomic (§3.2).

## Appendix A. Related work

The planner/executor split belongs to an established family: program-aided language models, tool and function
calling, code-as-action agents, plan-then-execute agents, and the dual-LLM pattern and CaMeL, which separate a
model's control flow from the data it acts on for security. Core applies the split to exact shared-state editing
across agents, with replica digests and zero-call reconciliation, and publishes a benchmark (StateBench) for comparing
approaches.

## Appendix B. Origins (informative)

Each Core operation has a symbolic origin in the RSOS language (for example `reassign_where` ← REHOST, "re-host";
`state_digest` ← "green dot"; `reconcile` ← "heal"), recorded in the registry's `origin` field. RSOS began as a
symbolic language for healing, transforming, signalling and evolving; Core is the technical layer that grew from it.
