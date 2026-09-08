# SPICT-4ALL FI — G5 human review packet

Work package: **WP-G5-HUMAN-REVIEW-PREPARATION-001**
Run: **G5-20260908-001**
Role: **G5 human-review preparation (not the human adjudicator)**
Preparation model: **Cursor Grok 4.6**
Coverage: **54/54**
Status: **PREPARATION_COMPLETE_AWAITING_HUMAN_DISPOSITION**

This package prepares decision material. It is not human adjudication, not
human approval, and not clinical validation. No option below is pre-checked.
No Finnish G2 candidate was changed. No G3 back-translation was changed. No
G4 critic output was changed. Source-authority conflicts remain unresolved.

## Human authority

Every one of the 54 units requires an explicit human disposition
at G5. Do not interpret absence of a critic finding as acceptance. Do not treat
AI agreement as acceptance. Do not mark anything HUMAN_APPROVED in this
preparation package.

A reviewer may inspect critic-clean units as a batch, but the resulting
evidence must still create an explicit disposition record for each unit.

## Review tiers

- **Tier 1 — priority human review** (11): `S4A-2026-001`, `S4A-2026-008`, `S4A-2026-009`, `S4A-2026-017`, `S4A-2026-021`, `S4A-2026-025`, `S4A-2026-026`, `S4A-2026-036`, `S4A-2026-042`, `S4A-2026-045`, `S4A-2026-049`
- **Tier 2 — low-severity review** (10): `S4A-2026-000`, `S4A-2026-003`, `S4A-2026-004`, `S4A-2026-014`, `S4A-2026-018`, `S4A-2026-033`, `S4A-2026-034`, `S4A-2026-040`, `S4A-2026-043`, `S4A-2026-047`
- **Tier 3 — no-critic-issue review** (33): `S4A-2026-002`, `S4A-2026-005`, `S4A-2026-006`, `S4A-2026-007`, `S4A-2026-010`, `S4A-2026-011`, `S4A-2026-012`, `S4A-2026-013`, `S4A-2026-015`, `S4A-2026-016`, `S4A-2026-019`, `S4A-2026-020`, `S4A-2026-022`, `S4A-2026-023`, `S4A-2026-024`, `S4A-2026-027`, `S4A-2026-028`, `S4A-2026-029`, `S4A-2026-030`, `S4A-2026-031`, `S4A-2026-032`, `S4A-2026-035`, `S4A-2026-037`, `S4A-2026-038`, `S4A-2026-039`, `S4A-2026-041`, `S4A-2026-044`, `S4A-2026-046`, `S4A-2026-048`, `S4A-2026-050`, `S4A-2026-051`, `S4A-2026-052`, `S4A-REQ-2026-001`

Highlight especially `S4A-2026-025` and
`S4A-2026-045`.

## Existing human-decision conflicts

`S4A-2026-001`, `S4A-2026-042`, `S4A-2026-017`

Present both the earlier Project Owner wording and the critic evidence.
Do not overwrite or automatically retain the old decision.

`S4A-2026-021` has no final recorded human wording for frailty/hauraus.
Preserve that fact.

## Domain-expert review recommended

Recommended IDs: `S4A-2026-017`, `S4A-2026-021`, `S4A-2026-025`, `S4A-2026-026`, `S4A-2026-045`, `S4A-2026-049`

This field is true only where there is a genuine clinical / healthcare
terminology / referent question. This list itself is not clinical review.

## Source authority — separate track

- `S4A-2026-000`: UNRESOLVED, publication-blocking, not insertable.
- `S4A-REQ-2026-001`: NONCANONICAL, canonical omission unresolved,
  publication-blocking.

The human translation reviewer may review Finnish wording for these units,
but must not resolve the source-authority question.

## Units in canonical order

## S4A-2026-000

> SOURCE AUTHORITY — SEPARATE TRACK. Publication-blocking. Not insertable. Finnish wording review does not resolve authority.

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `e0d92d4423ed4dd44c3905348ccb15531f9d0d8635b6d9e3e6aed8f7d5977a79`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Supportive and Palliative Care Indicators Tool (SPICT-4ALL-……)
```

**Current Finnish G2 candidate**
```
Tukea antavan ja palliatiivisen hoidon tunnusmerkkityökalu (SPICT-4ALL-……)
```

**Blind back-translation**
```
Supportive and palliative care indicator tool (SPICT-4ALL-……)
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · plain_language, terminology
Title meaning is recognisable, but the compound is unnatural Finnish and slightly miscasts indicators. Stylistic/terminology concern without a material change of tool identity.
Proposed Finnish (review evidence only; not applied):
```
Tukea antavan ja palliatiivisen hoidon tunnusmerkkien työkalu (SPICT-4ALL-……)
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** UNRESOLVED
**Publication-blocking:** yes
Source-authority status remains UNRESOLVED. Not eligible for document insertion. Publication-blocking. Critic findings do not resolve this. Separate from critic severity.
The translation reviewer may review Finnish wording but must not resolve the source-authority question.

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-001

> EXISTING HUMAN DECISION CONFLICT: present both the earlier human decision and the critic evidence. Do not overwrite or automatically retain the old decision.

- **Review tier:** TIER_1
- **Finding status:** CORROBORATED
- **Combined review priority:** MEDIUM
- **source_text_sha256:** `073f41ea2df0103ff84d71ac3bf63cdbc88ed4ce579604fbbac10aea11652aac`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
The SPICT helps us look for people who have life shortening health conditions and are less well. These people need more help and care now, and a plan for care in the future.
```

**Current Finnish G2 candidate**
```
SPICT auttaa meitä etsimään ihmisiä, joilla on elinikää lyhentäviä terveydentiloja ja joiden terveydentila on heikentynyt. Nämä ihmiset tarvitsevat nyt enemmän apua ja hoitoa sekä suunnitelman tulevasta hoidosta.
```

**Blind back-translation**
```
SPICT helps us look for people who have life-shortening health conditions and whose health has deteriorated. These people now need more help and care, as well as a plan for future care.
```

**Critic A:** ISSUE · MEDIUM · changed time or frequency, meaning narrowed
A current state of being less well and a stated deterioration are not always equivalent. The Finnish may therefore narrow eligibility to people whose worsening can be framed as a decline.
Proposed Finnish (review evidence only; not applied):
```
SPICT auttaa meitä etsimään ihmisiä, joilla on elinikää lyhentäviä terveydentiloja ja jotka voivat huonommin. Nämä ihmiset tarvitsevat nyt enemmän apua ja hoitoa sekä suunnitelman tulevasta hoidosta.
```

**Critic B:** ISSUE · LOW · plain_language, time_degree, agency
Core case-finding meaning is kept, but less well is recast as deteriorated health status. Unlikely to change who is identified, still worth a plain-language check.
Proposed Finnish (review evidence only; not applied):
```
SPICT auttaa meitä etsimään ihmisiä, joilla on elinikää lyhentäviä terveydentiloja ja jotka voivat huonommin. Nämä ihmiset tarvitsevat nyt enemmän apua ja hoitoa sekä suunnitelman tulevasta hoidosta.
```

**Existing human decision:** Project Owner: less well -> terveydentila on heikentynyt. T-002: elinikää lyhentävät terveydentilat. Critics raised source-fidelity (current poorer state versus recorded deterioration). EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5. Do not auto-retain or overwrite.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-002

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `4e2ea44a5cb6778dfe05cadc1c17810b91e4e245ac7d2d9f0eb869b523fb452d`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Does this person have signs of poor health or health problems that are getting worse?
```

**Current Finnish G2 candidate**
```
Onko tällä henkilöllä merkkejä huonosta terveydentilasta tai terveysongelmia, jotka pahenevat?
```

**Blind back-translation**
```
Does this person have signs of poor health or health problems that are getting worse?
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-003

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `e0833c16f94535ce3009a1737201e39f1b822baa1447edbc35b6f8a37a6d756a`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Urgent or emergency hospital admission(s) or visits.
```

**Current Finnish G2 candidate**
```
Kiireellinen tai päivystyksellinen sairaalaan otto(t) tai käynnit.
```

**Blind back-translation**
```
Urgent or emergency hospital admission(s) or visits.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · plain_language, terminology
Meaning is recoverable, but the parenthetical plural is a literal English device and otto is not plain Finnish.
Proposed Finnish (review evidence only; not applied):
```
Kiireellinen tai päivystyksellinen sairaalaan ottaminen tai käynnit.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-004

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `e2a76846cca5d053af8161133c81edddbe40529b37fde2bfde986af56ce60c3c`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Less able to manage usual activities; not as well as they used to be.
(Person often stays in bed or in a chair for more than half the day.)
```

**Current Finnish G2 candidate**
```
Toimintakyky on heikentynyt tavanomaisissa toimissa; vointi ei ole yhtä hyvä kuin ennen.
(Henkilö viettää usein yli puolet päivästä vuoteessa tai tuolissa.)
```

**Blind back-translation**
```
Functioning has declined in usual activities; the person's condition is not as good as before.
(The person often spends more than half of the day in bed or in a chair.)
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · plain_language, agency
Sense is close, but the person is no longer the grammatical agent of being less able. Same pattern as S4A-2026-014.
Proposed Finnish (review evidence only; not applied):
```
Pystyy huonommin hoitamaan tavanomaisia toimia; vointi ei ole yhtä hyvä kuin ennen.
(Henkilö viettää usein yli puolet päivästä vuoteessa tai tuolissa.)
```

**Existing human decision:** Project Owner: less able to manage usual activities -> toimintakyky on heikentynyt.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-005

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `fdcefa0555355b1ced3795bd3b6068b5a351d4a7f2498a9d6b941094a3606f21`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Needs more help and care from others due to increasing physical and/or mental health problems.
```

**Current Finnish G2 candidate**
```
Tarvitsee muilta enemmän apua ja hoitoa lisääntyvien fyysisen terveyden ja/tai mielenterveyden ongelmien vuoksi.
```

**Blind back-translation**
```
Needs more help and care from others because of increasing physical health and/or mental health problems.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-006

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `ecdb4474294eb1f6797305ec921a2f58658b85ca3875d9e639de4ccb3e322601`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Person’s carer needs more help and support.
```

**Current Finnish G2 candidate**
```
Henkilöstä huolehtiva ihminen tarvitsee enemmän apua ja tukea.
```

**Blind back-translation**
```
The person who cares for them needs more help and support.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-007

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `7181dd9f28e654ec269bda2ff32da7c18405eca65e4969279686e38741064214`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Has clearly lost weight over the last few months; or stays too thin.
```

**Current Finnish G2 candidate**
```
On selvästi laihtunut muutaman viime kuukauden aikana; tai pysyy liian laihana.
```

**Blind back-translation**
```
Has clearly lost weight during the last few months; or remains too thin.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-008

- **Review tier:** TIER_1
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** MEDIUM
- **source_text_sha256:** `4001d97a18450bfb36e8eaf191283f8cceccbbe86bbd1d331d9e74621a7d8eb7`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Has troublesome symptoms most of the time despite good treatment of their health problems.
```

**Current Finnish G2 candidate**
```
Hänellä on hankalia oireita suurimman osan ajasta, vaikka hänen terveysongelmiaan hoidetaan hyvin.
```

**Blind back-translation**
```
Has troublesome symptoms most of the time, even though their health problems are treated well.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · MEDIUM · plain_language, terminology, adversarial
Possible shift from adequate treatment of the problems to being treated well. Needs human check; not a proven reversal.
Proposed Finnish (review evidence only; not applied):
```
Hankalia oireita suurimman osan ajasta huolimatta terveysongelmien hyvästä hoidosta.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-009

- **Review tier:** TIER_1
- **Finding status:** CORROBORATED
- **Combined review priority:** MEDIUM
- **source_text_sha256:** `792e53797023341c64f79e3598752320b23375c8bc346e14dd6906e003362f29`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
The person (or family) asks for palliative care; chooses to reduce, stop or not have treatment; or wishes to focus on quality of life.
```

**Current Finnish G2 candidate**
```
Henkilö (tai perhe) pyytää palliatiivista hoitoa; valitsee hoidon vähentämisen, lopettamisen tai ottamatta jättämisen; tai toivoo keskittymistä elämänlaatuun.
```

**Blind back-translation**
```
The person (or family) asks for palliative care; chooses to reduce, stop, or not take treatment; or wishes to focus on quality of life.
```

**Critic A:** ISSUE · LOW · ambiguous Finnish
The surrounding word 'valitsee' limits the risk, so this is primarily a wording ambiguity rather than a likely material mistranslation.
Proposed Finnish (review evidence only; not applied):
```
Henkilö (tai perhe) pyytää palliatiivista hoitoa; valitsee hoidon vähentämisen tai lopettamisen tai sen, ettei ota hoitoa vastaan; tai toivoo keskittymistä elämänlaatuun.
```

**Critic B:** ISSUE · MEDIUM · terminology, agency, omission_addition
Choice agency is kept, but not have treatment is liable to be read as not taking treatment. Agency on wishes to focus is also weakened.
Proposed Finnish (review evidence only; not applied):
```
Henkilö (tai perhe) pyytää palliatiivista hoitoa; valitsee hoidon vähentämisen, lopettamisen tai sen, ettei hoitoa oteta; tai haluaa keskittyä elämänlaatuun.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-010

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `91aa0e8b9dd807ae79c1ed0d573e0faf66910befda4681cae6c821e8e5687c6b`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Does this person have any of these health problems?
```

**Current Finnish G2 candidate**
```
Onko tällä henkilöllä jokin näistä terveysongelmista?
```

**Blind back-translation**
```
Does this person have any of these health problems?
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-011

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `f2c28b5295d9ad14e2e24f8467e0dab646338858d7f11d5267b094e875e36edb`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Cancer
```

**Current Finnish G2 candidate**
```
Syöpä
```

**Blind back-translation**
```
Cancer
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-012

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `96483c2d15c955cd20a7e3f77f7cfe11675e57abac2b8253523ca7f90a49f219`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Heart or circulation problems
```

**Current Finnish G2 candidate**
```
Sydämen tai verenkierron ongelmat
```

**Blind back-translation**
```
Heart or circulation problems
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-013

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `268f55cc97dd320e421d37a95d15154fe7a9996c5eac7349e37b35a9a2ff388d`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Kidney problems
```

**Current Finnish G2 candidate**
```
Munuaisongelmat
```

**Blind back-translation**
```
Kidney problems
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-014

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `99fde2e084601e17d09b4d21f6fd5332555634a614361a9d6df4299582c02fbb`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Less able to manage usual activities and health is getting poorer.
```

**Current Finnish G2 candidate**
```
Toimintakyky on heikentynyt tavanomaisissa toimissa, ja terveys heikkenee.
```

**Blind back-translation**
```
Functioning has declined in usual activities, and health is deteriorating.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · plain_language, agency
Second clause is faithful; first clause repeats the 004 agency/plain-language issue.
Proposed Finnish (review evidence only; not applied):
```
Pystyy huonommin hoitamaan tavanomaisia toimia, ja terveys heikkenee.
```

**Existing human decision:** Project Owner: less able to manage usual activities -> toimintakyky on heikentynyt.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-015

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `a2033df46c00ed0fa3eaae26c5185127d715d9f8a71db3b98965ac006919465c`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Heart failure or heart blood vessel disease. Short of breath or has chest pain when resting, moving or walking a few steps.
```

**Current Finnish G2 candidate**
```
Sydämen vajaatoiminta tai sydämen verisuonisairaus. Hengenahdistusta tai rintakipua levätessä, liikkuessa tai kävellessä muutaman askeleen.
```

**Blind back-translation**
```
Heart failure or disease of the heart's blood vessels. Shortness of breath or chest pain when resting, moving, or walking a few steps.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-016

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `caf76353b40f44135d84633d46d756043db126bfd293f6b08f0902384e619f1b`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Kidneys are not working well; general health is getting poorer.
```

**Current Finnish G2 candidate**
```
Munuaiset eivät toimi hyvin; yleinen terveys heikkenee.
```

**Blind back-translation**
```
The kidneys are not working well; general health is deteriorating.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-017

> EXISTING HUMAN DECISION CONFLICT: present both the earlier human decision and the critic evidence. Do not overwrite or automatically retain the old decision.

- **Review tier:** TIER_1
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** MEDIUM
- **source_text_sha256:** `9206d4bd4125ed5c6ef1006bbbe74035d8c4ee3021400d0bcaf06ab0908a552f`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Not well enough for cancer treatment or treatment is to help with symptoms.
```

**Current Finnish G2 candidate**
```
Ei ole riittävän hyväkuntoinen syöpähoitoon, tai hoito on oireiden helpottamiseksi.
```

**Blind back-translation**
```
Is not well enough for cancer treatment, or the treatment is for relieving symptoms.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · MEDIUM · plain_language, terminology, adversarial
Fluent Finnish that ordinary users may hear as fitness rather than insufficient health for cancer treatment.
Proposed Finnish (review evidence only; not applied):
```
Ei ole riittävän hyvässä kunnossa syöpähoitoon, tai hoito on oireiden helpottamiseksi.
```

**Existing human decision:** Project Owner: not well enough for cancer treatment -> ei ole riittävän hyväkuntoinen syöpähoitoon. Critic B raised a possible hyväkuntoinen / physical-fitness ambiguity. EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5. Do not decide.
**Domain expert review recommended:** yes. Possible hyväkuntoinen / physical-fitness reading versus clinical well-enough for cancer treatment. Not a wording-style preference.
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-018

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `058b7cb6ee5a40a7d514f92acad1533f77a63576601024e2667ffc02e6aea25f`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Leg problems due to poor blood circulation; surgery is not possible.
```

**Current Finnish G2 candidate**
```
Jalkaongelmia huonon verenkierron vuoksi; leikkaus ei ole mahdollinen.
```

**Blind back-translation**
```
Leg problems because of poor circulation; surgery is not possible.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · plain_language, terminology
Impossibility and circulation cause are faithful; jalka is a mild limb/foot ambiguity.
Proposed Finnish (review evidence only; not applied):
```
Jalkojen ongelmia huonon verenkierron vuoksi; leikkaus ei ole mahdollinen.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-019

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `2b7fddfeb4727487c69bcfde27c5f60a91c1e74206c30068035e330753f18303`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Stopping kidney dialysis or choosing palliative care instead of starting dialysis.
```

**Current Finnish G2 candidate**
```
Munuaisdialyysin lopettaminen tai palliatiivisen hoidon valitseminen dialyysin aloittamisen sijaan.
```

**Blind back-translation**
```
Stopping kidney dialysis or choosing palliative care instead of starting dialysis.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-020

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `8ce559219ef352629369543d5a95eeae1d37c880c65715511d69634ae6eefcb2`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Stopping or not starting dialysis
```

**Current Finnish G2 candidate**
```
Dialyysin lopettaminen tai aloittamatta jättäminen
```

**Blind back-translation**
```
Stopping dialysis or not starting it
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-021

> Frailty/hauraus: no final recorded human wording decision. Preserve that fact. Do not invent a term.

- **Review tier:** TIER_1
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** MEDIUM
- **source_text_sha256:** `ae652fc158e53bfb5c9b52b9c94f57696f0d433f2240c5345a6d99b48ba02f73`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Dementia or frailty
```

**Current Finnish G2 candidate**
```
Dementia tai hauraus
```

**Blind back-translation**
```
Dementia or frailty
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · MEDIUM · plain_language, terminology
Heading may fail as patient-facing frailty language. Terminology needs human review; this is not an adjudication of the clinical label.
Proposed Finnish (review evidence only; not applied):
```
Dementia tai hauraus ja heikkous
```

**Existing human decision:** NO_FINAL_RECORDED_HUMAN_WORDING_DECISION. Frailty/hauraus was discussed before G1; no final recorded human term is preserved.
**Domain expert review recommended:** yes. Frailty / hauraus is a healthcare concept with no final recorded human wording. Not a stylistic Finnish choice.
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-022

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `fd5a7429de80300bad8e049546d350e782e81952420927c1e487b0d285007c11`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Respiratory problems
```

**Current Finnish G2 candidate**
```
Hengitysongelmat
```

**Blind back-translation**
```
Breathing problems
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-023

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `2008353ef1fa350f45f0267d8e2116677fce16728e66b811230748faa8400728`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Liver problems
```

**Current Finnish G2 candidate**
```
Maksaongelmat
```

**Blind back-translation**
```
Liver problems
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-024

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `b946f5676d14ac3e69ba2303043942ee4e09a1da960a77735c4aedc09e3bc02e`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Unable to dress, walk or eat without help.
```

**Current Finnish G2 candidate**
```
Ei pysty pukeutumaan, kävelemään tai syömään ilman apua.
```

**Blind back-translation**
```
Cannot dress, walk, or eat without help.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-025

> PRIORITY HIGHLIGHT: Critic A HIGH and Critic B HIGH. Literal Finnish rendering of 'when the chest is at its best'.

- **Review tier:** TIER_1
- **Finding status:** CORROBORATED
- **Combined review priority:** HIGH
- **source_text_sha256:** `4370111602ffcff5b4b2fe5b501df2b001b5424b4813493a605dacc5e6472802`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
More unwell with long term lung problems. Short of breath when resting, moving or walking a few steps even when the chest is at its best.
```

**Current Finnish G2 candidate**
```
Vointi on huonompi pitkäaikaisten keuhko-ongelmien yhteydessä. Hengenahdistusta levätessä, liikkuessa tai kävellessä muutaman askeleen silloinkin, kun rintakehä on parhaimmillaan.
```

**Blind back-translation**
```
The person's condition is worse with long-term lung problems. Shortness of breath when resting, moving, or walking a few steps even when the chest is at its best.
```

**Critic A:** ISSUE · HIGH · changed referent, ambiguous Finnish, clinical concept changed
This is not merely word order or style: the Finnish literalization creates a semantically defective phrase at a clinically relevant criterion.
Proposed Finnish (review evidence only; not applied):
```
Vointi on huonompi pitkäaikaisten keuhko-ongelmien yhteydessä. Hengenahdistusta levätessä, liikkuessa tai kävellessä muutaman askeleen silloinkin, kun keuhkojen tila on parhaimmillaan.
```

**Critic B:** ISSUE · HIGH · plain_language, terminology, adversarial
Literal English-idiom translation that ordinary users can misread. Probable material error in the baseline-breathing clause.
Proposed Finnish (review evidence only; not applied):
```
Vointi on huonompi pitkäaikaisten keuhko-ongelmien kanssa. Hengenahdistusta levätessä, liikkuessa tai kävellessä muutaman askeleen silloinkin, kun hengitys on parhaimmillaan.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** yes. Literal rendering of 'when the chest is at its best' raises a clinical-referent question about baseline respiratory status.
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-026

- **Review tier:** TIER_1
- **Finding status:** CORROBORATED
- **Combined review priority:** MEDIUM
- **source_text_sha256:** `af527f00432f81a06cb3f05cdda159821b786bc73318c0fb577f55eac57dc04e`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Worsening liver problems in the past year with complications like:
```

**Current Finnish G2 candidate**
```
Kuluneen vuoden aikana pahentuneita maksaongelmia, joihin liittyy lisäongelmia, kuten:
```

**Blind back-translation**
```
Liver problems that have worsened during the past year, with additional problems such as:
```

**Critic A:** ISSUE · LOW · meaning broadened
The liver-problem context still links the listed items to the condition, so the likely impact is low, but 'lisäongelmia' is semantically less specific than 'complications'.
Proposed Finnish (review evidence only; not applied):
```
Kuluneen vuoden aikana pahentuneita maksaongelmia, joihin liittyy komplikaatioita, kuten:
```

**Critic B:** ISSUE · MEDIUM · terminology, omission_addition
Time and worsening are faithful; complications is softened into extra problems and needs review.
Proposed Finnish (review evidence only; not applied):
```
Kuluneen vuoden aikana pahentuneita maksaongelmia, joihin liittyy liitännäisongelmia, kuten:
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** yes. Complications of liver disease versus extra problems is a clinical terminology/referent question, not a fluency preference.
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-027

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `adb8720dd5159892938a27769ffa7b771bd1f74d02cc3bb4922751f115123f94`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
fluid building up in the belly
```

**Current Finnish G2 candidate**
```
nesteen kertymistä vatsaan
```

**Blind back-translation**
```
fluid accumulating in the abdomen
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-028

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `893dc30e9dbb7c7b6604094e6b3b32e28d57e18d24b141b094f8f05995c6ea34`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
being confused at times
```

**Current Finnish G2 candidate**
```
ajoittaista sekavuutta
```

**Blind back-translation**
```
occasional confusion
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-029

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `7ee57d9b958f5eed889774298637a6a7646c7b7d671773f8a9abad9e3d20ccae`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
kidneys not working well
```

**Current Finnish G2 candidate**
```
munuaiset eivät toimi hyvin
```

**Blind back-translation**
```
the kidneys are not working well
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-030

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `f7c719ccac9bfcb69d5a06bb091cce53a8f48edc8f55a49e92418e5a0ef1bcf4`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
infections
```

**Current Finnish G2 candidate**
```
infektioita
```

**Blind back-translation**
```
infections
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-031

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `d00a673e4350880f79ceb91ca8b1c89ebc9421e549a5c3b10de2d3452237baa7`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
bleeding from the gullet
```

**Current Finnish G2 candidate**
```
verenvuotoa ruokatorvesta
```

**Blind back-translation**
```
bleeding from the oesophagus
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-032

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `b5543801f73cb501f54de194003f7d5fee207839b814601958e703045193e220`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Eating and drinking less; difficulty with swallowing.
```

**Current Finnish G2 candidate**
```
Syö ja juo vähemmän; nielemisvaikeuksia.
```

**Blind back-translation**
```
Eats and drinks less; difficulty swallowing.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-033

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `16b7ffb4566568735f445007a90b206e7051187169f0a14d5c2302ffb1c6fc79`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Needs to use oxygen for much of the day and night.
```

**Current Finnish G2 candidate**
```
Tarvitsee käyttää happea suuren osan päivästä ja yöstä.
```

**Blind back-translation**
```
Needs to use oxygen for a large part of the day and night.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · plain_language
Unnatural verb pair without a likely meaning change.
Proposed Finnish (review evidence only; not applied):
```
Joutuu käyttämään happea suuren osan päivästä ja yöstä.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-034

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `ee85bfdd3adc62c869acaa94fca31314a483269c0459128809a2dc1ba3199063`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Has poor control of bladder and bowels.
```

**Current Finnish G2 candidate**
```
Virtsarakon ja suolen hallinta on heikkoa.
```

**Blind back-translation**
```
Bladder and bowel control is poor.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · plain_language, terminology
Sense of incontinence is recoverable, but the wording is a literal English control metaphor.
Proposed Finnish (review evidence only; not applied):
```
Virtsan ja suolen pidätyskyky on heikko.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-035

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `03dc5cede7282aba176529d454a95cc5428d817357dbffc5dbaaaa5c9262cb81`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Has needed treatment with a breathing machine in hospital.
```

**Current Finnish G2 candidate**
```
On tarvinnut sairaalassa hoitoa hengityskoneella.
```

**Blind back-translation**
```
Has needed treatment in hospital with a ventilator.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** T-013 Project Owner: breathing machine -> hengityskone.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-036

- **Review tier:** TIER_1
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** MEDIUM
- **source_text_sha256:** `69688aa05b30b967ed5ed973c91cae039d2ff3f7130f894e0184addb81c60884`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Not able to communicate by speaking; not responding much to other people.
```

**Current Finnish G2 candidate**
```
Ei pysty viestimään puhumalla; ei vastaa juurikaan muihin ihmisiin.
```

**Blind back-translation**
```
Cannot communicate by speaking; responds very little to other people.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · MEDIUM · plain_language, adversarial
Second clause is fluent-looking but semantically odd Finnish; meaning is probably recoverable, still needs review.
Proposed Finnish (review evidence only; not applied):
```
Ei pysty viestimään puhumalla; ei vastaa juurikaan muille ihmisille.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-037

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `96324a612d8a141623f99119fea92e7043689d4744fe0d6bbead80d2cd8aa182`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Frequent falls; fractured femur.
```

**Current Finnish G2 candidate**
```
Toistuvia kaatumisia; reisiluun murtuma.
```

**Blind back-translation**
```
Repeated falls; fracture of the femur.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-038

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `99ecdde88af547bde3129601476f3b323e511474ef069349752fe59866e61df8`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Frequent infections; pneumonia
```

**Current Finnish G2 candidate**
```
Toistuvia infektioita; keuhkokuume
```

**Blind back-translation**
```
Repeated infections; pneumonia
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-039

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `5c3d417084d24c372a80dcc69467cc7d378715635bedd894b9bcbc3369dc071e`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Nervous system problems
```

**Current Finnish G2 candidate**
```
Hermoston ongelmat
```

**Blind back-translation**
```
Nervous system problems
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-040

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `76be1cc7c5b8be144dbd59555fa0b57a080e2e7bcbeedb0845e61c69a1fb0c0a`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Other conditions
```

**Current Finnish G2 candidate**
```
Muut terveydentilat
```

**Blind back-translation**
```
Other health conditions
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · omission_addition, terminology
Minor broadening/explicitness, not a likely mis-grouping of the section.
Proposed Finnish (review evidence only; not applied):
```
Muut sairaudet tai tilat
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-041

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `c0da68998a98e8a4b62feac9d288b1324608a923e07936e501368f525b478fa9`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Physical and mental health are getting worse.
```

**Current Finnish G2 candidate**
```
Fyysinen terveys ja mielenterveys heikkenevät.
```

**Blind back-translation**
```
Physical health and mental health are deteriorating.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-042

> EXISTING HUMAN DECISION CONFLICT: present both the earlier human decision and the critic evidence. Do not overwrite or automatically retain the old decision.

- **Review tier:** TIER_1
- **Finding status:** CORROBORATED
- **Combined review priority:** MEDIUM
- **source_text_sha256:** `d19219bbd6660dba90264b527df0573d44b9374e279181ff43baa7592d8d1169`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
People who are less well with other life shortening physical or mental illnesses or health conditions. There is no treatment available or it will not work well.
```

**Current Finnish G2 candidate**
```
Ihmiset, joiden terveydentila on heikentynyt ja joilla on muita elinikää lyhentäviä fyysisiä sairauksia, mielenterveyden sairauksia tai terveydentiloja. Hoitoa ei ole saatavilla tai se ei tehoa hyvin.
```

**Blind back-translation**
```
People whose health has deteriorated and who have other life-shortening physical illnesses, mental illnesses, or health conditions. Treatment is not available or does not work well.
```

**Critic A:** ISSUE · MEDIUM · changed time or frequency, meaning narrowed
The Finnish may narrow the source by requiring or implying an identifiable decline rather than simply a poorer current state.
Proposed Finnish (review evidence only; not applied):
```
Ihmiset, jotka voivat huonommin ja joilla on muita elinikää lyhentäviä fyysisiä sairauksia, mielenterveyden sairauksia tai terveydentiloja. Hoitoa ei ole saatavilla tai se ei tehoa hyvin.
```

**Critic B:** ISSUE · LOW · time_degree, terminology, plain_language
Availability/ineffectiveness contrast is kept; less well and work well are slightly recast. Same less-well pattern as 001.
Proposed Finnish (review evidence only; not applied):
```
Ihmiset, jotka voivat huonommin ja joilla on muita elinikää lyhentäviä fyysisiä sairauksia, mielenterveyden sairauksia tai terveydentiloja. Hoitoa ei ole saatavilla tai se ei toimi hyvin.
```

**Existing human decision:** Project Owner: less well -> terveydentila on heikentynyt. T-002: elinikää lyhentävät terveydentilat. Critics raised source-fidelity (current poorer state versus recorded deterioration). EXISTING_HUMAN_DECISION_REQUIRES_RECONSIDERATION_AT_G5. Do not auto-retain or overwrite.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-043

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `9fe2e73f548c64d0fd73941103a61bd789543c15a871c027617567cea69c7dbe`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
More problems with speaking and communicating; swallowing is getting worse.
```

**Current Finnish G2 candidate**
```
Enemmän ongelmia puhumisessa ja viestimisessä; nieleminen vaikeutuu.
```

**Blind back-translation**
```
More problems with speaking and communicating; swallowing becomes more difficult.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · time_degree
Speaking/communicating is faithful; swallowing worsening is slightly narrowed to difficulty.
Proposed Finnish (review evidence only; not applied):
```
Enemmän ongelmia puhumisessa ja viestimisessä; nieleminen heikkenee.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-044

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `3de4716eb33b41c98155657b801a05859fefe5fda817a3744076e38e39ab74d5`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
What we can do to help this person and their family.
```

**Current Finnish G2 candidate**
```
Mitä voimme tehdä tämän henkilön ja hänen perheensä auttamiseksi.
```

**Blind back-translation**
```
What can we do to help this person and their family.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-045

> PRIORITY HIGHLIGHT: Critic A BLOCKER and Critic B HIGH. Literal Finnish rendering of 'chest infections'.

- **Review tier:** TIER_1
- **Finding status:** CORROBORATED
- **Combined review priority:** BLOCKER
- **source_text_sha256:** `e6f4042ff1dd7f0560ebe0676573b533335874aa799c08b7701a94b72bcbf75d`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Chest infections or pneumonia; breathing problems.
```

**Current Finnish G2 candidate**
```
Rintakehän infektioita tai keuhkokuume; hengitysongelmia.
```

**Blind back-translation**
```
Chest infections or pneumonia; breathing problems.
```

**Critic A:** ISSUE · BLOCKER · changed referent, clinical concept changed
This is a clear semantic mistranslation of an English idiom at a health criterion. The Finnish should not be accepted without correction and human review.
Proposed Finnish (review evidence only; not applied):
```
Alempien hengitysteiden infektioita tai keuhkokuume; hengitysongelmia.
```

**Critic B:** ISSUE · HIGH · plain_language, terminology, adversarial
Literal chest calque with a clinically plausible wrong referent. Back-translation conceals it. Probable material error.
Proposed Finnish (review evidence only; not applied):
```
Keuhkoinfektioita tai keuhkokuume; hengitysongelmia.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** yes. Chest infections versus rintakehän infektiot raises a clinical referent question (respiratory/lung infection versus chest wall).
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-046

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `fc1e70c2a5d6055d43bd6e968d068c53e30374d1c0f46ff989b1d85d18584bd6`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Start talking with the person and their family or carer about help needed now and why making plans is important in case things change.
```

**Current Finnish G2 candidate**
```
Aloita keskustelu henkilön ja hänen perheensä tai hänestä huolehtivan ihmisen kanssa siitä, mitä apua tarvitaan nyt ja miksi suunnitelmien tekeminen on tärkeää siltä varalta, että asiat muuttuvat.
```

**Blind back-translation**
```
Start a discussion with the person and their family or the person who cares for them about what help is needed now and why making plans is important in case things change.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-047

- **Review tier:** TIER_2
- **Finding status:** CRITIC_B_ONLY
- **Combined review priority:** LOW
- **source_text_sha256:** `f3cb22010d9566918b33bf98f2e3bbd44976fe1c2a638f3d561a2c8cb3c36d37`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Ongoing disability with increasing physical and/or mental health problems after one or more strokes.
```

**Current Finnish G2 candidate**
```
Jatkuva toimintarajoite, johon liittyy lisääntyviä fyysisen terveyden ja/tai mielenterveyden ongelmia yhden tai useamman aivohalvauksen jälkeen.
```

**Blind back-translation**
```
Ongoing functional limitation with increasing physical health and/or mental health problems after one or more strokes.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** ISSUE · LOW · plain_language, terminology
Meaning of post-stroke ongoing disability is kept; the heading word is bureaucratic rather than plain.
Proposed Finnish (review evidence only; not applied):
```
Jatkuva toimintakyvyn rajoite, johon liittyy lisääntyviä fyysisen terveyden ja/tai mielenterveyden ongelmia yhden tai useamman aivohalvauksen jälkeen.
```

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-048

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `88456f1d645cbb8c2b727c914d1aea3db6974b82608a1d99c43f68ac4868bff8`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Ask for help and advice from a nurse, doctor, social worker or other staff if the person or family needs a review of their care and support.
```

**Current Finnish G2 candidate**
```
Pyydä apua ja neuvoa sairaanhoitajalta, lääkäriltä, sosiaalityöntekijältä tai muulta henkilökunnalta, jos henkilö tai perhe tarvitsee hoitonsa ja tukensa tarkastelua.
```

**Blind back-translation**
```
Ask for help and advice from a nurse, doctor, social worker, or other staff if the person or family needs their care and support to be reviewed.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-049

- **Review tier:** TIER_1
- **Finding status:** CORROBORATED
- **Combined review priority:** MEDIUM
- **source_text_sha256:** `bbf8762a42a6a44aacc9121173ad6e4c5578384ec72e3f25ebee38e11f6be4f3`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
We look at the person’s medicines and other treatments to give the best care. Holistic care includes symptoms, emotional, social, functional, financial, spiritual, cultural problems.
```

**Current Finnish G2 candidate**
```
Tarkastelemme henkilön lääkkeitä ja muita hoitoja, jotta voimme antaa parasta hoitoa. Kokonaisvaltainen hoito kattaa oireet sekä tunne-elämään, sosiaaliseen elämään, toimintakykyyn, talouteen, henkisiin ja hengellisiin kysymyksiin sekä kulttuuriin liittyvät ongelmat.
```

**Blind back-translation**
```
We review the person's medicines and other treatments so that we can provide the best care. Holistic care covers symptoms as well as problems related to emotional life, social life, functioning, finances, mental and spiritual issues, and culture.
```

**Critic A:** ISSUE · LOW · addition, meaning broadened
The added semantic branch is probably low impact, but it is not strictly source-equivalent and deserves terminology review if 'spiritual' has a defined project translation.
Proposed Finnish (review evidence only; not applied):
```
Tarkastelemme henkilön lääkkeitä ja muita hoitoja, jotta voimme antaa parasta hoitoa. Kokonaisvaltainen hoito kattaa oireet sekä tunne-elämään, sosiaaliseen elämään, toimintakykyyn, talouteen, hengellisyyteen ja kulttuuriin liittyvät ongelmat.
```

**Critic B:** ISSUE · MEDIUM · omission_addition, terminology, plain_language, adversarial
Holistic list is mostly complete, but henkinen adds a mental/existential domain and overlaps emotional. Needs human terminology review.
Proposed Finnish (review evidence only; not applied):
```
Katsomme henkilön lääkkeitä ja muita hoitoja, jotta voimme antaa parasta hoitoa. Kokonaisvaltainen hoito kattaa oireet sekä tunne-elämään, sosiaaliseen elämään, toimintakykyyn, talouteen, hengellisyyteen ja kulttuuriin liittyvät ongelmat.
```

**Existing human decision:** T-016 Sami / domain expert: holistic care -> kokonaisvaltainen hoito. This records the holistic-care term only; it does not decide the spiritual/henkinen question.
**Domain expert review recommended:** yes. Spiritual versus henkinen/hengellinen is a healthcare-domain referent question. T-016 records holistic care wording only.
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-050

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `ea006ba91f098733a23dacdda2893c980aabebc7414528de20a2ec009d628520`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Ask for specialist help if symptoms or problems are difficult to manage.
```

**Current Finnish G2 candidate**
```
Pyydä asiantuntija-apua, jos oireita tai ongelmia on vaikea hallita.
```

**Blind back-translation**
```
Ask for specialist help if symptoms or problems are difficult to manage.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-051

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `886e103145f4e3545e3196a255762f45c8e5724745af06ba5f39463b40df39fb`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
Care plans are shared with staff who need to see them and kept up to date.
```

**Current Finnish G2 candidate**
```
Hoitosuunnitelmat jaetaan henkilökunnalle, jonka tarvitsee nähdä ne, ja ne pidetään ajan tasalla.
```

**Blind back-translation**
```
Care plans are shared with staff who need to see them, and they are kept up to date.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-2026-052

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `0a78ae33f3c606ddb9e6a0403586e89ada590f7dd48254a2fe854b48bff589be`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
SPICT – 4ALL 2026
```

**Current Finnish G2 candidate**
```
SPICT – 4ALL 2026
```

**Blind back-translation**
```
SPICT – 4ALL 2026
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** CANONICAL
**Publication-blocking:** no

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

## S4A-REQ-2026-001

> SOURCE AUTHORITY — SEPARATE TRACK. Publication-blocking. Not insertable. Finnish wording review does not resolve authority.

- **Review tier:** TIER_3
- **Finding status:** NO_CRITIC_ISSUE
- **Combined review priority:** NONE
- **source_text_sha256:** `1b64512313b1820b42bf0692274c18740b11a2c395750605cfda023afcc7bc93`
- **Preparation model/run:** Cursor Grok 4.6 / G5-20260908-001

**Exact English source**
```
A liver transplant is not possible.
```

**Current Finnish G2 candidate**
```
Maksansiirto ei ole mahdollinen.
```

**Blind back-translation**
```
Liver transplantation is not possible.
```

**Critic A:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Critic B:** no issue recorded (OK / NONE). Absence of a critic finding is not acceptance.

**Existing human decision:** None recorded for this unit.
**Domain expert review recommended:** no
**Source-authority status:** NONCANONICAL
**Publication-blocking:** yes
Remains NONCANONICAL. Canonical omission remains unresolved. Publication-blocking. Critic findings do not resolve this. Separate from critic severity.
The translation reviewer may review Finnish wording but must not resolve the source-authority question.

HUMAN DECISION (human adjudicator only; leave blank in this package)

[ ] ACCEPT_CURRENT
[ ] ACCEPT_WITH_EDIT
[ ] REJECT_AND_REWRITE
[ ] ESCALATE_DOMAIN_EXPERT
[ ] DEFER_SOURCE_AUTHORITY

Final Finnish wording:
Reviewer:
Reviewer role:
Decision rationale:
Decision date:

