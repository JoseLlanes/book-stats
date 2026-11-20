"""Launch the one-word scraper for words in the configured input file."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from typing import Sequence

from openpyxl import Workbook, load_workbook

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORDS_FILE = PROJECT_ROOT / "data" / "palabras_unicas.txt"
DATABASE_FILE = PROJECT_ROOT / "data" / "syllable_database.xlsx"
SCRAPER_SCRIPT = Path(__file__).with_name("syllable_scraper.py")
DELAY_SECONDS = 2 * 60

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def normalize_word(word: str) -> str:
    """Normalize spelling for matching input words against saved results."""
    candidate = word.strip()
    if "Ãƒ" in candidate or "Ã‚" in candidate:
        try:
            candidate = candidate.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return unicodedata.normalize("NFC", candidate).casefold()


def load_words(words_file: Path = WORDS_FILE) -> list[str]:
    """Read non-empty words from the configured UTF-8 text file."""
    unique: dict[str, str] = {}
    for line in Path(words_file).read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if word:
            unique.setdefault(normalize_word(word), word)
    return list(unique.values())


def load_saved_words(database_file: Path = DATABASE_FILE) -> set[str]:
    """Return words already present in the database's `word` column."""
    path = Path(database_file)
    if not path.exists():
        return set()

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = (
            workbook["Sheet1"]
            if "Sheet1" in workbook.sheetnames
            else workbook.worksheets[0]
        )
        headers = {
            str(cell.value).strip(): cell.column for cell in sheet[1] if cell.value
        }
        word_column = headers.get("word")
        if word_column is None:
            return set()
        return {
            normalize_word(str(row[word_column - 1]))
            for row in sheet.iter_rows(min_row=2, values_only=True)
            if row[word_column - 1]
        }
    finally:
        workbook.close()


def save_results(
    records: list[dict[str, object]], database_file: Path = DATABASE_FILE
) -> int:
    """Append scraper records to Sheet1 and return the number of rows added."""
    if not records:
        return 0

    path = Path(database_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(path) if path.exists() else Workbook()
    if "Sheet1" in workbook.sheetnames:
        sheet = workbook["Sheet1"]
    elif workbook.sheetnames == ["Sheet"] and workbook["Sheet"]["A1"].value is None:
        sheet = workbook["Sheet"]
        sheet.title = "Sheet1"
    else:
        sheet = workbook.create_sheet("Sheet1")

    if "results" in workbook.sheetnames:
        del workbook["results"]

    if sheet.max_row == 1 and all(cell.value is None for cell in sheet[1]):
        headers = list(records[0])
        for column, name in enumerate(headers, start=1):
            sheet.cell(row=1, column=column, value=name)
    else:
        headers = [
            str(cell.value) if cell.value is not None else "" for cell in sheet[1]
        ]
        for record in records:
            for name in record:
                if name not in headers:
                    headers.append(name)
                    sheet.cell(row=1, column=len(headers), value=name)

    header_columns = {name: index + 1 for index, name in enumerate(headers) if name}
    for record in records:
        row_number = sheet.max_row + 1
        for name, value in record.items():
            sheet.cell(row=row_number, column=header_columns[name], value=value)

    workbook.save(path)
    workbook.close()
    return len(records)


def run_scraper(word: str, timeout_seconds: int = 90) -> list[dict[str, object]]:
    """Run the one-word scraper as a separate terminal process."""
    completed = subprocess.run(
        [sys.executable, str(SCRAPER_SCRIPT), word],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"El scraper falló para {word!r}: {details}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"El scraper no devolvió JSON válido para {word!r}."
        ) from exc
    if not isinstance(result, list):
        raise RuntimeError(f"El scraper devolvió un formato inesperado para {word!r}.")
    return result


def run_queue(
    words_file: Path = WORDS_FILE,
    database_file: Path = DATABASE_FILE,
    delay_seconds: int = DELAY_SECONDS,
) -> None:
    """Scrape each word absent from the database, pausing between processes."""
    words = load_words(words_file)
    saved_words = load_saved_words(database_file)
    pending = [word for word in words if normalize_word(word) not in saved_words]
    logger.info(
        "%s palabra(s) pendientes de %s en %s", len(pending), len(words), database_file
    )

    for index, word in enumerate(pending):
        logger.info("Consultando %r (%s/%s)", word, index + 1, len(pending))
        try:
            records = run_scraper(word)
            if records:
                save_results(records, database_file)
                saved_words.add(normalize_word(word))
                logger.info(
                    "Guardadas %s interpretación(es) para %r", len(records), word
                )
            else:
                logger.warning(
                    "No se encontraron resultados para %r; se podrá reintentar", word
                )
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            logger.error("%s", exc)
            if "HTTP 403" in str(exc) or "HTTP 429" in str(exc):
                logger.error(
                    "El sitio bloqueó o limitó la consulta; se detiene la cola."
                )
                break

        if index + 1 < len(pending) and delay_seconds:
            logger.info(
                "Esperando %s segundos antes de la siguiente consulta", delay_seconds
            )
            time.sleep(delay_seconds)


def run_single_word(word: str, database_file: Path = DATABASE_FILE) -> bool:
    """Scrape and save one word unless it is already in the database."""
    word = word.strip()
    if not word or any(character.isspace() for character in word):
        raise ValueError("Indica exactamente una palabra, sin espacios.")

    if normalize_word(word) in load_saved_words(database_file):
        logger.info("%r ya está en %s; no se consulta de nuevo", word, database_file)
        return True

    records = run_scraper(word)
    if not records:
        logger.warning("No se encontraron resultados para %r", word)
        return False

    save_results(records, database_file)
    logger.info("Guardadas %s interpretación(es) para %r", len(records), word)
    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Consulta una palabra o procesa la lista configurada."
    )
    parser.add_argument(
        "word",
        nargs="?",
        help="consulta y guarda solo esta palabra; sin ella procesa la lista completa",
    )
    parser.add_argument(
        "--words-file",
        type=Path,
        default=WORDS_FILE,
        help=f"lista de palabras (por defecto: {WORDS_FILE})",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DATABASE_FILE,
        help=f"Excel de resultados (por defecto: {DATABASE_FILE})",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=DELAY_SECONDS,
        help=f"segundos entre ejecuciones (por defecto: {DELAY_SECONDS})",
    )
    args = parser.parse_args(argv)
    if args.delay < 0:
        parser.error("--delay no puede ser negativo")
    if args.word is not None:
        try:
            return 0 if run_single_word(args.word, args.database) else 1
        except (RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
            logger.error("%s", exc)
            return 1
    run_queue(args.words_file, args.database, args.delay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
