# Systematic review: organisational capacity in community sport clubs

| File | What it is |
|---|---|
| **`organised_extraction.xlsx`** | **Primary dataset.** Overview (one row per paper), Indicators (quantitative), and Limitations & future research |
| `FINDINGS.md` | Key findings, insights, research gaps, and data points to check |
| `CODEBOOK.md` | What every column means, allowed values and decision rules, based on Hall et al.'s (2003) model. Paper checks cite these rules |
| `HIGHLIGHT_COLOURS.md` | Colour for each category of evidence in the highlighted PDFs (the tool reads this file) |
| `evidence/` | One evidence table per verified paper (`paper_XX.md`): every value with the quote and page it came from |
| `highlighted/` | Highlighted copy of each checked paper (kept local; not committed) |
| `tools/evidence.py` | Builds the evidence table and the highlighted PDF from `evidence/paper_XX.csv` |
| `archive/` | Everything else: the raw extraction workbook, the Python pipeline that built the first organised version, its summary tables, figures, quality checks and review workflow. See `archive/README.md` |

Edit `organised_extraction.xlsx` directly from now on. The archived scripts read
the raw workbook in `archive/data/raw/`, not this file, so re-running them will not
pick up edits made here.

## Verifying a paper against its PDF

1. Put the paper in `papers/` (e.g. `papers/paper_01.pdf`). PDFs are never committed.
2. Record each data point in `evidence/paper_01.csv`, with columns Section, Field,
   Category (from `HIGHLIGHT_COLOURS.md`), Value, Basis (Stated / Inferred / Not found),
   Quote (exact words from the paper), Location and Reasoning (citing the `CODEBOOK.md` rule).
3. Run:

   ```bash
   pip install -r tools/requirements.txt
   python tools/evidence.py papers/paper_01.pdf evidence/paper_01.csv
   ```

   This writes `evidence/paper_01.md`, with the page each quote was found on, and
   `highlighted/paper_01_highlighted.pdf`. Each quote is highlighted in its category
   colour, with a wavy underline when the value is inferred. Clicking a highlight shows
   the reasoning, and the first page has a colour legend and an index of every field.
   A quote that isn't found in the PDF is marked ✗ and not highlighted.
