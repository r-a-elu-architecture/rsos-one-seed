# SRC-X.5: an open record of sealed claims, verified at the source

**R. A. Elu** (ORCID 0009-0000-1456-2467) · Protocol paper, version 1.0 · 26 November 2026 · DOI: 10.5281/zenodo.24555259 ·
Text: CC BY 4.0; code: Apache 2.0

## Abstract

A claim is easy to make and hard to check. SRC-X.5 is an open protocol that makes one claim checkable by anyone, in any
field: a record states what was predicted and by which criteria, which files were fixed and when, when the test ran,
what came out, who replicated it and where it came from, and carries no personal data. A record's identity is the
SHA-256 of its canonical form, so every copy is verified independently of the host or network it came from. Records enter
an append-only, hash-chained log through seven admission checks; admission is non-blocking: a submission
that fails a check is quarantined with its reasons, never published and never deleted. Because a record is canonical bytes
whose identity is their own hash, the protocol defines a binding for each layer of the OSI model, for an application-semantics layer above it,
and for the internet, space, linked-data, ledger and archive models, each through that layer's main standard. We
report two sets of tests, each sealed before it ran. The v1.2 launch proofs quarantined 600 of 600 invalid records
across 15 classes and blocked 0 of 200 valid ones. The v1.4 launch tests met all seven of their criteria: records
arrived byte-identical through six carriers, including a simulated delay-tolerant link with 30 % loss; sync failed over
when two of three mirrors were down; every interface conformed to its standard; an AI agent verified and rejected
records through the Model Context Protocol; 400 hostile requests caused no failure; and the log head was anchored on
Bitcoin. The specification, a reference node in one file of Python standard library code, and the first records are
released under open licences.

## 1. Motivation

Pre-registration separates prediction from result, and it is now practised in medicine, psychology and, increasingly,
machine learning. What remains hard is checking it afterwards, across fields and tools: a registry entry, a commit, the
analysis code and the outcome usually live in different places, in different formats, under different operators. A
reader who wants to know whether a claim was fixed before its test, whether the files that produced it are the files
that were fixed, and whether anyone else reproduced it must trust each of those places.

SRC-X.5 puts all of it in one record that anyone can verify with a hash function. It builds on established foundations:
registries for pre-registration (OSF Registries [1], AsPredicted [2]), append-only transparency logs (Certificate
Transparency [3]; Sigstore's Rekor [4]), content addressing (git, IPFS [5]), provenance vocabularies (W3C PROV [6]) and
permanent archives (Software Heritage [7], Zenodo [8]). The contribution is their combination into one domain-free record with admission checks
that quarantine instead of reject, stable identifiers across revisions, and a binding for each communication layer, so
that individuals, research centres, companies, tools and AI agents connect to the same record from wherever they are.

## 2. The record

A record is one JSON object. Its `id` is the SHA-256 of its canonical form without `id`: JSON with sorted keys, no
spaces, UTF-8, and integers or strings only (no floating-point numbers, so every language produces the same bytes).
Changing any byte changes the id.

| Field | Meaning |
|---|---|
| `type` | `claim` (a sealed test), `replication`, `forecast` or `health` |
| `title`, `purpose` | what is tested, and why |
| `prediction.criteria` | the pass criteria, fixed before the run |
| `seal.files[]`, `seal.sealed_at` | `{path, sha256}` for every file fixed before the run, and when |
| `run.started_at` | when the run began; must be after the seal |
| `outcome.criteria_met` | `all`, `partly`, `none` or `pending`, with fingerprinted result files |
| `evidence` | where the claim was shown: `real`, `simulated` or `both` |
| `lineage` | parent records, and a stable identity that survives revision |
| `declarations` | who is affected and whether they consented, predicted harm, the declared purpose |
| `consent_harm.personal_data` | must be `false`: the open log holds no personal data |

## 3. Admission: seven checks, quarantine and stable identifiers

Every record passes seven checks, and every reason names its check.

| Check | What it requires |
|---|---|
| DISCLOSURE | content matches its id; criteria stated; sealed before the run, and never dated in the future |
| CONSENT_PRIVACY | no personal data (patterns for e-mail, phone, payment card with Luhn check, IBAN); consent where people are affected |
| HARM_BOUND | declared predicted harm at or below 0.3 |
| CONFORMANCE | valid version, evidence domain, lineage and references |
| NON_BLOCKING | a valid record is never blocked (measured in every test) |
| ATTRIBUTION | a measured outcome carries fingerprinted results; a replication names who made it |
| PURPOSE | the record declares the purpose it serves |

**Non-blocking admission.** A submission that fails a check is quarantined with its reasons; it is not published and
not deleted. **Stable identifiers across revisions.** A revision is a new record that references the earlier one in
`supersedes` and carries the same `lineage.identity`; both remain in the log, and the active set lists only the latest. **Nodes audit each other** with two independent
signals (the peer's chain does not verify; a record it serves differs from ours) and report divergence only when both agree.

## 4. The log and sync

Admitted records are appended to a log of entries `{seq, prev, record, entry_hash}`, where `entry_hash` is the SHA-256 of
the entry's canonical form and `prev` the previous entry's hash. Editing any stored entry breaks the chain from that
point. Sync is digest-based: a node compares ids with a peer and moves only the records it lacks, in the peer's chain
order, re-checking each one as it arrives.

## 5. Layer bindings

A record is canonical bytes whose identity is its own SHA-256. Any layer of a communication stack can carry bytes,
and any system can compute a hash, so the protocol defines a binding for each layer through that layer's main standard.

| Layer | Main standard there | SRC-X.5 at that layer |
|---|---|---|
| 8 Application semantics (above OSI) | purpose, criteria, lineage; agents | records state purpose, pre-fixed criteria and lineage; AI agents connect through MCP |
| 7 Application | HTTP, git, MCP | node API (OpenAPI 3.1); the log as a git repository; a browser verifier |
| 6 Presentation | UTF-8, JSON, JSON-LD | one canonical encoding; JSON Schema 2020-12; a W3C PROV view in JSON-LD |
| 5 Session | peer synchronisation | digest sync: compare, move only what is missing, resume after any break |
| 4 Transport | TCP, QUIC; the Bundle Protocol [13] | carried unchanged; self-contained records suit store-and-forward |
| 3 Network | IP; content addressing | content addressing: the id locates the bytes and verifies them over any route |
| 2 Data link | Ethernet, Wi-Fi, CCSDS space data link | any frame; integrity is end to end, by the hash |
| 1 Physical | fibre, radio, optical, print | any medium; bytes read back verify identically |

The other models bind the same way: the internet's TCP/IP stack (layers 7 to 3 merged); space and interplanetary links
(CCSDS [14] and delay-tolerant networking [13], where records travel as bundles and sync tolerates long delays); the web and
linked data (records as PROV entities); decentralized ledgers (the head hash anchored in a transaction); and archives
(DOI snapshots, Software Heritage).

## 6. Interfaces, mirrors and anchors

**Uniform read interface.** A running node and a static mirror answer the same read paths (`ids.json`, `head.json`,
`log.json`, `records/<id>.json`, `ld/<id>.jsonld`, `.well-known/srcx5.json`); a running node also accepts `POST /submit`.
A client never needs to know which kind it reached.

**Interfaces.** OpenAPI 3.1 [10] describes the API, so any HTTP tool or SDK can generate a client; JSON Schema 2020-12 [11] describes
the record; every record has a JSON-LD [9] view in the W3C PROV vocabulary [6] (entity, generating activity, derivation,
revision, attribution); an MCP [12] server exposes six tools to AI agents (list, get, verify, verify the log, submit, linked
data); and `llms.txt` points AI readers to all of it.

**Mirrors and failover.** A mirror list ships with the log. Sync tries peers and mirrors in order and uses the first that
answers; a copy that serves a record whose id is not its own hash is skipped for that record, and the record is taken
from the next copy. A scheduled check compares each mirror's head with the log and refreshes stale ones. Anyone running
a node holds a full copy and can be added with one pull request. At release the mirrors are GitHub Pages, GitHub's raw
content service and the jsDelivr content network, with Software Heritage as a permanent archive.

**Anchors.** An anchor proves that the log head, and so every record before it, existed at a time on a public network.
Anchors live beside the log, not in it, so any network can be added without changing a record. The reference set stamps
the head on Bitcoin through OpenTimestamps [15], which is free and needs no wallet.

**Hardening.** A node accepts at most 256 kB per submission and 30 submissions per client per minute, accepts only UTF-8
JSON objects, answers 4xx to anything else, refuses edits and deletion, and never crashes on bad input.

## 7. Evaluation

Both test sets were written with their pass criteria, fingerprinted and pushed before they ran, and each ran once.

**v1.2 launch proofs** (seed 3): 600 of 600 invalid records quarantined across 15 attack classes, including forged and
tampered ids, back-dated and future-dated seals, and personal data; every check quarantined 30 of 30 targeted records
and named itself; 0 of 200 valid records blocked; a superseding clone kept its identity; a peer audit flagged only the
edited peer; sync moved 50.3 % of a full copy for a new node and 0.86 % for a re-check.

**v1.4 launch tests** (seed 14; 6.7 s for T1–T6, T7 in GitHub Actions):

| Test | Result |
|---|---|
| T1 Carriers | 10 of 10 records byte-identical, ids recomputed, chain intact and head equal through six carriers: a running node, a static mirror over HTTP, a git clone, a file copy, a delay-tolerant link (86 bundles of 1 kB, 30 % loss per attempt, 130 attempts over 5 simulated hours), and 30 QR-sized chunks reassembled from a shuffled order |
| T2 Failover | a stale mirror reported stale and the others current, then all current after refill; with two of three mirrors down, the third answered with 10 of 10; with all down, a clean error at once; a record altered on one mirror was skipped and taken from the next |
| T3 Standards | OpenAPI 3.1 valid; 26 of 26 live responses conformed; 10 of 10 records valid against the JSON Schema; 10 of 10 JSON-LD views expanded to PROV entities |
| T4 AI agents (MCP) | six tools; a real record verified valid; a tampered copy rejected ("id does not match the record's content") and quarantined on submission; a malformed message answered with a JSON-RPC parse error, and the server kept answering |
| T5 No regression | through the v1.4 node, 600 of 600 invalid records quarantined and 200 of 200 valid records admitted; 210 entries, chain intact |
| T6 Hardening | 400 hostile requests (random bytes, invalid UTF-8, oversized and missing lengths, 50,000-deep nesting, edits, deletions, random paths) answered 404, 405, 411, 413 or 422; no server error; nothing admitted; the 31st submission in a minute answered 429 |
| T7 Anchor | an OpenTimestamps proof of the log head created and submitted to four public calendars; status pending until Bitcoin confirmation |

**Disclosures.** Before T7 ran, its sealed workflow was found to check its seal from the wrong folder; a copy with that
one line corrected was sealed and run. After T7 ran, the status label written by the first anchoring command read
"confirmed" for a pending proof; the proof was correct, the label was not, and a new anchoring tool reads the status from
the proof itself. The rules file is byte-identical across the v1.3 and v1.4 seals.

## 8. The first records

The log opens with ten records: the sealed tests of the research release *One Selector, Many Domains* (DOI 10.5281/zenodo.24555154),
including those whose criteria were not met, and the protocol's own launch proofs. A forecast about the launch itself
was sealed privately and kept out of the public log, which therefore holds only claims that can be rerun.

## 9. Limits

The checks are mechanical: they verify disclosure, timing, fingerprints, declarations and the absence of known personal
data patterns, not whether a claim is scientifically sound; that is what replications are for. The personal-data
patterns are heuristics. Free mirrors depend on their providers, which is why there are several and why any node can
join. Admission through the public workflow depends on GitHub until other nodes accept submissions. The Bitcoin anchor
confirms hours after stamping. The protocol has one maintainer at release.

## 10. Using it

A person opens the viewer, which re-checks every record in the browser. A research group seals its pre-registration and
results as a claim and receives replications from others. A company makes a benchmark or vendor claim checkable before
publishing it. A public body seals a forecast before a decision and audits it afterwards. A tool connects over HTTP from
the OpenAPI description; an AI agent connects through MCP; a node operator runs `srcx5_net.py serve` and becomes a mirror.

## 11. Availability

Specification v1.4.1 (`SPEC_SRCX5_1_4_1.md`, CC BY 4.0), reference implementation and log (Apache 2.0): [github.com/r-a-elu-architecture/srcx5](https://github.com/r-a-elu-architecture/srcx5).
Viewer: [r-a-elu-architecture.github.io/srcx5](https://r-a-elu-architecture.github.io/srcx5/). Tests and results:
`tests/RESULTS.md` (v1.2) and `tests/v14/RESULTS_V14.md` (v1.4). Companion papers: *One Selector, Many Domains* (DOI
10.5281/zenodo.24555154) and *Blind planning and the error-window law* (DOI 10.5281/zenodo.24555298).

## References

1. Center for Open Science. *OSF Registries.* https://osf.io/registries
2. Wharton Credibility Lab. *AsPredicted.* https://aspredicted.org
3. B. Laurie, A. Langley, E. Kasper. *Certificate Transparency.* RFC 6962, IETF, 2013.
4. Sigstore. *Rekor: a transparency log for software supply-chain metadata.* https://docs.sigstore.dev
5. J. Benet. *IPFS: Content Addressed, Versioned, P2P File System.* arXiv:1407.3561, 2014.
6. L. Moreau, P. Missier (eds.). *PROV-DM: The PROV Data Model.* W3C Recommendation, 2013.
7. Software Heritage. *The universal source code archive.* https://www.softwareheritage.org
8. CERN and OpenAIRE. *Zenodo.* https://zenodo.org
9. W3C. *JSON-LD 1.1.* W3C Recommendation, 2020.
10. OpenAPI Initiative. *OpenAPI Specification 3.1.0*, 2021.
11. JSON Schema. *Draft 2020-12.* https://json-schema.org
12. Model Context Protocol. *Specification*, 2025. https://modelcontextprotocol.io
13. S. Burleigh, K. Fall, E. Birrane. *Bundle Protocol Version 7.* RFC 9171, IETF, 2022.
14. CCSDS. *Space Communications Protocol Standards.* https://public.ccsds.org
15. OpenTimestamps. *Timestamping with Bitcoin.* https://opentimestamps.org
