# Methodology

The official SPICT translation guidance supplied for this project states that first translations should use an evidence-based translation/cross-cultural adaptation approach, begin with a small group with palliative-care experience, receive wider peer review, be tried in clinical settings, and keep a clear record of the process. It points to WHO translation/adaptation guidance, Beaton et al., and the TRAPD team translation model.

This repository implements those principles as an AI-assisted evidence workflow, not as an AI-only replacement for human review.

## AI-assisted adaptation of the process
1. Lock official files, canonical source units, and provenance-linked official source requirements.
2. Agent A and Agent B independently translate every required evidence source EN->FI, including unresolved requirements that require translation evidence.
3. Agent C compares source+A+B and creates a synthesis with explicit disagreements.
4. A blind model back-translates FI->EN without seeing the source.
5. Critic agents check semantic/clinical drift, omissions, additions, terminology and plain-language quality.
6. Small human expert group adjudicates every unit; machine agreement does not equal approval.
7. Target users/staff test wording in practice as appropriate.
8. Final wording and external review status are recorded.

## Source authority and translation evidence
The manifest-verified canonical template determines canonical document text and
layout. Source-unit data is accepted as canonical evidence only after an exact
text-and-location match or an enumerated, deterministic layout-whitespace
normalization of visible text in that DOCX. A schema-validated exception records
the exact Word part, location, pre-normalization text and hash, normalization
method, normalized text, unit text, and source hashes. An exception cannot create
text absent from the DOCX. An official change specification can independently
establish that an explicit change requirement exists even when the canonical
template omits it. The requirement is therefore preserved and may undergo the
complete translation evidence workflow without being promoted into the canonical
unit namespace.

Translation evidence answers how a source would be translated. It does not answer whether that source belongs in the final publication. Inclusion or exclusion requires an explicit human/source-authority disposition. Until then, the conflict remains visible, final source reconciliation is incomplete, and a publication-blocking requirement prevents publication.

The evidence-source contract is immutable and typed. It records source kind,
exact text and hash, provenance, translation and human-review requirements, final
inclusion state, and explicit document-insertion eligibility. Directly resolved
and normalization-resolved units are proven against canonical text.
`S4A-2026-000` resolves through declared line-break normalization while its
existing authority state remains unresolved and non-insertable. An
unresolved official requirement is also not insertable; only an explicit
authority disposition can change either authority state.

## Terminology evidence precedence and isolation
1. Exact SPICT English source text and official change requirements define what
   must be translated and have absolute source authority.
2. Official Finnish healthcare and palliative-care references with verified
   provenance provide terminology evidence.
3. Other high-quality Finnish health and social-care references provide
   supporting terminology/context evidence.
4. AI suggestions are candidates only.
5. Explicit human project decisions may create approved project terminology.

Finnish terminology evidence can guide wording but cannot override, narrow, or
expand English SPICT meaning. Conflicts are recorded for human decision rather
than silently resolved. Agent A and Agent B may receive the same explicitly
`APPROVED` project glossary. They must not receive each other's translations,
synthesis output, or critic conclusions from the other forward run. Unapproved
terminology discoveries are available to terminology reviewers, not injected as
mandatory forward-translation wording.

## Why this is stronger than a single-model translation
The workflow deliberately separates generation, comparison, blind back-translation, critique and approval. Independent artifacts make errors easier to detect and make the process reproducible.

## What AI cannot establish by itself
- clinical validity
- psychometric validity
- cultural acceptability in real Finnish users
- legal or organisational approval
- external SPICT programme approval

Those require human/evidence steps and must be documented separately.

## Official methodology links
- SPICT translations: https://www.spict.org.uk/translations/
- WHO process of translation/adaptation of instruments: http://www.who.int/substance_abuse/research_tools/translation/en/
- Beaton DE et al., Guidelines for the process of cross-cultural adaptation of self-report measures: https://pubmed.ncbi.nlm.nih.gov/11124735/
- TRAPD / Cross-Cultural Survey Guidelines: http://ccsg.isr.umich.edu/index.php/chapters/translation-chapter/translation-overview
