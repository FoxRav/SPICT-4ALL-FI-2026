# G1-B-20260908-002 correction report

Work package: **WP-G1-B-CORRECTION-R2-001**
Corrected run: **G1-B-20260908-002**
Original run: **G1-B-20260908-001** (byte-for-byte unchanged)

## Purpose

Independent audit found that G1-B-20260908-001 did not apply three explicit
Project Owner wording decisions recorded in
`terminology/adjudication/T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md`. Those
decisions pre-date G1 and are authorized input. They are not Agent A evidence.

This run is a targeted correction. It is not synthesis.

## Independence

- Agent A was not inspected.
- No Agent A translation evidence was supplied.
- No synthesis was performed.
- No G2 was performed.
- No human approval state was created.
- Schema status remains `READY_FOR_SYNTHESIS` (repository forward-run marker, not approval).

## Project Owner wordings applied exactly

1. less well → `terveydentila on heikentynyt` (`S4A-2026-001`, `S4A-2026-042`)
2. less able to manage usual activities → `toimintakyky on heikentynyt` (`S4A-2026-004`, `S4A-2026-014`), with usual/tavanomaiset activities kept in the surrounding sentence
3. not well enough for cancer treatment → `ei ole riittävän hyväkuntoinen syöpähoitoon` (`S4A-2026-017`)

No terminology decision IDs were invented for these wordings.
T-002, T-013 and T-016 remain applied.

## Changed units

Exactly five `candidate_fi` fields changed. No other Finnish candidate was edited.

- `S4A-2026-001`: `SPICT auttaa meitä etsimään ihmisiä, joilla on elinikää lyhentäviä terveydentiloja ja jotka voivat huonommin. Nämä ihmiset tarvitsevat nyt enemmän apua ja hoitoa sekä suunnitelman tulevaa hoitoa varten.` → `SPICT auttaa meitä etsimään ihmisiä, joilla on elinikää lyhentäviä terveydentiloja ja joiden terveydentila on heikentynyt. Nämä ihmiset tarvitsevat nyt enemmän apua ja hoitoa sekä suunnitelman tulevaa hoitoa varten.`
- `S4A-2026-004`: `Selviytyy tavanomaisista toimistaan aiempaa huonommin; ei ole yhtä hyvässä kunnossa kuin ennen.
(Henkilö on usein vuoteessa tai tuolissa yli puolet päivästä.)` → `Toimintakyky on heikentynyt tavanomaisissa toimissa; ei ole yhtä hyvässä kunnossa kuin ennen.
(Henkilö on usein vuoteessa tai tuolissa yli puolet päivästä.)`
- `S4A-2026-014`: `Selviytyy tavanomaisista toimistaan aiempaa huonommin, ja terveys heikkenee.` → `Toimintakyky on heikentynyt tavanomaisissa toimissa, ja terveys heikkenee.`
- `S4A-2026-017`: `Ei ole tarpeeksi hyvässä kunnossa syöpähoitoon, tai hoito on oireiden helpottamiseksi.` → `Ei ole riittävän hyväkuntoinen syöpähoitoon, tai hoito on oireiden helpottamiseksi.`
- `S4A-2026-042`: `Ihmiset, jotka voivat huonommin ja joilla on muita elinikää lyhentäviä ruumiillisia tai henkisiä sairauksia tai terveydentiloja. Hoitoa ei ole saatavilla, tai se ei tehoa hyvin.` → `Ihmiset, joiden terveydentila on heikentynyt ja joilla on muita elinikää lyhentäviä ruumiillisia tai henkisiä sairauksia tai terveydentiloja. Hoitoa ei ole saatavilla, tai se ei tehoa hyvin.`

Unchanged `candidate_fi` count: 49

## Validation snapshot

- candidate_count: 54
- canonical_count: 53
- source_requirement_count: 1
- schema_valid: True
- coverage_complete: True
