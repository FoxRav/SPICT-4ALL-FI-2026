# SPICT-4ALL FI — G1 gate closure

Work package: **WP-G1-GATE-CLOSURE-001**
Packaged: 2026-09-08
Status: **G1 independent forward translations complete. G2 not started.**

This package closes G1 after both independent forward translations and the
main-branch G1/T1 isolation integration fix. It is not a translation task and
does not start synthesis, back-translation, or critic review.

## Independent runs

| Role | Authoritative artifact | Actual model | Configured / planned role model |
| --- | --- | --- | --- |
| Forward Translator A | `work/agent-a/candidates.jsonl` | **GPT-6** | GPT-5.6 Sol Medium |
| Forward Translator B R2 | `work/agent-b/runs/G1-B-20260908-002/candidates.jsonl` | **Cursor Grok 4.6** | Claude Fable 5.1 High |

The planned/configured identities in `config/model_roles.yaml` differ from the
actual models used. That discrepancy is preserved. Exact GPT-6 backend variant
and effort were not exposed in the Agent A run record.

Original Agent B run `work/agent-b/candidates.jsonl` remains byte-for-byte
preserved as G1-B-20260908-001. R2 is the authoritative B wording for G1 close.

## Coverage

- Agent A: **54/54** (53 canonical + 1 source requirement). IDs unique. No blank Finnish.
- Agent B R2: **54/54** (53 canonical + 1 source requirement). IDs unique. No blank Finnish.
- A and B share the identical frozen source universe, exact English, and source SHA-256 per ID.
- Schema states remain non-approval: Agent A `DRAFT`, Agent B R2 `READY_FOR_SYNTHESIS`.
- No `HUMAN_APPROVED` status is inferred. No clinical validation is claimed.

## Unresolved authority preserved

- `S4A-2026-000` remains unresolved and non-insertable.
- `S4A-REQ-2026-001` remains noncanonical, unresolved, and publication-blocking.

## Upstream audit ZIPs

The A and B-R2 audit ZIPs are **not nested** in this archive. They were hashed
and independently verified in place. Sidecars are included.

- `SPICT4ALL-FI-G1-A-forward-translation-audit-20260908.zip`: cfffef8b6adac0586d00c3ca450143626a710ec40cff2b7d99b969f0a7970cd2 (2938533 bytes) — PASS
- `SPICT4ALL-FI-G1-B-R2-forward-translation-audit-20260908.zip`: 459f79ede3abde0c0e64a9e7c63b4549a4c1911c1bbe702b2f63ec6485729f4b (2992334 bytes) — PASS

## Frozen candidate hashes

- `work/agent-a/candidates.jsonl`: `82d06571c855c87d04e015bf905b1943c5fcd31e68827695fd4cfceb52f4c2cd`
- `work/agent-b/candidates.jsonl`: `0bb36348713bf951fb5166c4ebed53d66afc6f3436c5790d790d0a53fe23f640`
- `work/agent-b/runs/G1-B-20260908-002/candidates.jsonl`: `6033c9970d0b61fd64dfc5c0350b6c97a9ba3cf35725d2f8db7aee79752a25a1`

## Integration isolation

Historical T1 tests continue to validate a pre-G1 view. G1 tests validate the
current G1 view. `src/spict4all/g1_t1_isolation.py`, `tests/conftest.py`, and
`tests/test_g1_t1_isolation.py` hide both `work/agent-a/**` and `work/agent-b/**`
except `.gitkeep` while T1 inventory is evaluated. Historical T1 validator files
`src/spict4all/adjudication.py`, `src/spict4all/terminology_closure.py`, and
`tests/test_adjudication.py` match baseline `2aa066fdba27fa083ff9ad78f285c0751d3f085f`.

## Validation

The live repository passed **341 tests** plus official-source, requirement,
canonical, governance, terminology, compileall, strict mypy, and ruff checks
before sealing. Full command outputs are in `G1_GATE_VALIDATION_RESULTS.json`.
Those checks are mechanical integrity results, not clinical validation.

Verify with `python scripts/verify_g1_gate_closure.py /path/to/SPICT4ALL-FI-G1-gate-closure-audit-20260908.zip` while
keeping the companion hash files alongside the ZIP.

No Finnish candidate was changed while creating this closure. G2 was not started.
