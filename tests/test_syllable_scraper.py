"""Offline parser and workbook tests for the syllable scraper."""

from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from notebooks.scrapping.syllable_scraper import (
    OUTPUT_FILE,
    PROJECT_ROOT,
    REQUEST_DELAY_SECONDS,
    WORDS,
    WORDS_FILE,
    ResultValidationError,
    ScraperHTTPError,
    _check_response_status,
    load_failed_words,
    normalize_word,
    parse_result,
    save_to_excel,
)


def result_card(
    word: str,
    interpretation: str,
    count: int,
    position: int,
    syllables: str,
    phenomenon: str = "",
    group: str = "",
) -> str:
    """Build a compact fixture matching the site's observed result-card markup."""
    phenomenon_item = (
        f'<li class="list-group-item"><span class="text-muted">{phenomenon}: '
        f'</span><span class="float-right">{word[:1]}<b>{group}</b>{word[1:]}</span></li>'
        if phenomenon
        else ""
    )
    explanation = (
        f"La palabra {word} tiene un {phenomenon.casefold()} en el grupo vocálico "
        f"<b><i>{group}</i></b>."
        if phenomenon
        else ""
    )
    return f"""
    <div class="card tarjeta">
      <div class="card-header cardHeaderAccordion">
        <span class="accordionWord">{word}</span>
        <span class="accordionFlexionTextMuted">{interpretation}</span>
      </div>
      <div class="card-body"><ul class="list-group">
        <li class="list-group-item"><span class="text-muted">Número sílabas: </span><span class="float-right">{count}</span></li>
        <li class="list-group-item"><span class="text-muted">Posición sílaba tónica: </span><span class="float-right">{position}</span></li>
        <li class="list-group-item"><span class="text-muted">Sílabas: </span><span class="float-right">{syllables}</span></li>
        <li class="list-group-item"><span class="text-muted">Acentuación: </span><span class="float-right">llana</span></li>
        <li class="list-group-item"><span class="text-muted">Tipo de acento: </span><span class="float-right">prosódico</span></li>
        {phenomenon_item}
      </ul><p>{explanation}</p></div>
    </div>
    """


@pytest.mark.parametrize(
    ("word", "count", "position", "syllables", "phenomenon", "group"),
    [
        ("quisiera", 3, 2, "qui-sie-ra", "Diptongo", "ie"),
        ("teléfono", 4, 2, "te-lé-fo-no", "", ""),
        ("país", 2, 2, "pa-ís", "Hiato", "aí"),
        ("averiguáis", 4, 4, "a-ve-ri-guáis", "Triptongo", "uai"),
    ],
)
def test_parse_sample_words(word, count, position, syllables, phenomenon, group):
    html = result_card(
        word, "verbo", count, position, syllables, phenomenon, group
    )

    [record] = parse_result(html, word)

    assert record["word"] == word
    assert record["syllable_count"] == count
    assert record["stressed_position"] == position
    assert record["syllables"] == syllables
    assert record["stressed_syllable"] == syllables.split("-")[position - 1]
    if phenomenon:
        key = {
            "Diptongo": "diphthong",
            "Triptongo": "triphthong",
            "Hiato": "hiatus",
        }[phenomenon]
        assert record[f"has_{key}"] is True
        assert record[f"{key}_groups"] == group


def test_parser_keeps_multiple_grammatical_interpretations():
    html = result_card("sabia", "adjetivo", 2, 1, "sa-bia") + result_card(
        "sabia", "verbo", 3, 2, "sa-bí-a", "Hiato", "í-a"
    )

    records = parse_result(html, "sabia")

    assert [row["grammatical_interpretation"] for row in records] == [
        "adjetivo",
        "verbo",
    ]


@pytest.mark.parametrize(
    "count,position,syllables",
    [(3, 2, "qui-ra"), (3, 4, "qui-sie-ra"), (0, 1, "")],
)
def test_parser_rejects_inconsistent_syllable_data(count, position, syllables):
    html = result_card("quisiera", "verbo", count, position, syllables)

    with pytest.raises(ResultValidationError):
        parse_result(html, "quisiera")


def test_empty_or_unrecognized_result_is_empty():
    assert parse_result("<html><body>Palabra no encontrada</body></html>", "nada") == []


@pytest.mark.parametrize("status", [403, 429])
def test_blocked_or_rate_limited_response_stops_scraper(status):
    with pytest.raises(ScraperHTTPError, match=str(status)):
        _check_response_status(status)


def test_normalize_word_repairs_mojibake_and_unicode_composition():
    assert normalize_word("telÃ©fono") == "teléfono"
    assert normalize_word("PAI\u0301S") == "país"


def test_project_paths_and_word_list_are_loaded_from_project_root():
    assert PROJECT_ROOT == Path(__file__).resolve().parents[1]
    assert WORDS_FILE == PROJECT_ROOT / "data" / "palabras_unicas.txt"
    assert OUTPUT_FILE == PROJECT_ROOT / "data" / "syllable_database.xlsx"
    assert WORDS == [line.strip() for line in WORDS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert REQUEST_DELAY_SECONDS == 15


def test_excel_appends_results_preserves_existing_rows_and_retries(tmp_path: Path):
    output_file = tmp_path / "db.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(
        [
            "word",
            "normalized_word",
            "syllable_count",
            "stressed_position",
            "syllables",
            "stressed_syllable",
            "unstressed_syllables",
            "accentuation",
            "accent_type",
            "has_diphthong",
            "diphthong_groups",
            "has_triphthong",
            "triphthong_groups",
            "has_hiatus",
            "hiatus_groups",
            "source",
            "status",
        ]
    )
    sheet.append(["legacy", "legacy", 2, 1, 2, None, None, "llana"])
    workbook.save(output_file)

    failure = {"país": ("país", "timeout", "2026-11-17T10:00:00+00:00")}
    save_to_excel([], failure, output_file)
    assert load_failed_words(output_file) == ["país"]
    record = parse_result(
        result_card("país", "sustantivo", 2, 2, "pa-ís", "Hiato", "aí"), "país"
    )[0]
    save_to_excel([record, record], failure, output_file)
    save_to_excel([record], {}, output_file)

    saved = load_workbook(output_file, data_only=True)
    result_sheet = saved["Sheet1"]
    headers = {cell.value: cell.column for cell in result_sheet[1]}
    rows = list(result_sheet.iter_rows(min_row=2, values_only=True))
    assert rows[0][0] == "legacy"
    assert sum(row[headers["word"] - 1] == "país" for row in rows) == 1
    assert rows[1][headers["grammatical_interpretation"] - 1] == "sustantivo"
    assert saved["failed_words"].max_row == 1
    assert load_failed_words(output_file) == []
    saved.close()


def test_default_output_path_is_inside_project_data_directory():
    assert OUTPUT_FILE.name == "syllable_database.xlsx"
    assert OUTPUT_FILE.parent.name == "data"
    assert OUTPUT_FILE.parent.parent == Path(__file__).resolve().parents[1]
