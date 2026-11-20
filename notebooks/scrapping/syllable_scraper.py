"""Scrape syllable and stress analyses from Sílaba Tónica TIP."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import unicodedata
from typing import Any

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://tulengua.iatext.ulpgc.es/silaba-tonica/"
RESULT_TIMEOUT_MS = 45_000
SEARCH_INPUT_SELECTOR = "#FormularioContent_inputPalabra"
SEARCH_BUTTON_SELECTOR = "#FormularioContent_idBuscar"
RESULT_CARD_SELECTOR = "div.cardHeaderAccordion"

logger = logging.getLogger(__name__)


class ScraperHTTPError(RuntimeError):
    """Raised when the service blocks or rate-limits a search."""


class ResultValidationError(ValueError):
    """Raised when a result has inconsistent syllable or stress data."""


def _repair_encoding(word: str) -> str:
    """Repair common UTF-8-as-Windows-1252 text without damaging valid text."""
    candidate = word.strip()
    if "Ã" in candidate or "Â" in candidate:
        try:
            candidate = candidate.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return unicodedata.normalize("NFC", candidate)


def normalize_word(word: str) -> str:
    """Normalize a word for matching, including common mojibake repair."""
    return _repair_encoding(word).casefold()


def _display_word(word: str) -> str:
    """Return a normalized, user-facing spelling for a queued word."""
    return _repair_encoding(word)


def _value_for_label(card: Tag, wanted_label: str) -> str | None:
    """Read one labeled value from a result card, regardless of whitespace."""
    for item in card.select("li.list-group-item"):
        label = item.select_one(".text-muted")
        if label is None:
            continue
        label_text = re.sub(r"\s+", " ", label.get_text(" ", strip=True))
        if label_text.rstrip(" :").casefold() != wanted_label.casefold():
            continue

        value = item.select_one(".float-right")
        if value is not None:
            # Inline <b>/<i> markup highlights the stressed syllable/group.
            direct_value = value.get_text("", strip=True)
            if direct_value:
                return direct_value
        pieces = [
            child.get_text("", strip=True)
            if isinstance(child, Tag)
            else str(child).strip()
            for child in item.contents
            if child is not label
        ]
        direct_value = " ".join(piece for piece in pieces if piece)
        if direct_value:
            return direct_value

    following_labels = {
        "Número sílabas": "Posición sílaba tónica",
        "Posición sílaba tónica": "Sílabas",
        "Sílabas": "Acentuación",
        "Acentuación": "Tipo de acento",
    }
    next_label = following_labels.get(wanted_label)
    text = re.sub(r"\s+", " ", card.get_text(" ", strip=True))
    stop = rf"(?=\s+{re.escape(next_label)}\s*:|$)" if next_label else r"(?=$)"
    match = re.search(
        rf"{re.escape(wanted_label)}\s*:\s*(.*?){stop}",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    value = match.group(1).strip()
    if wanted_label == "Sílabas":
        value = re.sub(r"\s*[-‐‑‒–—]\s*", "-", value)
        value = re.sub(r"\s+", "", value)
    return value or None


def _phenomenon_groups(card: Tag, label: str, text: str) -> list[str]:
    """Extract highlighted or explanatory vowel groups for a phenomenon."""
    item = next(
        (
            candidate
            for candidate in card.select("li.list-group-item")
            if (candidate.select_one(".text-muted") is not None)
            and candidate.select_one(".text-muted")
            .get_text(" ", strip=True)
            .rstrip(" :")
            .casefold()
            == label.casefold()
        ),
        None,
    )
    if item is None:
        return []

    value = item.select_one(".float-right")
    if value is not None:
        highlighted = [
            node.get_text("", strip=True)
            for node in value.select("b, strong")
            if node.get_text("", strip=True)
        ]
        if highlighted:
            return highlighted

    name = {"Diptongo": "diptongo", "Triptongo": "triptongo", "Hiato": "hiato"}[label]
    match = re.search(
        rf"{name}\s+en\s+el\s+grupo\s+voc[aá]lico\s+([a-záéíóúü]+)",
        text,
        re.IGNORECASE,
    )
    return [match.group(1)] if match else []


def _parse_card(card: Tag, searched_word: str) -> dict[str, Any]:
    """Parse and validate one grammatical interpretation card."""
    card_text = re.sub(r"\s+", " ", card.get_text(" ", strip=True))
    syllable_count_text = _value_for_label(card, "Número sílabas")
    stressed_position_text = _value_for_label(card, "Posición sílaba tónica")
    syllables = _value_for_label(card, "Sílabas")
    accentuation = _value_for_label(card, "Acentuación")
    accent_type = _value_for_label(card, "Tipo de acento")

    if not syllable_count_text or not stressed_position_text or not syllables:
        raise ResultValidationError(
            "Faltan el número, la posición tónica o las sílabas"
        )
    if not syllable_count_text.isdigit() or not stressed_position_text.isdigit():
        raise ResultValidationError(
            "El número de sílabas o la posición tónica no es entero"
        )

    syllable_count = int(syllable_count_text)
    stressed_position = int(stressed_position_text)
    syllable_list = [part.strip() for part in syllables.split("-")]
    if (
        syllable_count < 1
        or len(syllable_list) != syllable_count
        or any(not syllable for syllable in syllable_list)
    ):
        raise ResultValidationError(
            f"La separación {syllables!r} no contiene {syllable_count} sílabas"
        )
    if not 1 <= stressed_position <= syllable_count:
        raise ResultValidationError(
            f"La posición tónica {stressed_position} está fuera de 1..{syllable_count}"
        )

    header = card.select_one(".cardHeaderAccordion")
    word_node = header.select_one(".accordionWord") if header else None
    part_of_speech = header.select_one(".accordionFlexionTextMuted") if header else None
    interpretation = part_of_speech.get_text(" ", strip=True) if part_of_speech else ""
    card_word = word_node.get_text(" ", strip=True) if word_node else searched_word
    if normalize_word(card_word) != normalize_word(searched_word):
        raise ResultValidationError(
            f"La ficha corresponde a {card_word!r}, no a {searched_word!r}"
        )

    diphthongs = _phenomenon_groups(card, "Diptongo", card_text)
    triphthongs = _phenomenon_groups(card, "Triptongo", card_text)
    hiatuses = _phenomenon_groups(card, "Hiato", card_text)

    return {
        "word": _display_word(searched_word),
        "normalized_word": normalize_word(searched_word),
        "grammatical_interpretation": interpretation,
        "syllable_count": syllable_count,
        "stressed_position": stressed_position,
        "syllables": "-".join(syllable_list),
        "stressed_syllable": syllable_list[stressed_position - 1],
        "unstressed_syllables": ", ".join(
            syllable
            for position, syllable in enumerate(syllable_list, start=1)
            if position != stressed_position
        ),
        "accentuation": accentuation,
        "accent_type": accent_type,
        "has_diphthong": bool(diphthongs),
        "diphthong_groups": ", ".join(diphthongs),
        "has_triphthong": bool(triphthongs),
        "triphthong_groups": ", ".join(triphthongs),
        "has_hiatus": bool(hiatuses),
        "hiatus_groups": ", ".join(hiatuses),
        "source": BASE_URL,
        "status": "parsed",
    }


def parse_result(html: str, searched_word: str) -> list[dict[str, Any]]:
    """Extract all valid grammatical interpretations from the returned HTML."""
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, Any]] = []
    invalid_cards: list[str] = []
    for header in soup.select(RESULT_CARD_SELECTOR):
        card = header.find_parent("div", class_="tarjeta")
        if card is None:
            continue
        word_node = header.select_one(".accordionWord")
        if word_node and normalize_word(
            word_node.get_text(" ", strip=True)
        ) != normalize_word(searched_word):
            continue
        try:
            records.append(_parse_card(card, searched_word))
        except ResultValidationError as exc:
            invalid_cards.append(str(exc))

    if records:
        return records
    if invalid_cards:
        raise ResultValidationError("; ".join(invalid_cards))
    return []


def search_word(
    page: Page, word: str, timeout_ms: int = RESULT_TIMEOUT_MS
) -> list[dict[str, Any]]:
    """Search one word through the site's verified form and parse its cards."""
    initial_response = page.goto(
        BASE_URL, wait_until="domcontentloaded", timeout=timeout_ms
    )
    if initial_response is not None:
        _check_response_status(initial_response.status)
    page.locator(SEARCH_INPUT_SELECTOR).wait_for(state="visible", timeout=timeout_ms)
    page.locator(SEARCH_INPUT_SELECTOR).fill(_display_word(word))

    with page.expect_response(
        lambda response: (
            response.url.rstrip("/") == BASE_URL.rstrip("/")
            and response.request.method == "POST"
        ),
        timeout=timeout_ms,
    ) as response_info:
        # Let Playwright wait for a form navigation before reading page.content().
        page.locator(SEARCH_BUTTON_SELECTOR).click(timeout=timeout_ms)

    response = response_info.value
    _check_response_status(response.status)

    return parse_result(page.content(), word)


def _check_response_status(status: int) -> None:
    """Stop immediately on access denial, throttling, or another HTTP error."""
    if status in {403, 429}:
        raise ScraperHTTPError(
            f"El sitio respondió HTTP {status}; se detiene el scraper."
        )
    if status >= 400:
        raise ScraperHTTPError(f"El sitio respondió HTTP {status}.")


def scrape_word(word: str, timeout_ms: int = RESULT_TIMEOUT_MS) -> list[dict[str, Any]]:
    """Scrape the site's result for exactly one word and return its interpretations."""
    word = _display_word(word)
    if not word or any(character.isspace() for character in word):
        raise ValueError("Indica una única palabra, sin espacios.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            return search_word(page, word, timeout_ms)
        finally:
            browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta una palabra en Sílaba Tónica TIP."
    )
    parser.add_argument("word", help="La única palabra que se consultará")
    args = parser.parse_args()
    results = scrape_word(args.word)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
