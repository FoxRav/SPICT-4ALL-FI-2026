"""Audited field-specific extraction rules for the five frozen terminology files.

These rules bind semantic fields to exact line ranges/context and complete spans,
not arbitrary page substrings. New sources or changed rules require evidence review.
No publisher/date/URL is inferred for the two CSV exports.
"""

from __future__ import annotations

from typing import Any

METADATA_BINDINGS: dict[tuple[str, str], dict[str, Any]] = {
    ("a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f", "title"): {
        "kind": "PDF_PAGE",
        "page": 1,
        "locator": "running title line in the page footer block",
        "metadata_field": "title",
        "source_file": "hoitosuositukseen-palliatiivinen-hoito-ja-saattohoito-liittyvää-sanastoa.pdf",
        "source_sha256": "a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f",
        "exact_source_text": "Hoitosuositukseen "
        "Palliatiivinen "
        "hoito "
        "ja "
        "saattohoito "
        "liittyvää "
        "sanastoa",
        "semantic_evidence_type": "DOCUMENT_TITLE",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 65,
        "line_count": 1,
        "context_text": "Hoitosuositukseen "
        "Palliatiivinen "
        "hoito "
        "ja "
        "saattohoito "
        "liittyvää "
        "sanastoa",
        "span_start": 0,
        "span_end": 72,
    },
    (
        "a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f",
        "publisher_organisation",
    ): {
        "kind": "PDF_PAGE",
        "page": 3,
        "locator": "copyright line above the running title",
        "metadata_field": "publisher_organisation",
        "source_file": "hoitosuositukseen-palliatiivinen-hoito-ja-saattohoito-liittyvää-sanastoa.pdf",
        "source_sha256": "a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f",
        "exact_source_text": "Suomalainen Lääkäriseura Duodecim",
        "semantic_evidence_type": "PUBLISHER_ATTRIBUTION",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 47,
        "line_count": 1,
        "context_text": "© 2026 Suomalainen Lääkäriseura Duodecim",
        "span_start": 7,
        "span_end": 40,
    },
    (
        "a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f",
        "publication_version_date",
    ): {
        "kind": "PDF_PAGE",
        "page": 1,
        "locator": "date line below the working-group line",
        "metadata_field": "publication_version_date",
        "source_file": "hoitosuositukseen-palliatiivinen-hoito-ja-saattohoito-liittyvää-sanastoa.pdf",
        "source_sha256": "a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f",
        "exact_source_text": "16.2.2018",
        "semantic_evidence_type": "PUBLICATION_DATE",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 4,
        "line_count": 1,
        "context_text": "16.2.2018",
        "span_start": 0,
        "span_end": 9,
    },
    (
        "a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f",
        "source_url",
    ): {
        "kind": "PDF_PAGE",
        "page": 1,
        "locator": "retrieval URL printed in the page footer block",
        "metadata_field": "source_url",
        "source_file": "hoitosuositukseen-palliatiivinen-hoito-ja-saattohoito-liittyvää-sanastoa.pdf",
        "source_sha256": "a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f",
        "exact_source_text": "https://www.kaypahoito.fi/nix01005?utm_source=chatgpt.com",
        "semantic_evidence_type": "DOCUMENT_RETRIEVAL_OR_PERSISTENT_URL",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 66,
        "line_count": 1,
        "context_text": "https://www.kaypahoito.fi/nix01005?utm_source=chatgpt.com",
        "span_start": 0,
        "span_end": 57,
    },
    (
        "a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f",
        "copyright_notice",
    ): {
        "kind": "PDF_PAGE",
        "page": 3,
        "locator": "copyright line after the final terminology row",
        "metadata_field": "copyright_notice",
        "source_file": "hoitosuositukseen-palliatiivinen-hoito-ja-saattohoito-liittyvää-sanastoa.pdf",
        "source_sha256": "a53e67df6962e182eb2a4113ec7b93a0efa5cd4a95536866d69a83bdabedb38f",
        "exact_source_text": "© 2026 Suomalainen Lääkäriseura Duodecim",
        "semantic_evidence_type": "COPYRIGHT_NOTICE",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 47,
        "line_count": 1,
        "context_text": "© 2026 Suomalainen Lääkäriseura Duodecim",
        "span_start": 0,
        "span_end": 40,
    },
    ("a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419", "title"): {
        "kind": "PDF_PAGE",
        "page": 1,
        "locator": "document title line",
        "metadata_field": "title",
        "source_file": "palliatiivinen-hoito-ja-saattohoito.pdf",
        "source_sha256": "a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419",
        "exact_source_text": "Palliatiivinen hoito ja saattohoito",
        "semantic_evidence_type": "DOCUMENT_TITLE",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 0,
        "line_count": 1,
        "context_text": "Palliatiivinen hoito ja saattohoito",
        "span_start": 0,
        "span_end": 35,
    },
    (
        "a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419",
        "publisher_organisation",
    ): {
        "kind": "PDF_PAGE",
        "page": 1,
        "locator": "working-group attribution line",
        "metadata_field": "publisher_organisation",
        "source_file": "palliatiivinen-hoito-ja-saattohoito.pdf",
        "source_sha256": "a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419",
        "exact_source_text": "Suomalaisen "
        "Lääkäriseuran "
        "Duodecimin "
        "ja "
        "Suomen "
        "Palliatiivisen "
        "Lääketieteen "
        "yhdistyksen "
        "asettama "
        "työryhmä",
        "semantic_evidence_type": "PUBLISHER_ATTRIBUTION",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 3,
        "line_count": 1,
        "context_text": "Suomalaisen "
        "Lääkäriseuran "
        "Duodecimin "
        "ja "
        "Suomen "
        "Palliatiivisen "
        "Lääketieteen "
        "yhdistyksen "
        "asettama "
        "työryhmä",
        "span_start": 0,
        "span_end": 104,
    },
    (
        "a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419",
        "publication_version_date",
    ): {
        "kind": "PDF_PAGE",
        "page": 1,
        "locator": "publication and status line under the title",
        "metadata_field": "publication_version_date",
        "source_file": "palliatiivinen-hoito-ja-saattohoito.pdf",
        "source_sha256": "a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419",
        "exact_source_text": "Julkaistu: 04.10.2019",
        "semantic_evidence_type": "PUBLICATION_DATE",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 1,
        "line_count": 1,
        "context_text": "Käypä "
        "hoito "
        "-suositus "
        "| "
        "Julkaistu: "
        "04.10.2019 "
        "| "
        "Tila: "
        "voimassa",
        "span_start": 24,
        "span_end": 45,
    },
    (
        "a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419",
        "source_url",
    ): {
        "kind": "PDF_PAGE",
        "page": 46,
        "locator": "retrieval URL printed in the final page footer block",
        "metadata_field": "source_url",
        "source_file": "palliatiivinen-hoito-ja-saattohoito.pdf",
        "source_sha256": "a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419",
        "exact_source_text": "https://www.kaypahoito.fi/hoi50063?utm_source=chatgpt.com",
        "semantic_evidence_type": "DOCUMENT_RETRIEVAL_OR_PERSISTENT_URL",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 20,
        "line_count": 1,
        "context_text": "https://www.kaypahoito.fi/hoi50063?utm_source=chatgpt.com",
        "span_start": 0,
        "span_end": 57,
    },
    (
        "a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419",
        "copyright_notice",
    ): {
        "kind": "PDF_PAGE",
        "page": 45,
        "locator": "copyright line",
        "metadata_field": "copyright_notice",
        "source_file": "palliatiivinen-hoito-ja-saattohoito.pdf",
        "source_sha256": "a37cffaa4fdcb39db9ba76fe6959cb13e4af117f5bb3ba0cd70ed5c4792a2419",
        "exact_source_text": "© 2026 Suomalainen Lääkäriseura Duodecim",
        "semantic_evidence_type": "COPYRIGHT_NOTICE",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 36,
        "line_count": 1,
        "context_text": "© 2026 Suomalainen Lääkäriseura Duodecim",
        "span_start": 0,
        "span_end": 40,
    },
    ("a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554", "title"): {
        "kind": "PDF_PAGE",
        "page": 2,
        "locator": "title block on the imprint page",
        "metadata_field": "title",
        "source_file": "OHJ2022_004_08042022.pdf",
        "source_sha256": "a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554",
        "exact_source_text": "Palliatiivisen "
        "hoidon "
        "ja "
        "saattohoidon \n"
        "kansallinen "
        "laatusuositus",
        "semantic_evidence_type": "DOCUMENT_TITLE",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 8,
        "line_count": 2,
        "context_text": "Palliatiivisen "
        "hoidon "
        "ja "
        "saattohoidon \n"
        "kansallinen "
        "laatusuositus ",
        "span_start": 0,
        "span_end": 64,
    },
    (
        "a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554",
        "publisher_organisation",
    ): {
        "kind": "PDF_PAGE",
        "page": 3,
        "locator": "copyright line on the imprint page",
        "metadata_field": "publisher_organisation",
        "source_file": "OHJ2022_004_08042022.pdf",
        "source_sha256": "a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554",
        "exact_source_text": "Terveyden ja hyvinvoinnin laitos",
        "semantic_evidence_type": "PUBLISHER_ATTRIBUTION",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 28,
        "line_count": 1,
        "context_text": "© Kirjoittajat ja Terveyden ja hyvinvoinnin laitos ",
        "span_start": 18,
        "span_end": 50,
    },
    (
        "a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554",
        "publication_version_date",
    ): {
        "kind": "PDF_PAGE",
        "page": 3,
        "locator": "place and year of publication on the imprint page",
        "metadata_field": "publication_version_date",
        "source_file": "OHJ2022_004_08042022.pdf",
        "source_sha256": "a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554",
        "exact_source_text": "Helsinki, 2022",
        "semantic_evidence_type": "PUBLICATION_DATE",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 49,
        "line_count": 1,
        "context_text": "Helsinki, 2022 ",
        "span_start": 0,
        "span_end": 14,
    },
    (
        "a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554",
        "source_url",
    ): {
        "kind": "PDF_PAGE",
        "page": 3,
        "locator": "persistent URN below the ISBN on the imprint page",
        "metadata_field": "source_url",
        "source_file": "OHJ2022_004_08042022.pdf",
        "source_sha256": "a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554",
        "exact_source_text": "http://urn.fi/URN:ISBN:978-952-343-824-8",
        "semantic_evidence_type": "DOCUMENT_RETRIEVAL_OR_PERSISTENT_URL",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 42,
        "line_count": 1,
        "context_text": "http://urn.fi/URN:ISBN:978-952-343-824-8 ",
        "span_start": 0,
        "span_end": 40,
    },
    (
        "a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554",
        "copyright_notice",
    ): {
        "kind": "PDF_PAGE",
        "page": 3,
        "locator": "copyright line on the imprint page",
        "metadata_field": "copyright_notice",
        "source_file": "OHJ2022_004_08042022.pdf",
        "source_sha256": "a9171d1373a7ec8d5b35f8ba25d3ed3c6c4cda309f200e5721465a123921c554",
        "exact_source_text": "© Kirjoittajat ja Terveyden ja hyvinvoinnin laitos",
        "semantic_evidence_type": "COPYRIGHT_NOTICE",
        "extraction_rule": "FROZEN_PDF_LINE_RANGE_AND_FIELD_SPAN",
        "line_start": 28,
        "line_count": 1,
        "context_text": "© Kirjoittajat ja Terveyden ja hyvinvoinnin laitos ",
        "span_start": 0,
        "span_end": 50,
    },
    ("3e2ae5ef2f2ed833deebd54b06688b1ab0b334bed940750f3320b11c3137a2e1", "title"): {
        "kind": "CSV_CELL",
        "row": 3,
        "header": "properties.prefLabel.fi",
        "locator": "vocabulary title row preceding the concept rows",
        "metadata_field": "title",
        "source_file": "Terveydenhuollon_tiedonhallinnan_sanasto.csv",
        "source_sha256": "3e2ae5ef2f2ed833deebd54b06688b1ab0b334bed940750f3320b11c3137a2e1",
        "exact_source_text": "Terveydenhuollon tiedonhallinnan sanasto",
        "semantic_evidence_type": "DOCUMENT_TITLE",
        "extraction_rule": "CSV_VOCABULARY_TITLE_ROW",
        "context_text": "Terveydenhuollon tiedonhallinnan sanasto",
    },
    ("75925bf85c6297c50fa27ce3997ba62078a97f5c3976ce85e6a7aac694fcd829", "title"): {
        "kind": "CSV_CELL",
        "row": 3,
        "header": "properties.prefLabel.fi",
        "locator": "vocabulary title row preceding the concept rows",
        "metadata_field": "title",
        "source_file": "Sosiaali-_ja_terveydenhuollon_uudistamisen_keskeiset_käsitteet.csv",
        "source_sha256": "75925bf85c6297c50fa27ce3997ba62078a97f5c3976ce85e6a7aac694fcd829",
        "exact_source_text": "Sosiaali- "
        "ja "
        "terveydenhuollon "
        "uudistamisen "
        "keskeiset "
        "käsitteet",
        "semantic_evidence_type": "DOCUMENT_TITLE",
        "extraction_rule": "CSV_VOCABULARY_TITLE_ROW",
        "context_text": "Sosiaali- "
        "ja "
        "terveydenhuollon "
        "uudistamisen "
        "keskeiset "
        "käsitteet",
    },
}
