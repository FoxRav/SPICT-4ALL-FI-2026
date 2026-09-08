"""Build additive evidence artifacts from reviewed, git-ignored Firecrawl receipts.

The TSV is authored separately by build_t1_1_tables.mjs using this payload.
Existing differing artifacts are never overwritten.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from spict4all.adjudication import BASE, read_json, read_tsv
from spict4all.terminology_enrichment import (
    ENRICHMENT,
    EVIDENCE,
    QUEUE,
    build_table,
    counts,
    human_review,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ENRICHMENT


def save(name, content):
    path = OUT / name
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"Refusing to overwrite differing artifact: {name}")
    else:
        path.write_text(content, encoding="utf-8")


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def lines(value):
    return "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in value)


# This table is MODEL interpretation; quoted strings must match an actual response.
# Core support is evidence for the head concept, never approval of SPICT wording.
NOTES = {
1: "Adjektiivin määritelmä tukee oireita lievittävää merkitystä; ei määrittele koko palliatiivista hoitoa eikä tee siitä saattohoidon synonyymiä.",
2: "Haku ei tuottanut riittävän täsmällistä käsitemääritelmää. Elinajan lyheneminen, ennuste ja yksittäinen sairaus eivät ole automaattisesti sama käsite.",
3: "Omaishoitaja esiintyy sopimuksen ja palvelusuunnitelman yhteydessä. SPICT carer voi tarkoittaa laajempaa läheisen auttajan roolia; sopimusta ei saa lisätä edellytykseksi.",
4: "Hoito- ja palvelusuunnitelma on kontekstuaalinen esimerkki. SPICT care plans ei rajaudu omaishoitoon eikä ole automaattisesti hoitotahto.",
5: "DNAR on rajattu elvytystä koskeva päätös eikä tarkoita kaiken hoidon lopettamista. Vähentäminen, lopettaminen ja aloittamatta jättäminen sekä henkilön valinnat on säilytettävä erillisinä.",
6: "Dialyysi määritellään myös munuaisten vajaatoiminnan hoitona. Hemodialyysi on vertailuun tarkoitettu alalaji; sitä ei saa valita koko dialyysin vastineeksi.",
7: "Elämänlaatu esiintyy terveyskäsitteen yhteydessä, mutta katkelma ei määrittele sitä kattavasti eikä anna englanninkielistä termiparia.",
8: "Sanasto määrittelee dementian oireyhtymiksi. Lähteen vaihtoehtoinen ilmaus tylsistyminen ei ole suositus selkokieliseksi vastineeksi; ei pidä samastaa kaikkeen muistisairauteen.",
9: "Hauraus-raihnausoireyhtymä/gerastenia määritellään vanhuuteen liittyväksi. SPICT frailty-käsitteen laajuus ja ymmärrettävyys vaativat asiantuntijapäätöksen; ikärajausta ei saa lisätä.",
10: "Sydämen vajaatoiminta on lähteen hakusana. Vaikeusaste ja lähdelauseen ehdot on arvioitava erikseen; sydäninsuffisienssi on tekninen vertailutermi.",
11: "Maksansiirto esiintyy hoitotoimenpiteenä, maksasiirre siirrettävänä elimenä; siirre ja transplantaatio määritellään erikseen. Elinsiirto on yleisempi. Lopullista suomenkielistä valintaa ei tehdä. S4A-REQ-2026-001 jää ratkaisemattomaksi SPICT-lähdevaatimukseksi.",
12: "Hengenahdistus on subjektiivinen oire; respiratory problems on laajempi. Rasitusta, vaikeutta ja syy-yhteyksiä ei saa päätellä sanastosta.",
13: "Respiraattori määritellään hengitystä tehostavaksi laitteeksi. Laitetyyppi ja maallikon ymmärtämä hengityskone/hengityslaite vaativat ihmisen valinnan; invasiivisuutta ei saa olettaa.",
14: "Hoidon määritelmä sisältää oireiden lievittämisen; katkelma ei kata kaikkia SPICT-oireita eikä ole valmis lausekäännös.",
15: "Hoitovaste kuvaa saavutettua muutosta. Hoidon puuttuminen, heikko teho ja tehoton hoito eivät ole keskenään sama asia; lähdelauseiden erot säilytettävä.",
16: "Holistinen-haku ei antanut käyttökelpoista hoidon käsitemääritelmää. Laaja terveyskäsitys ei yksin todista holistic care -vastaavuutta.",
17: "Kuntoutuksen määritelmä tukee omatoimisuuden kontekstia; se ei määrittele jatkuvaa toimintarajoitetta eikä korvaa lähteen toimintakykykuvausta.",
18: "Kohdennetusta hausta ei löytynyt käyttökelpoista näyttöä. Hengelliset ja eksistentiaaliset tarpeet sekä henkilön oma merkitys vaativat erillistä asiantuntemusta.",
19: "Kohdennetusta hausta ei löytynyt käyttökelpoista näyttöä. Kulttuuriin liittyviä ongelmia ei saa supistaa diagnoosiksi tai kieliongelmaksi.",
20: "Tarkkailuosasto on sairaalan osasto. Katkelma ei määrittele kiireellisyyttä, päivystyskäyntiä tai sairaalaan ottamista kokonaisuutena; nämä erot jäävät ensihoidon ammattilaisen tarkistettaviksi.",
21: "Konsultaatio koskee neuvon kysymistä; specialist help voi sisältää muitakin tukimuotoja. Lähteen termi ei yksin ratkaise erikoisalan avun laajuutta.",
22: "Potilas määritellään terveyspalvelusuhteen kautta; person ei automaattisesti rajaa henkilöä potilaaksi. Vanhoja potilas/asiakas-ristiriitoja ei ratkaista tällä määritelmällä.",
23: "Hoito kattaa useita toimia. Help and care needed ei supistu kliiniseen hoitoon tai muodolliseen palvelutarpeeseen; vanha palvelutarve-ristiriita jää avoimeksi.",
24: "Haku ei tuottanut riittäviä ammattinimikkeiden määritelmiä. Eri henkilöstöryhmät ja other staff -vaihtoehto on säilytettävä; tehtävänimikepäätös vaatii ihmisen.",
25: "Inoperaabeli-haku ei palauttanut tuloksia. Teknistä diagnoosiluonteista termiä ei lisätä lähteen surgery is not possible -ilmaukseen.",
26: "Hoidon määritelmä mainitsee lääkityksen ja muita toimia. Tämä on osittainen tuki, ei lääke-käsitteen määritelmä eikä peruste häivyttää medicines and other treatments -erottelua.",
27: "Aivohalvauksen sanastomääritelmä painottaa halvausoiretta; stroke voi esiintyä myös ilman tätä. Tarvitaan kliininen laajuustarkistus. One or more -määrää ei saa kadottaa.",
28: "Dysfagian määritelmä on nielemishäiriö. Maallikkokielinen vaikeuden kuvaus ja syömisen/juomisen konteksti jäävät valittaviksi; teknistä termiä ei automaattisesti siirretä SPICTiin.",
29: "Sekavuustila on määritelty tajunnan/orientaation häiriöksi. Being confused at times ei itsessään todista delirium-diagnoosia; ajallinen vaihtelu säilytettävä.",
}

# number, page identifier, source headword or exact usage, exact short fragment
SELECTIONS = [
(1, 'ltt04389', 'palliatiivinen', 'oireita lievittävä mutta tautia parantamaton'),
(3, 'dlk00899', 'Omaishoitaja', 'Omaishoitaja ja hyvinvointialue tekevät omaishoitosopimuksen, johon\nliittyy aina hoito- ja palvelusuunnitelma.'),
(4, 'dlk00899', 'hoito- ja palvelusuunnitelma', 'Omaishoitaja ja hyvinvointialue tekevät omaishoitosopimuksen, johon\nliittyy aina hoito- ja palvelusuunnitelma.'),
(5, 'dlk01180', 'DNAR-päätös', 'DNAR-päätös ei tarkoita hoidon lopettamista ja on hoidon rajauksista lievin'),
(6, 'ltt00543', 'dialyysi', 'kalvoerottelu; mm. munuaisten vajaatoiminnan hoitoon käytetty menetelmä'),
(6, 'ltt01085', 'hemodialyysi', 'mm. munuaisten vajaatoiminnan ja myrkytysten hoitona käytettävä menetelmä'),
(7, 'dlk00903', 'elämänlaatu', 'Toimintakyky ja elämänlaatu ovat\nkeskeisiä terveyden kokemiseen liittyviä käsitteitä.'),
(8, 'ltt00512', 'dementia', 'useista eri aivosairauksista johtuvia oireyhtymiä'),
(9, 'ltt04142', 'hauraus-raihnausoireyhtymä', 'vanhuudessa etenevä monimuotoinen fysiologinen ja neurologinen rapistuminen'),
(10, 'ltt03328', 'sydämen vajaatoiminta', 'tila jossa sydän ei pysty pumppaamaan siihen tulevaa verta riittävän nopeasti eteenpäin'),
(11, 'khp00142', 'Maksansiirto', 'Maksansiirto soveltuu hoidoksi osalle maksakirroosia sairastavista.'),
(11, 'orp01816', 'maksasiirre', 'Joskus saatetaan tarvita sekä munuais- että maksasiirre.'),
(11, 'trv00146', 'elinsiirto', 'hoitona on elinsiirto, joskin siirtoelimistä on pulaa.'),
(11, 'ltt03123', 'siirre', 'elimistön osasta toiseen tai saman tai eri lajin yksilöstä toiseen leikkauksella siirretty elin tai kudos'),
(11, 'ltt03496', 'transplantaatio', 'elimen tai kudoksen siirto leikkauksella'),
(12, 'ltt01100', 'hengenahdistus', 'epämiellyttävä tuntemus hengitysilman riittämättömyydestä'),
(13, 'ltt02920', 'respiraattori', 'hengityslaite, hengityskoje; keuhkotuuletushäiriöiden hoitoon käytetty hengitystä tehostava laite'),
(14, 'ltt04798', 'hoito', 'sairauden tai vamman parantamiseen tai oire(id)en lievittämiseen tähtäävä toiminta'),
(15, 'ltt04804', 'hoitovaste', 'hoidolla saavutettu muutos potilaan tilassa tai taudin laajuutta tai vakavuutta kuvaavassa suureessa'),
(17, 'ltt01795', 'kuntoutus', 'potilaan työkyvyn ja omatoimisuuden palauttamiseen tähtäävä toiminta'),
(20, 'ltt04533', 'tarkkailuosasto', 'sairaalan osasto, jolle potilaat otetaan diagnoosin varmistamiseksi ja hoidon tarpeen määrittämiseksi'),
(21, 'ltt04820', 'konsultaatio', 'neuvon kysyminen'),
(22, 'ltt02702', 'potilas', 'potilas on terveyden- ja sairaanhoitopalveluja käyttävä tai niiden kohteena oleva henkilö'),
(23, 'ltt04798', 'hoito', 'toimenpiteitä, lääkitystä ja neuvontaa'),
(26, 'ltt04798', 'hoito', 'toimenpiteitä, lääkitystä ja neuvontaa'),
(27, 'ltt00059', 'aivohalvaus', 'aivokudoksen verettömyydestä (iskemiasta) tai aivoverenvuodosta\naiheutunut tahdonalaisten lihasten halvaus'),
(28, 'ltt04027', 'dysfagia', 'nielemishäiriö'),
(29, 'ltt03051', 'sekavuustila', 'tajunnan häiriö, jolle on ominaista häiriintynyt orientaatio aikaan, paikkaan ja/tai henkilöön nähden'),
]


def main():
    table = read_tsv(ROOT / BASE / 'TERMINOLOGY_ADJUDICATION_QUEUE.tsv')
    baseline = {row[0]: dict(zip(table[0], row, strict=True)) for row in table[1:]}
    searches = []
    for filename in ['t1_1-search-log.json', 't1_1-search-log2.json']:
        for item in read_json(ROOT / '.firecrawl' / filename):
            result = item.get('results') or {}
            web = result.get('data', {}).get('web', [])
            searches.append({
                'decision_id': item['decision_id'], 'query': item['query'],
                'retrieval_method': 'FIRECRAWL', 'accessed_at_utc': item.get('accessed_at_utc'),
                'exit_code': item['exit_code'], 'diagnostic': item.get('diagnostic', ''),
                'results': [{'url': r['url'], 'title': r['title']} for r in web],
                'screening': 'Discovery only. Search snippets are not source evidence. Retained pages/quotes are explicitly linked in the evidence ledger; other hits were not used.',
            })
    save('search_receipts.jsonl', lines(searches))
    receipts = []
    for name in ['t1_1-scrape-log.json', 't1_1-scrape-log2.json', 't1_1-scrape-log3.json', 't1_1-scrape-log4.json']:
        receipts += read_json(ROOT / '.firecrawl' / name)
    single = ROOT / '.firecrawl/t1_1-page-ltt03123.json'
    receipts.append({'url': 'https://www.terveyskirjasto.fi/ltt03123',
                     'accessed_at_utc': datetime.fromtimestamp(single.stat().st_mtime, UTC).isoformat(),
                     'retrieval_method': 'FIRECRAWL', 'exit_code': 0, 'diagnostic': '',
                     'cache_path': single.relative_to(ROOT).as_posix(),
                     'timestamp_basis': 'local receipt file completion time'})
    root_cache = ROOT / '.firecrawl/t1_1-root.json'
    receipts.append({'url': 'https://www.terveyskirjasto.fi/sisalto/laaketieteen-sanasto/111060',
                     'accessed_at_utc': datetime.fromtimestamp(root_cache.stat().st_mtime, UTC).isoformat(),
                     'retrieval_method': 'FIRECRAWL', 'exit_code': 0, 'diagnostic': '',
                     'cache_path': root_cache.relative_to(ROOT).as_posix(),
                     'timestamp_basis': 'local receipt file completion time'})
    for receipt in receipts:
        path = ROOT / receipt['cache_path']
        if receipt['exit_code'] == 0 and path.exists():
            raw = read_json(path)
            receipt['cache_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            receipt['page_title'] = raw['metadata'].get('title')
            receipt['firecrawl_scrape_id'] = raw['metadata'].get('scrapeId')
    save('page_receipts.jsonl', lines(receipts))
    registry = {
        'source_id': 'TERM-SRC-006', 'organisation_publisher': 'Kustannus Oy Duodecim',
        'publisher_basis': 'Copyright footer in Firecrawl markdown of ltt03123',
        'site_name': 'Duodecim Terveyskirjasto', 'resource_title': 'Lääketieteen sanasto',
        'root_url': 'https://www.terveyskirjasto.fi/sisalto/laaketieteen-sanasto/111060',
        'accessed_date': receipts[-1]['accessed_at_utc'][:10],
        'classification': 'TERMINOLOGY_REFERENCE', 'evidence_type': 'WEB_TERMINOLOGY_REFERENCE',
        'retrieval_method': 'FIRECRAWL', 'provenance_status': 'SOURCE_FRAGMENTS_RETRIEVED_WITH_RECEIPTS',
        'can_satisfy_spict_source_requirements': False,
        'scope': 'Targeted dictionary pages plus explicitly labelled contextual articles on the same site. Article collection is retained in receipt metadata.',
        'registration_note': 'Additive web registry. Five frozen local T0 source records and their 136 extracted entries remain unchanged.',
    }
    save('web_source_manifest.json', dump(registry))
    evidence = []
    core = {6, 8, 10, 13, 28}
    for number, ident, headword, fragment in SELECTIONS:
        candidates = [r for r in receipts if r['exit_code'] == 0 and f'-{ident}.json' in r['cache_path']]
        selected = None
        for receipt in reversed(candidates):
            raw = read_json(ROOT / receipt['cache_path'])
            match = re.search(r'\s+'.join(re.escape(word) for word in fragment.split()), raw.get('markdown', ''))
            if match:
                fragment = match.group()  # Preserve actual returned whitespace exactly.
                selected = (receipt, raw, 'markdown article fragment')
                break
            if fragment in raw['metadata'].get('description', '') and selected is None:
                selected = (receipt, raw, 'metadata.description (source-provided excerpt; body fragment not matched)')
        if selected is None:
            raise RuntimeError(f'Exact source fragment not found: {ident}: {fragment}')
        receipt, raw, locator = selected
        metadata = raw['metadata']
        decision = f'T-{number:03}'
        coverage = 'CORE_TERM_SUPPORTED' if number in core else 'PARTIAL_OR_CONTEXTUAL'
        evidence.append({
            'evidence_id': f'TERM-EVID-WEB-006-{len(evidence)+1:03}',
            'decision_id': decision, 'concept_en': baseline[decision]['concept_en'], 'source_id': 'TERM-SRC-006',
            'source_evidence': {
                'page_title': metadata['title'], 'url': receipt['url'],
                'accessed_at_utc': receipt['accessed_at_utc'], 'headword_fi': headword,
                'fragment': fragment, 'article_id': metadata.get('duo:identifier'),
                'locator': locator, 'article_date': metadata.get('duo:updated'),
                'retrieval_method': 'FIRECRAWL',
                'retrieval_metadata': {k: metadata[k] for k in ['scrapeId', 'statusCode', 'sourceURL', 'url', 'cacheState', 'duo:database', 'ogTitle'] if k in metadata},
                'cache_path': receipt['cache_path'], 'cache_sha256': receipt['cache_sha256'],
                'fragment_sha256': hashlib.sha256(fragment.encode()).hexdigest(),
            },
            'model_interpretation': {'relationship': 'MODEL_SEMANTIC_MAPPING',
                'relevance_note': NOTES[number], 'confidence': 'MODERATE' if number in core else 'LIMITED',
                'coverage': coverage},
        })
    save(EVIDENCE, lines(evidence))
    decisions = []
    for number in range(1, 30):
        decision = f'T-{number:03}'
        refs = [x['evidence_id'] for x in evidence if x['decision_id'] == decision]
        coverage = 'CORE_TERM_SUPPORTED' if number in core else ('PARTIAL_OR_CONTEXTUAL' if refs else 'NO_USEFUL_EVIDENCE')
        previous = baseline[decision]['candidate_origin']
        after = ('NEW_CORE_TERMINOLOGY_EVIDENCE_FOR_REVIEW' if number in core else
                 'STILL_INSUFFICIENT_PARTIAL_EVIDENCE' if refs and previous == 'NO_RELIABLE_TERMINOLOGY_EVIDENCE' else
                 'EXISTING_EVIDENCE_PLUS_CONTEXT' if refs else previous)
        decisions.append({'decision_id': decision, 'evidence_ids': refs, 'coverage': coverage,
                          'after_status': after, 'uncertainty': NOTES[number],
                          'must_review_with_sami': baseline[decision]['clinical_risk'] == 'HIGH'})
    conflicts = [{'conflict_id': f'T1.1-SCOPE-{i:03}', 'decision_id': f'T-{n:03}',
                  'type': 'MODEL_IDENTIFIED_SCOPE_TENSION', 'status': 'HUMAN_REVIEW_REQUIRED',
                  'note': NOTES[n]} for i, n in enumerate([3, 5, 9, 11, 22, 27, 29], 1)]
    save('model_interpretations.json', dump({'type': 'MODEL_SEMANTIC_MAPPING', 'approved': 0,
                                           'decisions': decisions, 'new_scope_conflicts': conflicts}))
    save('TERMINOLOGY_HUMAN_REVIEW_T1_1.md', human_review(ROOT))
    c = counts(ROOT)
    report = ['# T1.1 Terveyskirjasto enrichment', '', 'Evidence collection only; no terminology approval or SPICT translation.', '',
              '## Before and after', '', '| Measure | Result |', '| --- | --- |']
    for key, value in c.items():
        report.append(f'| {key} | {value} |')
    report += ['', 'Baseline: 29 concepts, 21 HIGH, 8 MEDIUM, 0 LOW; 16 with NO_RELIABLE_TERMINOLOGY_EVIDENCE; APPROVED 0.', '',
               'The primary before/after metric is conservative: partial/contextual evidence does not remove a concept from the 16 originally insufficient concepts. CORE_TERM_SUPPORTED means head-concept evidence is available for review, not that the whole SPICT sentence or Finnish choice is approved. All useful additions improve evidence availability; only five concepts improve the conservative sufficiency category.', '',
               'Search results are title/URL discovery only. No search snippet is quoted as source evidence. All 29 concepts received successful targeted searches, including successful no-result queries. Failed attempts and retries are retained. No whole-site crawl was performed.', '',
               'Initial dictionary scrapes omitted article bodies. Targeted delayed scrapes recovered bodies; where a selected exact fragment still matches only source-provided metadata.description, that limitation is explicit in its locator. No full articles are copied into this package. Raw Firecrawl responses remain in ignored .firecrawl, with hashes and scrape IDs in receipts; independent fresh clones can inspect the retained short quotes and re-fetch URLs, but do not contain the raw caches.', '',
               'TERM-SRC-006 is registered in web_source_manifest.json as an additive WEB_TERMINOLOGY_REFERENCE. The frozen original source registry retains five file sources. Supplementary Terveyskirjasto articles are contextual evidence and are not mislabelled dictionary definitions.', '',
               '## Liver transplant distinction', '',
               '| Search term | What was actually obtained | Remaining decision |', '| --- | --- | --- |',
               '| maksansiirto | Maksakirroosi article uses Maksansiirto as a treatment. | Procedure context; no final SPICT choice. |',
               '| maksasiirre | Orphanet article uses maksasiirre alongside munuaissiirre. | Material/organ usage; not proof of procedure equivalence. |',
               '| elinsiirto | Elinsiirrot ja suun terveys uses the broader term. | Organ-level generality does not specify liver. |',
               '| siirre | Dictionary defines a transferred organ/tissue. | Distinguish material from procedure. |',
               '| transplantaatio | Dictionary describes transfer of organ/tissue by surgery. | General procedure term; not automatically preferred plain Finnish. |', '',
               'These distinctions are model interpretations of the linked Finnish fragments. No source-provided English pairing is claimed. The exact SPICT requirement “A liver transplant is not possible.” remains unresolved under S4A-REQ-2026-001; this web source cannot satisfy its authority requirement. The normalized title authority issue also remains unchanged.', '',
               '## Conflicts and external review', '',
               'Seven new scope tensions are recorded in model_interpretations.json (not seven proven source contradictions). All remain HUMAN_REVIEW_REQUIRED. Original six conflicts remain unchanged; the three relevant to T1 remain unresolved. Automatically resolved = 0; formally reduced = 0. Additional evidence clarifies distinctions but does not resolve human decisions.', '',
               'Still insufficient among the original 16: ' + ', '.join(c['still_insufficient_ids']) + '.', '',
               'All 29 concepts need explicit human review. HIGH-risk items below particularly benefit from Sami’s ambulance/healthcare perspective. Other needs include Finnish plain-language review, palliative-care methodology, spiritual/cultural expertise, carer-role scope, and transplant/stroke specialist input where needed.', '',
               '## MUST REVIEW WITH SAMI', '', '| Decision | Concept | Reason / uncertainty |', '| --- | --- | --- |']
    for row in decisions:
        if row['must_review_with_sami']:
            report.append(f"| {row['decision_id']} | {baseline[row['decision_id']]['concept_en']} | {row['uncertainty']} |")
    report += ['', 'This is a proposed review agenda, not a claim that Sami has reviewed or approved anything. All human fields remain blank.', '',
               '## Validation and reproducibility', '',
               'Run scripts/validate_t1_1_enrichment.py and the full existing test/validation suite. Actual command outputs are recorded separately in T1_1_VALIDATION_RESULTS.json after execution. The validator checks the protected original artifacts, exact TSV cells, all decision links, source/model separation, short fragments and cache hashes when caches are available, authority classification, and absence of new translation work.', '',
               'No commit or push is performed. Original T1 artifacts remain separate and unchanged.', '']
    save('T1_1_TERVEYSKIRJASTO_ENRICHMENT_REPORT.md', '\n'.join(report))
    (ROOT / '.firecrawl/t1_1-table-payload.json').write_text(dump({QUEUE: build_table(ROOT)}), encoding='utf-8')
    print(dump(c))


if __name__ == '__main__':
    main()
