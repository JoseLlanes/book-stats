# Book Stats: Literary Analytics

Book Stats analyzes the vocabulary and structure of text based PDFs. Upload a PDF to view page and word counts, lexical diversity, word-length statistics, per-page word-length trends, and estimated chapter lengths. The uploaded file is processed in memory and is not stored by the application.

## Live app

The app is available at [my-book-stats.streamlit.app](https://my-book-stats.streamlit.app/).

## Run locally

Use Python 3.10 or later. From the project directory, create and activate a virtual environment, then install the dependencies and start Streamlit:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, upload a PDF, and select **Analyze Book**.

## Syllable scraper

The `notebooks/scrapping/syllable_scraper.py` script queries Sílaba Tónica TIP
for one word and prints the result as JSON. Pass the word on the command line:

```bash
python notebooks/scrapping/syllable_scraper.py quisiera
```

The same operation is available as `scrape_word("quisiera")` when importing
the script. Each run makes a single word lookup and does not read or write a
word list or workbook.

The `notebooks/scrapping/syllable_scraper_cli.py` launcher reads words from
`data/palabras_unicas.txt` and saves results to
`data/syllable_database.xlsx`. It skips words already present in the database
and launches the one-word scraper as a separate process, waiting two minutes
between searches. Run the full queue with:

```bash
python notebooks/scrapping/syllable_scraper_cli.py
```

También puedes pasar una palabra para consultarla y guardarla de forma
individual (si ya está en el Excel, se omite):

```bash
python notebooks/scrapping/syllable_scraper_cli.py desespera
```

## Deploy on Streamlit Community Cloud

1. Push this project to a GitHub repository. Keep local virtual environments and manuscript PDFs out of the repository.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and select **Create app**.
3. Choose the repository and branch, set the main file path to `app.py`, and deploy.
4. Community Cloud installs the packages listed in `requirements.txt`.

## Analysis notes

- Word counts use Unicode letter sequences, allowing accented Spanish and other alphabetic text. Apostrophes and hyphens inside words are retained; numbers and standalone punctuation are not counted.
- TTR is unique case-insensitive words divided by total words. Word length is measured in Python Unicode characters.
- Standard deviations are population standard deviations. Empty pages count as zero words in the per-page statistics.
- Chapter page totals are estimates: pages are assigned to the most recently detected `CAPÍTULO` or `CHAPTER` heading, and pages before the first heading are excluded. A page containing multiple headings is assigned to the first heading found.
- Scanned image-only PDFs require OCR and currently produce a no-text message.
