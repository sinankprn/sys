# Systematic review – data extraction pipeline

Python scripts that organise and summarise the extraction workbook on
**organisational capacity in community sport clubs**, check it for missing and
inconsistent data, and support re-reviewing every paper.

The raw workbook (`data/raw/extraction.xlsx`) is **never modified**. Corrections
from re-review are logged to `data/corrections/*.csv` and applied on top each
time the scripts run, so every change has a reviewer, page reference and date.

## Setup

```bash
pip install -r requirements.txt
```

## Run everything

```bash
python scripts/run_all.py
```

| Script | Answers | Main outputs |
|---|---|---|
| `00_organise_extraction.py` | A cleaner copy of the extraction | `output/organised_extraction.xlsx` (Overview, one tab per section, Indicators, Verification) |
| `01_publication.py` | Publications by year, authors, countries, sport, journal | `output/tables/01_publication.xlsx`, `output/figures/01_*.png` |
| `02_study_design.py` | Quantitative vs qualitative vs mixed, longitudinal vs cross-sectional, sample sizes, respondents, data collection | `02_study_design.xlsx`, `02_*.png` |
| `03_capacity.py` | Which dimensions received attention, how they were measured, what was looked at (indicators), capacity as outcome vs predictor, critical elements | `03_capacity.xlsx`, `03_*.png` |
| `04_models.py` | Statistical models employed (grouped into families), by period, per paper | `04_models.xlsx`, `04_*.png` |
| `05_quality_checks.py` | Missing, inconsistent and unverified data; per-paper re-review priority | `05_quality_checks.xlsx` |
| `06_make_review_workbook.py` | Builds a re-review workbook | `output/review/review_<name>.xlsx` |
| `07_apply_review.py` | Logs decisions from a completed review workbook | `data/corrections/corrections.csv`, `verifications.csv` |
| `08_agreement.py` | Agreement between two independent reviewers | `output/tables/08_agreement.xlsx` |

How free text is grouped into categories (model families, respondent types,
critical-element keywords, data-collection methods) is set in
`sysreview/config.py`. To change a coding decision, edit it there.

## Re-reviewing every paper

```bash
# 1. See what is missing or inconsistent, and which papers to review first
python scripts/05_quality_checks.py            # add --crossref on a machine with internet

# 2. Make a review workbook (all papers, or a batch)
python scripts/06_make_review_workbook.py --reviewer SK --papers 1-10

# 3. In Excel: for each row, pick a Decision, type any corrected value, record the page
# 4. Log the decisions and rebuild everything
python scripts/07_apply_review.py output/review/review_SK.xlsx
python scripts/run_all.py
```

Options:
- `--unverified-only` lists only fields not yet ticked, plus any flagged fields.
- `--blind` hides the current values so a second reviewer extracts independently. Compare the two files with `08_agreement.py`.

### Suggested approach

1. **Crossref check first (automatic).** `--crossref` compares authors, title,
   year and journal with the DOI's Crossref metadata, which settles most
   bibliographic fields without opening a PDF. Decide one rule for the year
   (online-first or print) and apply it to every paper.
2. **Work in priority order.** The *Paper priority* tab ranks papers by
   flagged issues and unticked fields. Papers that have never been verified come first.
3. **Re-read by section, not by column.** For each paper, read the Methods
   section once and complete all Sample and Design rows. Then read the
   Results/Tables and complete the Capacity and Modelling rows.
4. **Record a page or table for every value.** This makes later queries
   and disagreements quick to settle, and gives an audit trail for the write-up.
5. **Second reviewer on a sample.** A second person re-extracts 20–30% of papers
   blind (`--blind`), or all papers for the key categorical fields. Report the
   percentage agreement and Cohen's kappa from `08_agreement.py`, and resolve
   disagreements by discussion. This is standard practice (PRISMA 2020, item 9).
6. **Fix structural gaps alongside the re-read.** The per-dimension
   IV columns are blank for most quantitative papers because the detail sits in
   *Independent Variables*. Fill them, or drop them and rely on the parsed *Indicators* table.
   Also record a **Dataset ID** for papers that share one sample (e.g. the
   North Rhine-Westphalia club/member survey) so samples are not double counted.
7. **Lock the coding frame.** Before re-reading, agree definitions for every
   categorical field (e.g. when a dimension counts as "examined", or what
   "Partly" means for critical elements), so both readers code the same way.
