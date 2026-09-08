"""T1.2 material-meaning triage, separate from human decisions and translation."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .adjudication import BASE, read_json, read_tsv, tsv_text
from .errors import IntegrityError
from .human_terminology_decisions import BINDINGS, HUMAN_FILE, historical_human_bytes
from .terminology_enrichment import ENRICHMENT, validate_enrichment

QUEUE = "T1_2_MINIMAL_SAMI_QUEUE.tsv"
REPORT = "T1_2_HUMAN_REVIEW_REDUCTION_REPORT.md"
REVIEW = "T1_2_SAMI_REVIEW.md"
# Categories are review routing only. They neither approve terms nor erase evidence gaps.
TRIAGE = {
    1: ("EVIDENCED_OR_OBVIOUS", "Palliatiivisen hoidon lähdetermi on käytettävissä; saattohoidoksi rajaaminen on vältettävä merkitysmuutos, ei avoin synonyymivalinta."),
    2: ("HUMAN_DECIDED", "Projektinomistajan täsmällinen päätös kirjataan T-002:een; kysymystä ei avata uudelleen."),
    3: ("SAMI", "Omaishoitajan muodolliseen asemaan rajaava ilmaus voi sulkea carer-roolista epävirallisesti auttavan läheisen tai muun henkilön."),
    4: ("G1_G2_SYNTHESIS", "Tavallinen hoidon suunnittelu voidaan säilyttää ilman Kanta-asiakirjan tai hoitotahdon erityismerkityksen lisäämistä."),
    5: ("G1_G2_SYNTHESIS", "Lähteen erilliset vähentämisen, lopettamisen ja aloittamatta jättämisen vaihtoehdot sekä valinnan tekijä voidaan säilyttää tavallisessa käännösvertailussa; DNAR ei ole niiden vastine."),
    6: ("EVIDENCED_OR_OBVIOUS", "Dialyysin peruskäsite on lähteistetty; hemodialyysiin supistamista ei tarvita eikä tarjota vaihtoehtoisena merkityksenä."),
    7: ("EVIDENCED_OR_OBVIOUS", "Elämänlaadun arkinen merkitys ja lähteessä havaittu käyttö riittävät sanamuototyöhön; täydellisen sanastomääritelmän puuttuminen ei ole eskalointiperuste."),
    8: ("EVIDENCED_OR_OBVIOUS", "Dementia on lähteistetty käsite; vanha vaihtoehtoinen sanamuoto tai kaikkiin muistisairauksiin laajentaminen eivät edellytä uutta kysymystä."),
    9: ("DISCUSSED_RECORDING_NEEDED", "Ihmisten aiempi keskustelu on ilmoitettu, mutta täsmällistä lopullista suomenkielistä ratkaisua ei ole nykyisessä päätöstiedossa; tarvitaan aiemman ratkaisun kirjaus, ei peruskysymyksen uusimista."),
    10: ("EVIDENCED_OR_OBVIOUS", "Sydämen vajaatoiminta on suoraan lähteistetty; vaikeusasteen ja lauseen ehtojen säilyttäminen kuuluu myöhempään käännöstarkistukseen."),
    11: ("EVIDENCED_OR_OBVIOUS", "T1.1 erottaa siirtotoimenpiteen ja siirretyn elimen; tämä näyttö riittää sanamuototyöhön, mutta ratkaisematon SPICT-lähdevaltuus säilyy erillisenä."),
    12: ("G1_G2_SYNTHESIS", "Oireen ja laajemman hengitysongelman eri lähdeilmaukset säilytetään asiayhteyksittäin; yhdistetty arviointirivi ei velvoita yhteen yleisvastineeseen."),
    13: ("HUMAN_DECIDED", "Projektinomistajan hengityskone-päätös kirjataan T-013:een; laitevaihtoehtoja ei kysytä uudelleen."),
    14: ("STYLISTIC_OR_EQUIVALENT", "Oireiden helpottamista kuvaavien luontevien ilmausten vaihtelu on sanamuototyötä; tässä ei ole avoinna erillistä kliinistä käsitettä."),
    15: ("G1_G2_SYNTHESIS", "Hoidon puuttuminen ja odotettu heikko teho ovat lähteessä eri vaihtoehdot, jotka voi säilyttää ilman lääketieteellisen hyödyttömyyden lisätulkintaa."),
    16: ("HUMAN_DECIDED", "Samin / asiantuntijan kokonaisvaltainen hoito -päätös kirjataan T-016:een; sitä ei kysytä uudelleen."),
    17: ("G1_G2_SYNTHESIS", "Toimintakykyä kuvaavat kontekstit erotetaan synteesissä; ilmoitettu usual activities -päätös ei hyväksy koko functional problems / ongoing disability -ryhmää."),
    18: ("SAMI", "Spiritual problems -ilmauksen rajaaminen uskonnollisiin kysymyksiin voi jättää elämän merkitykseen ja vakaumukseen liittyvän tuen arvioinnin ulkopuolelle."),
    19: ("STYLISTIC_OR_EQUIVALENT", "Kulttuuriin liittyvän merkityksen säilyttävät tavalliset parafraasit kuuluvat kielityöhön; nykyinen näyttö ei osoita konkreettista kilpailevaa kliinistä käsitettä."),
    20: ("G1_G2_SYNTHESIS", "Kiireellisyys, sairaalaan ottaminen ja käynti ovat lähteessä näkyviä eroja; niitä ei tarvitse korvata suomalaisen palvelujärjestelmän tarkkailuosasto-luokalla."),
    21: ("G1_G2_SYNTHESIS", "Lähteen asiantuntija-avun voi säilyttää yleisenä tukena lisäämättä erikoislääkärivaatimusta tai muodollista läheteprosessia."),
    22: ("G1_G2_SYNTHESIS", "Lähteen henkilöviittaus voidaan säilyttää ilman potilas- tai asiakasaseman lisäämistä; näiden lähdetermien ristiriidat jäävät lokiin."),
    23: ("G1_G2_SYNTHESIS", "Avun ja hoidon tarve voidaan säilyttää ilman muodolliseen palvelutarpeen arviointiin supistamista; palvelutarve-ristiriidan ratkaiseminen ei ole tämän edellytys."),
    24: ("EVIDENCED_OR_OBVIOUS", "Tavalliset ammattinimikkeet ja muu henkilöstö eivät tarvitse domain-päätöstä vain siksi, ettei niille löytynyt erillistä sanastohakua."),
    25: ("EVIDENCED_OR_OBVIOUS", "Leikkauksen mahdottomuus voidaan ilmaista lähteen tasolla ottamatta kantaa anatomiseen syyhyn tai ottamalla käyttöön teknistä luokitusta."),
    26: ("EVIDENCED_OR_OBVIOUS", "Lääkkeiden ja muiden hoitojen ero on tavallista, ymmärrettävää sanastoa; kattavan määritelmän puute ei tee siitä kliinistä kysymystä."),
    27: ("SAMI", "Stroke-vastine voi rajata pois verenvuotoperäisiä tapahtumia tai laajentaa mukaan ohimeneviä tapahtumia, kun taas nykyinen sanastokatkelma painottaa halvausoiretta."),
    28: ("STYLISTIC_OR_EQUIVALENT", "Nielemisen vaikeuden luonnolliset kuvaukset säilyttävät saman merkityksen; dysfagia-termiä ei tarvitse nostaa maallikkotekstiin."),
    29: ("STYLISTIC_OR_EQUIVALENT", "Ajoittaisen sekavuuden tavalliset kuvaukset ovat sanamuotovalintoja; delirium-diagnoosin lisääminen olisi vältettävä lisäys eikä ratkaistava vaihtoehto."),
}
QUESTIONS = {
    3: "Millainen suomalainen roolin kuvaus kattaa myös epävirallisen auttajan ilman muodollisen omaishoitajuuden tai ammattihenkilön aseman vaatimusta?",
    18: "Miten tämän hoidon osa-alueen laajuus säilytetään suomeksi niin, ettei se rajaudu vain uskonnollisiin kysymyksiin tai sekoitu lähteen erikseen mainitsemiin tunne-elämän ongelmiin?",
    27: "Mikä suomalainen kliininen käsite säilyttää stroke-tapahtuman laajuuden ilman rajautumista vain infarktiin tai halvausoireeseen ja ilman laajenemista ohimeneviin tapahtumiin?",
}
UNBOUND = [
    {"concept_en": "less well", "finnish": "terveydentila on heikentynyt", "decision_maker": "Project Owner", "source_unit_ids": ["S4A-2026-001", "S4A-2026-042"]},
    {"concept_en": "less able to manage usual activities", "finnish": "toimintakyky on heikentynyt", "decision_maker": "Project Owner", "source_unit_ids": ["S4A-2026-004", "S4A-2026-014"]},
    {"concept_en": "not well enough for cancer treatment", "finnish": "ei ole riittävän hyväkuntoinen syöpähoitoon", "decision_maker": "Project Owner", "source_unit_ids": ["S4A-2026-017"]},
]


def assessment(root: Path) -> dict[str, Any]:
    table = read_tsv(root / ENRICHMENT / "T1_1_UPDATED_ADJUDICATION_QUEUE.tsv")
    old = {r["decision_id"]: r for r in read_json(root / ENRICHMENT / "model_interpretations.json")["decisions"]}
    rows = []
    for values in table[1:]:
        r = dict(zip(table[0], values, strict=True))
        n = int(r["decision_id"].split("-")[1])
        category, reason = TRIAGE[n]
        rows.append({"decision_id": r["decision_id"], "concept_en": r["concept_en"],
                     "previous_sami": old[r["decision_id"]]["must_review_with_sami"],
                     "category": category, "reason": reason,
                     "material_meaning_difference": reason if category == "SAMI" else "",
                     "question": QUESTIONS.get(n, ""),
                     "exact_spict_context_en": r["exact_spict_context_en"],
                     "source_unit_ids": r["source_unit_ids"],
                     "existing_evidence_ids": r["terminology_evidence_ids"],
                     "web_evidence_ids": r["terveyskirjasto_evidence_ids"],
                     "preserved_conflict_status": r["conflict_status"],
                     "preserved_uncertainty": r["remaining_uncertainty"]})
    previous = [r for r in rows if r["previous_sami"]]
    return {"work_package": "WP-T1.2-HUMAN-REVIEW-REDUCTION-001", "assessment_type": "MODEL_REVIEW_ROUTING",
            "original_concepts": len(rows), "previous_sami_count": len(previous),
            "final_sami_count": sum(r["category"] == "SAMI" for r in rows),
            "previous_queue_dispositions": dict(Counter(r["category"] for r in previous)),
            "all_concept_dispositions": dict(Counter(r["category"] for r in rows)),
            "decisions": rows, "explicit_human_decisions_without_exact_decision_id": UNBOUND,
            "frailty_status": "ALREADY_DISCUSSED_DISPOSITION_NEEDS_RECORDING",
            "frailty_final_term": None, "new_term_approvals_by_model": 0}


def minimal_table(root: Path) -> list[list[str]]:
    fields = ["decision_id", "concept_en", "material_meaning_difference", "question", "exact_spict_context_en",
              "source_unit_ids", "existing_evidence_ids", "web_evidence_ids"]
    return [fields + ["human_decision", "human_decision_note"]] + [
        [str(r[k]) for k in fields] + ["", ""] for r in assessment(root)["decisions"] if r["category"] == "SAMI"]


def review_text(root: Path) -> str:
    a = assessment(root)
    out = ["# T1.2 — Samin arvioitavat merkityskysymykset", "",
           "Kolme avointa merkityskysymystä. Tämä jono korvaa T1.1:n laajan Sami-listan; se ei hyväksy termejä eikä käynnistä käännöstä.", ""]
    for r in a["decisions"]:
        if r["category"] != "SAMI":
            continue
        out += [f"## {r['decision_id']} — {r['concept_en']}", "", "**Mikä merkitys voi muuttua:** " + r["material_meaning_difference"], "",
                "**Kysymys:** " + r["question"], "", "Lähteen täsmällinen asiayhteys:", "", "```text", r["exact_spict_context_en"], "```", "",
                f"Lähdetunnisteet: {r['source_unit_ids']}", "",
                f"Aiempi näyttö: {r['existing_evidence_ids'] or 'Ei käsitteeseen sidottua havaintoa'}. T1.1: {r['web_evidence_ids'] or 'Ei käyttökelpoista katkelmaa'}.", "",
                "Merkitysero ja kysymys ovat mallin arvioita olemassa olevasta näytöstä; ne eivät ole lähteen antamia käännöksiä.", "",
                "Ihmisen päätös: __________", "Perustelu / ratkaisija / päivämäärä: __________", ""]
    out += ["## Aiemmin käsitellyt", "", "Frailty (T-009) on jo keskusteltu. Nykyisistä tiedostoista ei löydy täsmällistä lopullista ihmisratkaisua. Kirjaustarve säilyy erillisenä; peruskysymystä ei esitetä uudelleen eikä sanamuotoa arvata.", "",
            "T-002, T-013 ja T-016 on kirjattu ilmoitettujen ihmisratkaisujen mukaisesti. Muut kolme ilmoitettua päätöstä säilyvät raportissa ilman keksittyä päätöstunnistetta.", ""]
    return "\n".join(out)


def report_text(root: Path) -> str:
    a = assessment(root)
    out = ["# T1.2 — Ihmisarvioinnin rajaus", "",
           "Samin jono pienenee 21 kohdasta 3 merkityskysymykseen. Kaikki 29 käsitettä, 31 alkuperäistä evidenssiyhteyttä ja 28 T1.1-havaintoa on tarkastettu. Alkuperäiset arviointiasiakirjat ovat historiallista näyttöä; tämä raportti määrittää nykyisen Sami-reitityksen.", "",
           "Pelkkä kliininen riskiluokka, sanaston puuttuva osuma tai mahdollisuus huonoon käännökseen ei edellytä domain-arviointia. Tavalliset merkityksen säilyttämisen tarkistukset kuuluvat myöhempään itsenäiseen käännökseen ja synteesiin. Niitä ei ole tässä ajettu.", "",
           "## Lukumäärät", "", "| Luokka | Poistettu aiemmasta 21 kohdan jonosta | Kaikista 29 käsitteestä |", "| --- | ---: | ---: |"]
    for cat in ["STYLISTIC_OR_EQUIVALENT", "EVIDENCED_OR_OBVIOUS", "HUMAN_DECIDED", "G1_G2_SYNTHESIS", "DISCUSSED_RECORDING_NEEDED"]:
        out.append(f"| {cat} | {a['previous_queue_dispositions'].get(cat, 0)} | {a['all_concept_dispositions'].get(cat, 0)} |")
    out += ["", "Vanhan jonon 19 kohtaa poistetaan ja 2 säilytetään (T-003, T-027). Kaikkien 29 käsitteen uudelleenarvioinnissa mukaan tulee T-018, jonka MEDIUM-riskiluokka jätti sen aiemman HIGH-pohjaisen listan ulkopuolelle. Lopputulos: 21 − 19 + 1 = 3. Lukua ei ole kiintiöity.", "",
            "Aidosti avoimet uudet merkityskysymykset: 3. Frailtyn aiemman ratkaisun kirjaustarve: 1, erillään tästä jonosta. Ilmeiseksi luokittelu ei muuta aiempaa evidence-status-arvoa eikä hyväksy termiä.", "",
            "## Lopulliset englanninkieliset käsitteet", "", *[f"- {r['concept_en']}" for r in a["decisions"] if r["category"] == "SAMI"], "",
            "## Ihmisen päätösten kirjaus", "", "Lähde: projektinomistajan WP-T1.2-HUMAN-REVIEW-REDUCTION-001-viesti. Kirjattu 2026-09-07; alkuperäistä päätöspäivää ei ilmoitettu, joten decision_date jää tyhjäksi. ACCEPT tallentaa ilmoitetun päätöksen; hyväksyttyä sanastoa ei muuteta.", "",
            "| Olemassa oleva päätöstunniste | Käsite | Ihmisen ilmoittama suomi | Ratkaisija |", "| --- | --- | --- | --- |"]
    for identifier, (concept, term, maker) in BINDINGS.items():
        out.append(f"| {identifier} | {concept} | {term} | {maker} |")
    out += ["", "Seuraavat ihmisratkaisut säilytetään sellaisinaan, mutta human_terminology_decisions.tsv-tiedostoon ei ole turvallista tunnistesidosta. Lähdeyksikön tunniste ei ole terminologiapäätöksen tunniste, eikä läheinen laaja käsiteryhmä ole täsmällinen vastaavuus.", "",
            "| Ilmoitettu käsite | Ihmisen ilmoittama suomi | Lähdeyksiköt |", "| --- | --- | --- |"]
    for r in UNBOUND:
        out.append(f"| {r['concept_en']} | {r['finnish']} | {', '.join(r['source_unit_ids'])} |")
    out += ["", "Kaikkien kolmen ratkaisija on Project Owner. Less well ei ole T-002:n erillinen pääkäsite; usual activities on T-017:n osakonteksti; cancer treatment -kelpoisuus ei ole T-014:n oirehoitokäsitteen hyväksyntä. Päätöksiä ei kysytä uudelleen.", "",
            "Frailty T-009: ilmoituksen mukaan jo ihmisten kesken keskusteltu. Nykyinen päätöstiedosto on ennen tätä ajoa kokonaan tyhjä; T1/T1.1:ssa on mallin tulkintoja ja gerasteniaa koskeva lähdekatkelma, mutta ei täsmällistä lopullista ihmisratkaisua. Luokka ALREADY_DISCUSSED_DISPOSITION_NEEDS_RECORDING; lopullinen termi jätetään kirjaamatta.", "",
            "## Kaikkien 29 käsitteen reititys", "", "| ID | Käsite | Reititys | Perustelu |", "| --- | --- | --- | --- |"]
    for r in a["decisions"]:
        out.append(f"| {r['decision_id']} | {r['concept_en']} | {r['category']} | {r['reason']} |")
    out += ["", "## Näytön ja ristiriitojen säilytys", "", "T1_2_reclassification.json säilyttää jokaisen rivin vanhat näyttötunnisteet, epävarmuuden ja ristiriitatilan rinnakkain uuden reitityksen kanssa. T1/T1.1-asiakirjoja, kuutta alkuperäistä ristiriitaa tai seitsemää T1.1-merkitysrajaushavaintoa ei ratkaista tai kirjoiteta uudelleen. Myöhempi todellinen ristiriita käännöksissä voidaan käsitellä erikseen; se ei oikeuta ennakoivaan laajaan kyselyjonoon.", "",
            "Maksansiirron sekä otsikon lähdevaltuuskysymykset säilyvät. Sami-jonosta poisto ei ratkaise lähdevaatimuksia tai anna julkaisuvaltuutta. Tässä ei ajeta G1:tä, G2:ta eikä hyväksytä kokonaisia käännösyksiköitä.", "",
            "## Tarkistukset", "", "T1_2_VALIDATION_RESULTS.json sisältää toteutuneet testit, validoinnit ja Git-tilan. Kaikista aiemmista artefakteista otettiin eheysluettelo; vain human_terminology_decisions.tsv muuttuu täsmällisesti kolmelta riviltä. Sen aiempi tavusisältö säilyy T1_2_human_decisions_before.tsv-tiedostossa. Historialliset T1/T1.1-validoinnit tarkastavat edelleen alkuperäisen sisällön ja lisäksi nykyisen ihmisratkaisusiirtymän; vanhoja tiivisteitä ei vaihdeta.", "",
            "Hyväksyttyjä sanastorivejä edelleen 0. Ihmisen nimenomaisesti ilmoittamia kirjattuja terminologiapäätöksiä 3. Ei mallin tekemiä termihyväksyntöjä, käännösehdokkaita, committia tai pushia.", ""]
    return "\n".join(out)


def validate_reduction(root: Path) -> dict[str, Any]:
    lock = read_json(root / BASE / "T1_2_input_integrity.json")
    for name, expected in lock["protected_files"].items():
        content = historical_human_bytes(root) if name == HUMAN_FILE else (root / name).read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise IntegrityError(f"T1.2 protected artifact changed: {name}")
    validate_enrichment(root)
    a = assessment(root)
    if len(a["decisions"]) != 29 or len({r["decision_id"] for r in a["decisions"]}) != 29:
        raise IntegrityError("Missing or duplicate decisions")
    for identifier, (concept, _, _) in BINDINGS.items():
        if next(r for r in a["decisions"] if r["decision_id"] == identifier)["concept_en"] != concept:
            raise IntegrityError("Human binding does not match exact concept")
    if read_json(root / BASE / "T1_2_reclassification.json") != a:
        raise IntegrityError("Reduction classification/evidence mismatch")
    queue_text = (root / BASE / QUEUE).read_text(encoding="utf-8")
    closure_snapshot = root / BASE / "T1_3_SAMI_QUEUE_BEFORE_CLOSURE.tsv"
    if closure_snapshot.exists():
        if queue_text != tsv_text([minimal_table(root)[0]]):
            raise IntegrityError("Minimal Sami queue mismatch after closure")
        queue_text = closure_snapshot.read_text(encoding="utf-8")
    if queue_text != tsv_text(minimal_table(root)):
        raise IntegrityError("Minimal Sami queue mismatch or human decision injected")
    for name, text in [(REPORT, report_text(root)), (REVIEW, review_text(root))]:
        if (root / BASE / name).read_text(encoding="utf-8") != text:
            raise IntegrityError(f"Review/report mismatch: {name}")
    return {k: v for k, v in a.items() if k not in {"decisions", "explicit_human_decisions_without_exact_decision_id"}}


def write_artifacts(root: Path, payload: Path) -> None:
    from .human_terminology_decisions import expected_human_table

    for name, text in [("T1_2_reclassification.json", json.dumps(assessment(root), ensure_ascii=False, indent=2) + "\n"),
                       (REPORT, report_text(root)), (REVIEW, review_text(root))]:
        path = root / BASE / name
        if path.exists() and path.read_text(encoding="utf-8") != text:
            raise IntegrityError(f"Refusing to overwrite differing artifact: {name}")
        path.write_text(text, encoding="utf-8")
    payload.write_text(json.dumps({QUEUE: minimal_table(root), "human_terminology_decisions.tsv": expected_human_table(root)}, ensure_ascii=False), encoding="utf-8")
