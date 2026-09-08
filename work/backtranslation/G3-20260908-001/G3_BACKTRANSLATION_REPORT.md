# SPICT-4ALL FI — G3 blind back-translation

Work package: **WP-G3-BLIND-BACKTRANSLATION-AUDIT-001**
Run: **G3-20260908-001**
Role: **Blind back-translator**
Coverage: **54/54**

## Actual model provenance

- **model:** GPT-5.6 Sol
- **reasoning_effort:** High
- **environment:** ChatGPT Temporary Chat

Configured / planned role model in `config/model_roles.yaml`: GPT-5.6 Sol Medium.
These identities differ. The discrepancy is preserved.

Recorded from WP-G3-BLIND-BACKTRANSLATION-AUDIT-001 as the operator-stated ChatGPT Temporary Chat session that produced back_translation.jsonl. No independent API request log is packaged.

## Method

Blind FI→EN back-translation. The back-translator received only Finnish-only
blind input (`unit_id`, `text_fi`).

The back-translator received only the Finnish-only blind input (work/backtranslation/G3-20260908-001/blind_input.jsonl: unit_id and text_fi). This G3 audit does not claim independent observation of the Temporary Chat session beyond the operator-recorded method and the on-disk artifacts.

This work package does **not** compare the back-translation with the original
English source. **No semantic comparison** with the frozen English SPICT source
was performed in G3. That comparison belongs to a later review stage.

G3 output is evidence for later comparison. It is not human approval and not
clinical validation. These mechanical checks are not clinical validation.

G4 was not started.

## Frozen artifacts

- `work/backtranslation/G3-20260908-001/blind_input.jsonl`: `bbe32669ae4d0f25c3013f24573f14c2823021a96cbffc1ced4fe3f0f456f634`
- `work/backtranslation/G3-20260908-001/back_translation.jsonl`: `e674a7f0a69ed05c554eaade38e4dbd8025c1f34df0499a8fc4cc9a15c99f00f`
- `work/synthesis/G2-20260908-001/candidates.jsonl` (auditor derivation source only; not a translator input): `76462191d3ad2a83c878982a1460443f322437e547b747f6267f4a29d887c619`

Finnish blind `text_fi` matches G2 `candidate_fi` for all 54 IDs, including
`S4A-2026-000` and `S4A-REQ-2026-001`. Source-authority issues were not resolved.

## Recorded back-translator uncertainties

- `S4A-2026-025`: The wording "when the chest is at its best" is unusual and may be ambiguous; it is translated literally from the Finnish.

No G3 JSONL was rewritten by this metadata writer.
