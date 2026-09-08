"""Project Owner closure of pre-G1 terminology review; never a G1 execution."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .adjudication import BASE, read_json
from .errors import IntegrityError
from .review_reduction import QUEUE, validate_reduction

REPORT = "T1_TERMINOLOGY_CLOSURE_REPORT.md"
DISPOSITION = {
    "work_package": "WP-T1.3-CLOSE-PRE-G1-001",
    "decision_maker": "Project Owner",
    "provenance": "Explicit Project Owner disposition in the WP-T1.3 user message; recorded 2026-09-08",
    "t1_status": "READY_FOR_G1",
    "concepts_reviewed": 29,
    "mandatory_pre_g1_sami_items": 0,
    "terminology_blockers_to_g1": 0,
    "g1_started": False,
    "glossary_entries_approved_by_this_work_package": 0,
    "dispositions": [
        {"decision_id": "T-003", "concept_en": "carer", "mandatory_pre_g1": False,
         "route": "INDEPENDENT_FORWARD_TRANSLATION_AND_SYNTHESIS", "mandatory_finnish_term": None,
         "note": "Resolve contextually; no mandatory Finnish glossary term."},
        {"decision_id": "T-018", "concept_en": "spiritual problems", "mandatory_pre_g1": False,
         "route": "INDEPENDENT_FORWARD_TRANSLATION_AND_SYNTHESIS", "mandatory_finnish_term": None,
         "note": "Ordinary meaning is sufficiently clear; no further terminology research or expert escalation."},
        {"decision_id": "T-027", "concept_en": "one or more strokes", "mandatory_pre_g1": False,
         "route": "INDEPENDENT_FORWARD_TRANSLATION_AND_SYNTHESIS", "mandatory_finnish_term": None,
         "note": "Ordinary Finnish translation evidence is sufficient; no further expert escalation."},
        {"decision_id": "T-009", "concept_en": "frailty", "mandatory_pre_g1": False,
         "route": "ALREADY_DISCUSSED_TRANSLATION_AND_SYNTHESIS", "mandatory_finnish_term": None,
         "note": "Already discussed; missing final human wording/disposition is not invented. Not a pre-G1 blocker. A/B and synthesis may resolve it unless a genuinely material clinical ambiguity emerges later."},
    ],
}

REPORT_TEXT = """# T1 — Terminologiavaiheen sulkeminen

**T1 status: READY_FOR_G1**

| Tarkistus | Tulos |
| --- | ---: |
| Käsitteitä arvioitu | 29 |
| MUST REVIEW WITH SAMI ennen G1:tä | 0 |
| Terminologiasta johtuvia G1-esteitä | 0 |
| Tässä työpaketissa hyväksyttyjä sanastotermejä | 0 |
| Tässä työpaketissa käynnistettyjä G1-ajoja | 0 |

Projektinomistajan nimenomainen WP-T1.3-CLOSE-PRE-G1-001-päätös sulkee pakollisen pre-G1-terminologia-arvioinnin. T1/T1.1/T1.2:n 29 käsitettä ja niiden arviointitiedot on tarkastettu. Tämä sulkeminen korvaa aiempien raporttien pakolliset pre-G1-terminologia- ja Sami-suositukset. Historialliset raportit eivät ole aktiivisia työjonoja.

## Projektinomistajan ratkaisut

- **T-003 carer:** ei pakollista pre-G1-ihmis- tai asiantuntija-arviointia. Poistettu Sami-jonosta. Pakollista suomenkielistä sanastotermiä ei aseteta; asiayhteys ratkaistaan itsenäisissä käännöksissä ja synteesissä.
- **T-018 spiritual problems:** ei pakollista pre-G1-arviointia. Tavallinen merkitys on riittävän selvä käännöstyöhön. Ei uutta terminologiatutkimusta tai asiantuntijaeskalointia.
- **T-027 one or more strokes:** ei pakollista pre-G1-arviointia. Tavallinen suomenkielinen käännösnäyttö riittää työnkulkuun. Ei uutta asiantuntijaeskalointia.
- **T-009 frailty:** säilyy jo keskusteltuna. Puuttuvaa lopullista ihmisratkaisua tai sanamuotoa ei keksitä. Ei pre-G1-estettä; A/B-käännökset ja synteesi voivat ratkaista sanamuodon, ellei myöhemmin ilmene aidosti merkittävää kliinistä epäselvyyttä.

Ratkaisija on Project Owner, lähteenä tämän työpaketin käyttäjäviesti. Kirjauspäivä 2026-09-08. Nämä ovat työnkulun reitityspäätöksiä, eivät uusien suomenkielisten termien hyväksyntöjä.

## Aiemmat ihmisratkaisut ja jäljelle jäävä sanamuototyö

Aiemmat ihmisratkaisut säilyvät muuttumattomina: T-002 elinikää lyhentävät terveydentilat (Project Owner), T-013 hengityskone (Project Owner) ja T-016 kokonaisvaltainen hoito (Sami / domain expert). T1.2:ssa säilytetyt kolme muuta nimenomaista sanamuotoratkaisua pysyvät raportissa ilman keksittyjä päätöstunnisteita. human_terminology_decisions.tsv-tiedostoa ei muuteta tässä työpaketissa.

Ratkaisemattomat tyylilliset tai merkityksen kannalta ei-olennaiset sanamuodot voivat edetä itsenäisiin forward-käännöksiin ja synteesiin. Pakollisten pre-G1-päätösten puuttuminen ei tarkoita, että jokainen termi olisi APPROVED. Hyväksyttyyn sanastoon ei lisätä rivejä. Perusteettomia ihmisratkaisuja tai hyväksyntöjä ei ole keksitty.

## Historiallinen jäljitettävyys

T1_2_MINIMAL_SAMI_QUEUE.tsv sisältää nyt vain alkuperäisen otsikkorivin: aktiivisia pre-G1-kohtia on nolla. Kolmen kohdan aiempi jono säilyy tavuntarkasti tiedostossa T1_3_SAMI_QUEUE_BEFORE_CLOSURE.tsv. T1_3_input_integrity.json säilyttää aiempien artefaktien tiivisteet; T1_3_project_owner_disposition.json tallentaa yllä olevat reitityspäätökset koneellisesti.

T1/T1.1/T1.2:n näyttö, epävarmuudet, ristiriidat ja historialliset arvioinnit säilyvät. Niistä ei muodosteta uutta terminologiakyselyä. Otsikon ja maksansiirron erilliset lähdevaltuustiedot pysyvät muuttumattomina; terminologiavaiheen valmius ei ole julkaisu- tai koko työnkulun hyväksyntä.

## Validointi

T1_3_VALIDATION_RESULTS.json sisältää toteutuneet testit, lähde- ja terminologiavalidoinnit sekä Git-tilan. Historiallinen T1.2-validointi tarkistaa alkuperäisen jonon historiakopiosta ja edellyttää nykyiseltä jonolta tyhjää sisältöä otsikon jälkeen. Sulkemisvalidointi tarkistaa projektinomistajan täsmälliset reitityspäätökset, aiempien tiedostojen säilymisen ja sen, ettei uutta käännöstyötä ole syntynyt.

Ei lisätutkimusta, uusia terminologiakysymyksiä, G1-ajoa, virallisten lähteiden muutoksia, committia tai pushia.
"""


def validate_closure(root: Path) -> dict[str, Any]:
    validate_reduction(root)
    lock = read_json(root / BASE / "T1_3_input_integrity.json")
    for name, digest in lock["protected_files"].items():
        path = root / name
        if name == f"{BASE}/{QUEUE}":
            path = root / BASE / "T1_3_SAMI_QUEUE_BEFORE_CLOSURE.tsv"
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise IntegrityError(f"Closure protected artifact changed: {name}")
    if read_json(root / BASE / "T1_3_project_owner_disposition.json") != DISPOSITION:
        raise IntegrityError("Project Owner closure disposition mismatch")
    if (root / BASE / REPORT).read_text(encoding="utf-8") != REPORT_TEXT:
        raise IntegrityError("Closure report mismatch")
    work = sorted(p.relative_to(root).as_posix() for p in (root / "work").rglob("*") if p.is_file())
    if work != lock["work_files"]:
        raise IntegrityError("Closure must not start translation work")
    return {"t1_status": "READY_FOR_G1", "concepts_reviewed": 29,
            "pre_g1_terminology_blockers": 0, "active_sami_review_count": 0,
            "new_glossary_approvals": 0, "g1_started": False}
