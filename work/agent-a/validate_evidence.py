"""Agent A structural checks and limited lexical semantic tripwires."""
import json
import re
from dataclasses import asdict
from pathlib import Path

from build_evidence import HERE, ROOT, RUN_ID, sources
from jsonschema import Draft202012Validator, FormatChecker

from spict4all.artifacts import validate_jsonl_artifact
from spict4all.coverage import require_complete_coverage
from spict4all.hashing import sha256_file, sha256_text

# Tripwires test high-risk features, not semantic equivalence or clinical validity.
ANCHORS = {
    '004': ['ei ole yhtä hyvä', 'usein', 'yli puolet päivästä', 'vuoteessa tai tuolissa'],
    '005': ['muilta', 'enemmän', 'ja/tai', 'vuoksi'],
    '006': ['huolehtiva', 'enemmän', 'apua ja tukea'],
    '007': ['selvästi', 'viime kuukausien', 'edelleen liian laiha'],
    '008': ['suurimman osan ajasta', 'vaikka', 'hoidetaan hyvin'],
    '009': ['henkilö (tai perhe)', 'pyytää', 'valitsee', 'vähentämisen', 'lopettamisen', 'pidättäytymisen', 'toivoo', 'elämänlaatuun'],
    '015': ['levätessä', 'liikkuessa', 'muutaman askeleen'],
    '016': ['eivät toimi hyvin', 'heikkenee'],
    '017': ['ei ole riittävän hyväkuntoinen', 'tai', 'lievittää oireita'],
    '018': ['johtuvia', 'ei ole mahdollinen'],
    '019': ['lopettaminen tai', 'valitseminen', 'aloittamisen sijaan'],
    '020': ['lopettaminen tai aloittamatta'],
    '024': ['ei pysty', 'ilman apua'],
    '025': ['pitkäaikaisten', 'levätessä', 'liikkuessa', 'muutaman askeleen', 'silloinkin', 'parhaimmillaan'],
    '026': ['viimeksi kuluneen vuoden', 'esimerkiksi'],
    '028': ['ajoittaista'], '029': ['eivät toimi hyvin'],
    '032': ['syö ja juo vähemmän'], '033': ['tarvitsee', 'suuren osan päivästä ja yöstä'],
    '035': ['on tarvinnut', 'hengityskone', 'sairaalassa'],
    '036': ['ei pysty', 'vain vähän', 'muihin ihmisiin'],
    '042': ['ei ole saatavilla', 'tai se ei tehoa hyvin'],
    '044': ['voimme', 'henkilön ja hänen perheensä'],
    '046': ['aloita', 'henkilön ja hänen perheensä tai', 'huolehtivan', 'nyt', 'miksi', 'siltä varalta'],
    '047': ['jatkuva', 'lisääntyviä', 'ja/tai', 'yhden tai useamman', 'jälkeen'],
    '048': ['pyydä', 'sairaanhoitajalta', 'lääkäriltä', 'sosiaalityöntekijältä', 'tai muulta henkilökunnalta', 'jos', 'henkilön tai perheen', 'hoitoa ja tukea'],
    '049': ['tarkastelemme', 'lääkkeitä ja muita hoitoja', 'kokonaisvaltainen hoito', 'oireet', 'tunne-elämään', 'sosiaaliseen', 'toimintakykyyn', 'talouteen', 'henkisiin ja hengellisiin', 'kulttuuriin'],
    '050': ['pyydä', 'jos', 'vaikea'],
    '051': ['jaetaan', 'on tarpeen nähdä', 'pidetään ajan tasalla'],
}


def validate(path=HERE / 'candidates.jsonl'):
    evidence = sources()
    records = validate_jsonl_artifact(path, ROOT / 'schemas/translation_candidate.schema.json', source_records=evidence)
    require_complete_coverage(evidence, records)
    assert sum(s.source_kind.value == 'canonical_source_unit' for s in evidence) == 53
    assert sum(s.source_kind.value == 'official_change_requirement' for s in evidence) == 1
    expected = {s.evidence_id: s for s in evidence}
    metadata = json.loads((HERE / 'run_metadata.json').read_text(encoding='utf-8'))
    Draft202012Validator(json.loads((ROOT / 'schemas/run_metadata.schema.json').read_text()), format_checker=FormatChecker()).validate(metadata)
    for item in metadata['inputs']:
        p = Path(item['path'])
        assert sha256_file(p) == item['sha256'] and p.stat().st_size == item['bytes'], item['path']
    frozen_units = {u['unit_id']: u for u in map(json.loads, (ROOT / 'data/source_units.jsonl').read_text(encoding='utf-8').splitlines())}
    requirement = json.loads((ROOT / 'data/source_requirements.jsonl').read_text(encoding='utf-8'))
    checks = []
    for record in records:
        uid = record['unit_id']
        source = expected[uid]
        audit = record['extensions']['g1_agent_a']
        assert audit['source_contract'] == json.loads(json.dumps(asdict(source))), uid
        assert audit['source_text_en'] == source.exact_source_text_en, uid
        assert sha256_text(audit['source_text_en']) == record['source_text_sha256'], uid
        assert audit['frozen_record'] == frozen_units.get(uid, requirement), uid
        assert audit['translator_identity'] == 'Forward Translator A', uid
        assert audit['run_id'] == record['session_id'] == RUN_ID, uid
        assert audit['run_timestamp_utc'] == metadata['created_at_utc'], uid
        assert record['status'] == 'DRAFT' and record['model'] == 'GPT-6', uid
        fi = record['candidate_fi'].strip().lower()
        en = source.exact_source_text_en
        assert fi, uid
        assert uid == 'S4A-2026-052' or fi != en.lower(), uid
        assert not re.search(r'\b(the|their|person|treatment|problems|needs|not|health)\b', fi), uid
        if re.search(r'\bor\b', en, re.I):
            assert 'tai' in fi, uid
        if 'and/or' in en:
            assert 'ja/tai' in fi, uid
        if uid.startswith('S4A-2026-'):
            for anchor in ANCHORS.get(uid[-3:], []):
                assert anchor in fi, (uid, anchor)
        if uid == 'S4A-REQ-2026-001':
            assert 'ei ole mahdollinen' in fi
            assert audit['frozen_record']['publication_blocking'] is True
        if uid in ('S4A-2026-000', 'S4A-REQ-2026-001'):
            assert audit['source_contract']['final_inclusion_status'] == 'UNRESOLVED'
            assert audit['source_contract']['eligible_for_document_insertion'] is False
        checks.append({'unit_id': uid, 'structural_checks': 'PASS', 'lexical_tripwires': 'PASS', 'uncertainty': audit['uncertainty']})
    return {'expected': 54, 'translated': len(records), 'canonical': 53, 'source_requirements': 1,
            'result': 'PASS', 'limitations': 'Lexical tripwires cannot prove absence of semantic omissions/additions. Translator self-check only; no human approval or clinical validation.', 'items': checks}


if __name__ == '__main__':
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
