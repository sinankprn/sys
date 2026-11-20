# Systematic review: organisational capacity in community sport clubs

| File | What it is |
|---|---|
| **`organised_extraction.xlsx`** | **Primary dataset.** Overview (one row per paper), Indicators (quantitative), and Limitations & future research |
| `FINDINGS.md` | Key findings, insights, research gaps, and data points to check |
| `evidence/` | One evidence table per verified paper (`paper_XX.md`): every value with the quote and page it came from |
| `tools/evidence.py` | Builds the evidence table and a highlighted copy of the PDF from `evidence/paper_XX.csv` |
| `archive/` | Everything else: the raw extraction workbook, the Python pipeline that built the first organised version, its summary tables, figures, quality checks and review workflow. See `archive/README.md` |

Edit `organised_extraction.xlsx` directly from now on. The archived scripts read
the raw workbook in `archive/data/raw/`, not this file, so re-running them will not
pick up edits made here.

## Verifying a paper against its PDF

1. Put the paper in `papers/` (e.g. `papers/paper_01.pdf`). PDFs are never committed.
2. Record each data point in `evidence/paper_01.csv`, with columns Section, Field, Value,
   Basis (Stated / Inferred / Not found), Quote (exact words from the paper), Location
   and Reasoning.
3. Run:

   ```bash
   pip install -r tools/requirements.txt
   python tools/evidence.py papers/paper_01.pdf evidence/paper_01.csv
   ```

   This writes `evidence/paper_01.md`, with the page each quote was found on, and
   `evidence/paper_01_highlighted.pdf`. Its first page lists every field, and each
   quote is highlighted: yellow for stated, blue for inferred, with the reasoning in
   the comment. A quote that isn't found in the PDF is marked ✗ and not highlighted.
