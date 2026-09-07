# Methodology

The official SPICT translation guidance supplied for this project states that first translations should use an evidence-based translation/cross-cultural adaptation approach, begin with a small group with palliative-care experience, receive wider peer review, be tried in clinical settings, and keep a clear record of the process. It points to WHO translation/adaptation guidance, Beaton et al., and the TRAPD team translation model.

This repository implements those principles as an AI-assisted evidence workflow, not as an AI-only replacement for human review.

## AI-assisted adaptation of the process
1. Lock canonical source and hashes.
2. Agent A and Agent B independently translate every unit EN->FI.
3. Agent C compares source+A+B and creates a synthesis with explicit disagreements.
4. A blind model back-translates FI->EN without seeing the source.
5. Critic agents check semantic/clinical drift, omissions, additions, terminology and plain-language quality.
6. Small human expert group adjudicates every unit; machine agreement does not equal approval.
7. Target users/staff test wording in practice as appropriate.
8. Final wording and external review status are recorded.

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
