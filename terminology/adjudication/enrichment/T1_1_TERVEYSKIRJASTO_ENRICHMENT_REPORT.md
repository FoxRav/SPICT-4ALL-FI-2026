# T1.1 Terveyskirjasto enrichment

Evidence collection only; no terminology approval or SPICT translation.

## Before and after

| Measure | Result |
| --- | --- |
| concepts_searched | 29 |
| search_attempts | 49 |
| unique_search_results_screened | 79 |
| unique_pages_scraped | 28 |
| useful_evidence_records | 28 |
| concepts_enriched | 23 |
| no_sufficient_evidence_before | 16 |
| no_sufficient_evidence_after | 11 |
| still_insufficient_ids | ['T-003', 'T-007', 'T-009', 'T-011', 'T-015', 'T-018', 'T-019', 'T-024', 'T-026', 'T-027', 'T-029'] |
| original_no_evidence_now_with_zero_useful_evidence | 3 |
| high_risk_enriched | 18 |
| must_review_with_sami | 21 |
| external_human_review_required | 29 |
| new_scope_conflicts | 7 |
| original_conflicts_resolved | 0 |
| approved | 0 |

Baseline: 29 concepts, 21 HIGH, 8 MEDIUM, 0 LOW; 16 with NO_RELIABLE_TERMINOLOGY_EVIDENCE; APPROVED 0.

The primary before/after metric is conservative: partial/contextual evidence does not remove a concept from the 16 originally insufficient concepts. CORE_TERM_SUPPORTED means head-concept evidence is available for review, not that the whole SPICT sentence or Finnish choice is approved. All useful additions improve evidence availability; only five concepts improve the conservative sufficiency category.

Search results are title/URL discovery only. No search snippet is quoted as source evidence. All 29 concepts received successful targeted searches, including successful no-result queries. Failed attempts and retries are retained. No whole-site crawl was performed.

Initial dictionary scrapes omitted article bodies. Targeted delayed scrapes recovered bodies; where a selected exact fragment still matches only source-provided metadata.description, that limitation is explicit in its locator. No full articles are copied into this package. Raw Firecrawl responses remain in ignored .firecrawl, with hashes and scrape IDs in receipts; independent fresh clones can inspect the retained short quotes and re-fetch URLs, but do not contain the raw caches.

TERM-SRC-006 is registered in web_source_manifest.json as an additive WEB_TERMINOLOGY_REFERENCE. The frozen original source registry retains five file sources. Supplementary Terveyskirjasto articles are contextual evidence and are not mislabelled dictionary definitions.

## Liver transplant distinction

| Search term | What was actually obtained | Remaining decision |
| --- | --- | --- |
| maksansiirto | Maksakirroosi article uses Maksansiirto as a treatment. | Procedure context; no final SPICT choice. |
| maksasiirre | Orphanet article uses maksasiirre alongside munuaissiirre. | Material/organ usage; not proof of procedure equivalence. |
| elinsiirto | Elinsiirrot ja suun terveys uses the broader term. | Organ-level generality does not specify liver. |
| siirre | Dictionary defines a transferred organ/tissue. | Distinguish material from procedure. |
| transplantaatio | Dictionary describes transfer of organ/tissue by surgery. | General procedure term; not automatically preferred plain Finnish. |

These distinctions are model interpretations of the linked Finnish fragments. No source-provided English pairing is claimed. The exact SPICT requirement “A liver transplant is not possible.” remains unresolved under S4A-REQ-2026-001; this web source cannot satisfy its authority requirement. The normalized title authority issue also remains unchanged.

## Conflicts and external review

Seven new scope tensions are recorded in model_interpretations.json (not seven proven source contradictions). All remain HUMAN_REVIEW_REQUIRED. Original six conflicts remain unchanged; the three relevant to T1 remain unresolved. Automatically resolved = 0; formally reduced = 0. Additional evidence clarifies distinctions but does not resolve human decisions.

Still insufficient among the original 16: T-003, T-007, T-009, T-011, T-015, T-018, T-019, T-024, T-026, T-027, T-029.

All 29 concepts need explicit human review. HIGH-risk items below particularly benefit from Sami’s ambulance/healthcare perspective. Other needs include Finnish plain-language review, palliative-care methodology, spiritual/cultural expertise, carer-role scope, and transplant/stroke specialist input where needed.

## MUST REVIEW WITH SAMI

| Decision | Concept | Reason / uncertainty |
| --- | --- | --- |
| T-001 | palliative care | Adjektiivin määritelmä tukee oireita lievittävää merkitystä; ei määrittele koko palliatiivista hoitoa eikä tee siitä saattohoidon synonyymiä. |
| T-002 | life shortening health conditions | Haku ei tuottanut riittävän täsmällistä käsitemääritelmää. Elinajan lyheneminen, ennuste ja yksittäinen sairaus eivät ole automaattisesti sama käsite. |
| T-003 | carer | Omaishoitaja esiintyy sopimuksen ja palvelusuunnitelman yhteydessä. SPICT carer voi tarkoittaa laajempaa läheisen auttajan roolia; sopimusta ei saa lisätä edellytykseksi. |
| T-005 | reduce, stop or not have treatment / stopping or not starting dialysis | DNAR on rajattu elvytystä koskeva päätös eikä tarkoita kaiken hoidon lopettamista. Vähentäminen, lopettaminen ja aloittamatta jättäminen sekä henkilön valinnat on säilytettävä erillisinä. |
| T-006 | kidney dialysis | Dialyysi määritellään myös munuaisten vajaatoiminnan hoitona. Hemodialyysi on vertailuun tarkoitettu alalaji; sitä ei saa valita koko dialyysin vastineeksi. |
| T-008 | dementia | Sanasto määrittelee dementian oireyhtymiksi. Lähteen vaihtoehtoinen ilmaus tylsistyminen ei ole suositus selkokieliseksi vastineeksi; ei pidä samastaa kaikkeen muistisairauteen. |
| T-009 | frailty | Hauraus-raihnausoireyhtymä/gerastenia määritellään vanhuuteen liittyväksi. SPICT frailty-käsitteen laajuus ja ymmärrettävyys vaativat asiantuntijapäätöksen; ikärajausta ei saa lisätä. |
| T-010 | heart failure | Sydämen vajaatoiminta on lähteen hakusana. Vaikeusaste ja lähdelauseen ehdot on arvioitava erikseen; sydäninsuffisienssi on tekninen vertailutermi. |
| T-011 | liver transplant | Maksansiirto esiintyy hoitotoimenpiteenä, maksasiirre siirrettävänä elimenä; siirre ja transplantaatio määritellään erikseen. Elinsiirto on yleisempi. Lopullista suomenkielistä valintaa ei tehdä. S4A-REQ-2026-001 jää ratkaisemattomaksi SPICT-lähdevaatimukseksi. |
| T-012 | short of breath / respiratory problems | Hengenahdistus on subjektiivinen oire; respiratory problems on laajempi. Rasitusta, vaikeutta ja syy-yhteyksiä ei saa päätellä sanastosta. |
| T-013 | breathing machine | Respiraattori määritellään hengitystä tehostavaksi laitteeksi. Laitetyyppi ja maallikon ymmärtämä hengityskone/hengityslaite vaativat ihmisen valinnan; invasiivisuutta ei saa olettaa. |
| T-014 | symptoms / treatment to help with symptoms | Hoidon määritelmä sisältää oireiden lievittämisen; katkelma ei kata kaikkia SPICT-oireita eikä ole valmis lausekäännös. |
| T-015 | no treatment available / treatment will not work well | Hoitovaste kuvaa saavutettua muutosta. Hoidon puuttuminen, heikko teho ja tehoton hoito eivät ole keskenään sama asia; lähdelauseiden erot säilytettävä. |
| T-020 | urgent or emergency hospital admissions or visits | Tarkkailuosasto on sairaalan osasto. Katkelma ei määrittele kiireellisyyttä, päivystyskäyntiä tai sairaalaan ottamista kokonaisuutena; nämä erot jäävät ensihoidon ammattilaisen tarkistettaviksi. |
| T-021 | specialist help | Konsultaatio koskee neuvon kysymistä; specialist help voi sisältää muitakin tukimuotoja. Lähteen termi ei yksin ratkaise erikoisalan avun laajuutta. |
| T-024 | nurse, doctor, social worker or other staff | Haku ei tuottanut riittäviä ammattinimikkeiden määritelmiä. Eri henkilöstöryhmät ja other staff -vaihtoehto on säilytettävä; tehtävänimikepäätös vaatii ihmisen. |
| T-025 | surgery is not possible | Inoperaabeli-haku ei palauttanut tuloksia. Teknistä diagnoosiluonteista termiä ei lisätä lähteen surgery is not possible -ilmaukseen. |
| T-026 | medicines and other treatments | Hoidon määritelmä mainitsee lääkityksen ja muita toimia. Tämä on osittainen tuki, ei lääke-käsitteen määritelmä eikä peruste häivyttää medicines and other treatments -erottelua. |
| T-027 | one or more strokes | Aivohalvauksen sanastomääritelmä painottaa halvausoiretta; stroke voi esiintyä myös ilman tätä. Tarvitaan kliininen laajuustarkistus. One or more -määrää ei saa kadottaa. |
| T-028 | difficulty with swallowing | Dysfagian määritelmä on nielemishäiriö. Maallikkokielinen vaikeuden kuvaus ja syömisen/juomisen konteksti jäävät valittaviksi; teknistä termiä ei automaattisesti siirretä SPICTiin. |
| T-029 | being confused at times | Sekavuustila on määritelty tajunnan/orientaation häiriöksi. Being confused at times ei itsessään todista delirium-diagnoosia; ajallinen vaihtelu säilytettävä. |

This is a proposed review agenda, not a claim that Sami has reviewed or approved anything. All human fields remain blank.

## Validation and reproducibility

Run scripts/validate_t1_1_enrichment.py and the full existing test/validation suite. Actual command outputs are recorded separately in T1_1_VALIDATION_RESULTS.json after execution. The validator checks the protected original artifacts, exact TSV cells, all decision links, source/model separation, short fragments and cache hashes when caches are available, authority classification, and absence of new translation work.

No commit or push is performed. Original T1 artifacts remain separate and unchanged.
