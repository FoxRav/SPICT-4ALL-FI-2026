# SPICT-4ALL FI — G2 synthesis

Work package: **WP-G2-SYNTHESIS-001**
Run: **G2-20260908-001**
Role: **G2 synthesis reviewer**
**Actual model used: Cursor Grok 4.6**

Configured / planned synthesis role model in `config/model_roles.yaml`: Claude Opus 5 High.
These identities differ. The discrepancy is preserved. Cursor Grok 4.6 performed G2.
Claude Opus, Claude Fable, and GPT-6 did not perform G2.

## Methodological limitation

Forward Translator A used **GPT-6**.
Forward Translator B used **Cursor Grok 4.6**.
G2 synthesis also used **Cursor Grok 4.6**.

Forward Translator B and the G2 synthesis reviewer both used Cursor Grok 4.6. B wording has no preferential authority. Both A and B were judged independently against the exact frozen English source.

This limitation does not block G2.

## Coverage

- Translation-evidence items: **54/54**
- Canonical source units: **53** + source requirement **1**
- Exact A/B wording agreements: **17** (`A_B_AGREE`)
- A/B wording disagreements: **37**
- `SELECT_A`: 12
- `SELECT_B`: 15
- `COMBINE_A_B`: 10
- `NEW_SYNTHESIS`: 0

Every unit has exactly one classification. Disagreements have an explicit
source-fidelity rationale. Status is `READY_FOR_HUMAN_REVIEW`: model-generated G2 synthesis
evidence, not human approval. No human-approval status is recorded.

## Binding human wording used

- T-002 elinikää lyhentävät terveydentilat (S4A-2026-001, S4A-2026-042)
- T-013 hengityskone (S4A-2026-035)
- T-016 kokonaisvaltainen hoito (S4A-2026-049)
- less well → terveydentila on heikentynyt (S4A-2026-001, S4A-2026-042)
- less able to manage usual activities → toimintakyky on heikentynyt with tavanomaisissa toimissa (S4A-2026-004, S4A-2026-014)
- not well enough for cancer treatment → ei ole riittävän hyväkuntoinen syöpähoitoon (S4A-2026-017)

No missing decision IDs were invented. Glossary APPROVED rows remain 0.

## Source authority preserved, not resolved

- `S4A-2026-000`: Finnish synthesis produced; UNRESOLVED; not insertable; publication-blocking where currently defined.
- `S4A-REQ-2026-001`: Finnish synthesis produced; noncanonical; unresolved canonical omission; publication-blocking; not silently added to canonical membership.

## Genuine remaining wording uncertainties

These did not block a working synthesis:

- Supportive care has no approved Finnish project term (S4A-2026-000).
- Frailty/hauraus has no recorded final human term (S4A-2026-021).
- spiritual is kept as henkinen ja hengellinen so it is not narrowed to religion only (S4A-2026-049).
- stroke/aivohalvaus scope remains a prior T1 SAMI item (S4A-2026-047).
- chest infections is rendered plainly as rintakehän infektioita rather than medicalized (S4A-2026-045).
- The English relative clause in S4A-2026-002 can attach to health problems or to both alternatives; Finnish follows the nearest-antecedent reading.

## Document-level review

The 54 Finnish units were reread as one body for omission, addition, negation,
modality, time, agency, roles, alternatives, causality, narrowing/expansion,
treatment choice, and terminology consistency. Carer is huolehtiva ihminen
(006, 046). Physical health is fyysinen (005, 041, 042, 047). Communicate is
viestiä (036, 043). Dialysis is dialyysi without an added hoito (019, 020).
Resting/moving/walking a few steps is aligned (015, 025). T-002, T-013, T-016
and the three recorded unbound human wordings are preserved where they apply.

Mechanical checks do not prove semantic or clinical correctness.
These results are not clinical validation.

## Frozen inputs

- `work/agent-a/candidates.jsonl`: `82d06571c855c87d04e015bf905b1943c5fcd31e68827695fd4cfceb52f4c2cd`
- `work/agent-b/runs/G1-B-20260908-002/candidates.jsonl`: `6033c9970d0b61fd64dfc5c0350b6c97a9ba3cf35725d2f8db7aee79752a25a1`
- `work/agent-b/candidates.jsonl` (historical original B only): `0bb36348713bf951fb5166c4ebed53d66afc6f3436c5790d790d0a53fe23f640`
- G1 gate ZIP: `6e8846bc233070f3b18f7a3fbba81cb2bd4c04090afa5fbfe9be5aa0fc4fd0ef`

## Output hashes

- `work/synthesis/G2-20260908-001/candidates.jsonl`: `76462191d3ad2a83c878982a1460443f322437e547b747f6267f4a29d887c619`
- `work/synthesis/G2-20260908-001/synthesis_decisions.jsonl`: `760ddd2854712c9557438b8cfb4743200f55cf5b497cbb46aa0a9f10ad9f0d6d`

G3 was not started. No commit or push is performed by this builder.
