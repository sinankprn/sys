"""Turn a paper's evidence table into (1) a readable evidence table and
(2) a highlighted copy of the PDF.

    python tools/evidence.py papers/paper_01.pdf evidence/paper_01.csv

Input  evidence/paper_XX.csv, one row per data point:
    Section    Overview / Indicators / Limitations & future research
    Field      e.g. "Club sample size", or the indicator name
    Value      the value recorded in organised_extraction.xlsx
    Basis      Stated / Inferred / Not found
    Quote      exact words copied from the paper (blank for Not found)
    Location   where to look, e.g. "p.6, Sample" or "Table 2, p.8"
    Reasoning  why the value follows from the quote (needed for Inferred/Not found)

Output
    evidence/paper_XX.md                 evidence table, with the page each quote was found on
    evidence/paper_XX_highlighted.pdf    every quote highlighted, with a comment naming the field
                                         (yellow = Stated, blue = Inferred), plus a summary first page

A quote that cannot be found in the PDF is NOT highlighted and is marked ✗ in
the table, so misquotes and paraphrases are caught before anyone relies on them.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import pymupdf

COLOURS = {"stated": (1.0, 0.92, 0.23), "inferred": (0.55, 0.78, 1.0)}
FIELDS = ["Section", "Field", "Value", "Basis", "Quote", "Location", "Reasoning"]


def norm_token(t: str) -> str:
    t = unicodedata.normalize("NFKC", t).lower()
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = t.replace("–", "-").replace("—", "-").replace("−", "-")
    # Hyphens are dropped so "self-" + "empowerment" across a line break matches "self-empowerment"
    return re.sub(r"[^\w%€$.,+=<>/]", "", t).strip(".,;:")


def page_words(page):
    """Words on a page in reading order, re-joining words hyphenated across lines."""
    # Natural (stored) order follows the text flow, so two-column pages read
    # column by column; sort=True would interleave the columns line by line.
    words = page.get_text("words")   # x0, y0, x1, y1, word, block, line, wno
    out = []
    for w in words:
        rect, text = pymupdf.Rect(w[:4]), w[4]
        if out and out[-1][0].endswith(("-", "\u00ad")) and (w[5], w[6]) != out[-1][2]:
            prev_text, prev_rects, _ = out[-1]
            out[-1] = (prev_text[:-1] + text, prev_rects + [rect], (w[5], w[6]))
        else:
            out.append((text, [rect], (w[5], w[6])))
    return [(norm_token(t), rects) for t, rects, _ in out if norm_token(t)]


def find_quote(doc, quote: str, page_hint: int | None):
    """Return (page_number, rects) for the first match; the hinted page is searched first."""
    target = [norm_token(t) for t in quote.split() if norm_token(t)]
    if not target:
        return None
    order = list(range(len(doc)))
    if page_hint is not None and 0 <= page_hint < len(doc):
        order.remove(page_hint)
        order.insert(0, page_hint)
    for pno in order:
        words = page_words(doc[pno])
        tokens = [w for w, _ in words]
        n = len(target)
        for i in range(len(tokens) - n + 1):
            if tokens[i:i + n] == target:
                rects = [r for _, rs in words[i:i + n] for r in rs]
                return pno, rects
    return None


def page_hint(location: str, doc) -> int | None:
    """'p.6' in Location means printed page 6. Journals number pages differently
    from the PDF, so try the PDF's page labels first, then the PDF index."""
    m = re.search(r"\bp{1,2}\.?\s*(\d+)", str(location))
    if not m:
        return None
    n = m.group(1)
    for i, page in enumerate(doc):
        if page.get_label() == n:
            return i
    return int(n) - 1


def merge_line_rects(rects):
    """One highlight box per text line instead of one per word."""
    lines = []
    for r in rects:
        for k, line in enumerate(lines):
            if abs(line.y0 - r.y0) < 2 and abs(line.y1 - r.y1) < 2:
                lines[k] = pymupdf.Rect(min(line.x0, r.x0), min(line.y0, r.y0),
                                        max(line.x1, r.x1), max(line.y1, r.y1))
                break
        else:
            lines.append(pymupdf.Rect(r))
    return lines


def main(pdf_path, csv_path):
    pdf_path, csv_path = Path(pdf_path), Path(csv_path)
    ev = pd.read_csv(csv_path, dtype=str).fillna("")
    missing = [c for c in FIELDS if c not in ev.columns]
    if missing:
        sys.exit(f"{csv_path} is missing columns: {missing}")

    doc = pymupdf.open(pdf_path)
    if not any(p.get_text().strip() for p in doc):
        sys.exit("This PDF has no text layer (scanned image). Run OCR first, e.g. ocrmypdf.")

    found_pages, checks = [], []
    for _, r in ev.iterrows():
        basis = r["Basis"].strip().lower()
        if not r["Quote"].strip() or basis.startswith("not found"):
            found_pages.append("")
            checks.append("–")
            continue
        hit = find_quote(doc, r["Quote"], page_hint(r["Location"], doc))
        if hit is None:
            found_pages.append("")
            checks.append("✗ not found")
            continue
        pno, rects = hit
        label = doc[pno].get_label() or str(pno + 1)
        found_pages.append(label if label == str(pno + 1) else f"{label} (PDF p.{pno + 1})")
        checks.append("✓")
        page = doc[pno]                       # keep a reference: annots need a live page
        annot = page.add_highlight_annot(merge_line_rects(rects))
        annot.set_colors(stroke=COLOURS.get(basis.split()[0], COLOURS["stated"]))
        annot.set_info(title=f"{r['Section']}: {r['Field']}",
                       content=f"{r['Field']} = {r['Value']}\nBasis: {r['Basis']}"
                               + (f"\nReasoning: {r['Reasoning']}" if r["Reasoning"] else ""))
        annot.update()

    ev["Found on page"] = found_pages
    ev["Quote check"] = checks

    # Summary page at the front of the highlighted PDF
    summary = doc.new_page(0)
    lines = [f"Evidence summary: {pdf_path.name}", "",
             "Yellow = stated in the paper. Blue = inferred (see the comment for the reasoning).", ""]
    for _, r in ev.iterrows():
        where = f"p.{r['Found on page']}" if r["Found on page"] else ("not found in PDF" if r["Quote check"].startswith("✗") else r["Basis"])
        lines.append(f"[{r['Section']}] {r['Field']}: {r['Value'][:60]}  ->  {where}")
    summary.insert_textbox(pymupdf.Rect(40, 40, 555, 800), "\n".join(lines), fontsize=8)
    out_pdf = csv_path.with_name(csv_path.stem + "_highlighted.pdf")
    doc.save(out_pdf, garbage=3, deflate=True)

    # Markdown evidence table
    def cell(s):
        return str(s).replace("|", "\\|").replace("\n", " ")
    md = [f"# Evidence: {pdf_path.name}", "",
          f"Highlighted copy: `{out_pdf.name}` (first page lists every field). "
          "Quote check: ✓ found and highlighted, ✗ not found in the PDF (fix before use), – no quote.", ""]
    for section, grp in ev.groupby("Section", sort=False):
        md += [f"## {section}", "",
               "| Field | Value | Basis | Quote from paper | Location | Found on page | Check | Reasoning |",
               "|---|---|---|---|---|---|---|---|"]
        for _, r in grp.iterrows():
            q = f"“{cell(r['Quote'])}”" if r["Quote"] else ""
            md.append(f"| {cell(r['Field'])} | {cell(r['Value'])} | {cell(r['Basis'])} | {q} | "
                      f"{cell(r['Location'])} | {cell(r['Found on page'])} | {r['Quote check']} | {cell(r['Reasoning'])} |")
        md.append("")
    out_md = csv_path.with_suffix(".md")
    out_md.write_text("\n".join(md), encoding="utf-8")

    bad = (ev["Quote check"] == "✗ not found").sum()
    print(f"{len(ev)} data points, {(ev['Quote check'] == '✓').sum()} quotes highlighted, {bad} not found")
    print(f"-> {out_md}\n-> {out_pdf}")
    return bad


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(1 if main(*sys.argv[1:]) else 0)
