"""Turn a paper's evidence table into (1) a readable evidence table and
(2) a highlighted copy of the PDF.

    python tools/evidence.py papers/paper_01.pdf evidence/paper_01.csv

Input  evidence/paper_XX.csv, one row per data point:
    Section    Overview / Indicators / Limitations & future research
    Field      e.g. "Club sample size", or the indicator name
    Category   colour category from HIGHLIGHT_COLOURS.md (e.g. "Financial Capacity")
    Value      the value recorded in organised_extraction.xlsx
    Basis      Stated / Inferred / Not found
    Quote      exact words copied from the paper (blank for Not found)
    Location   where to look, e.g. "p.6, Sample" or "Table 2, p.8"
    Reasoning  why the value follows from the quote, citing the CODEBOOK.md rule

Output
    evidence/paper_XX.md                    evidence table, with the page each quote was found on
    highlighted/paper_XX_highlighted.pdf    every quote highlighted in its category colour
                                            (plain = Stated, with wavy underline = Inferred),
                                            a comment on each, and a summary/legend first page

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

ROOT = Path(__file__).resolve().parents[1]
COLOUR_FILE = ROOT / "HIGHLIGHT_COLOURS.md"
HIGHLIGHT_DIR = ROOT / "highlighted"
INFERRED_UNDERLINE = (0.15, 0.15, 0.15)
FIELDS = ["Section", "Field", "Category", "Value", "Basis", "Quote", "Location", "Reasoning"]


def load_colours(path: Path = COLOUR_FILE) -> dict[str, tuple[float, float, float]]:
    """Category -> RGB (0-1), read from the table in HIGHLIGHT_COLOURS.md."""
    colours = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|[^|]*\|\s*`?#([0-9A-Fa-f]{6})`?\s*\|", line)
        if m:
            h = m.group(2)
            colours[m.group(1)] = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    if not colours:
        sys.exit(f"No colours found in {path}")
    return colours


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

    colours = load_colours()
    unknown = sorted(set(ev["Category"]) - set(colours))
    if unknown:
        sys.exit(f"Unknown Category values {unknown}. Use one of: {list(colours)}")

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
        lines = merge_line_rects(rects)
        info = dict(title=f"{r['Category']} | {r['Field']}",
                    content=f"{r['Field']} = {r['Value']}\nBasis: {r['Basis']}"
                            + (f"\nReasoning: {r['Reasoning']}" if r["Reasoning"] else ""))
        annot = page.add_highlight_annot(lines)
        annot.set_colors(stroke=colours[r["Category"]])
        annot.set_info(**info)
        annot.update()
        if basis.startswith("inferred"):
            sq = page.add_squiggly_annot(lines)
            sq.set_colors(stroke=INFERRED_UNDERLINE)
            sq.set_info(**info)
            sq.update()

    ev["Found on page"] = found_pages
    ev["Quote check"] = checks

    # Summary + legend page at the front of the highlighted PDF
    summary = doc.new_page(0)
    y = 40
    summary.insert_text((40, y), f"Evidence summary: {pdf_path.name}", fontsize=12)
    y += 18
    summary.insert_text((40, y), "Colour = category (see legend). Plain highlight = Stated; "
                                 "wavy underline = Inferred. Click a highlight for the reasoning.", fontsize=7.5)
    y += 14
    used = [c for c in colours if c in set(ev["Category"])]
    for k, cat in enumerate(used):          # legend, two columns
        x = 40 + (k % 2) * 260
        yy = y + (k // 2) * 12
        summary.draw_rect(pymupdf.Rect(x, yy - 7, x + 18, yy + 2), color=None, fill=colours[cat])
        summary.insert_text((x + 24, yy), cat, fontsize=7.5)
    y += ((len(used) + 1) // 2) * 12 + 12
    for _, r in ev.iterrows():
        if y > 810:
            summary = doc.new_page(summary.number + 1)
            y = 40
        where = (f"p.{r['Found on page']}" if r["Found on page"]
                 else "QUOTE NOT FOUND" if r["Quote check"].startswith("✗") else r["Basis"])
        summary.draw_rect(pymupdf.Rect(40, y - 7, 52, y + 2), color=None, fill=colours[r["Category"]])
        mark = " (inferred)" if r["Basis"].lower().startswith("inferred") else ""
        summary.insert_text((58, y), f"{r['Field']}: {str(r['Value'])[:70]}{mark}  ->  {where}", fontsize=7.5)
        y += 11
    HIGHLIGHT_DIR.mkdir(exist_ok=True)
    out_pdf = HIGHLIGHT_DIR / (csv_path.stem + "_highlighted.pdf")
    doc.save(out_pdf, garbage=3, deflate=True)

    # Markdown evidence table
    def cell(s):
        return str(s).replace("|", "\\|").replace("\n", " ")
    md = [f"# Evidence: {pdf_path.name}", "",
          f"Highlighted copy: `highlighted/{out_pdf.name}` (first page lists every field). "
          "Colours: see HIGHLIGHT_COLOURS.md. Rules: see CODEBOOK.md. "
          "Quote check: ✓ found and highlighted, ✗ not found in the PDF (fix before use), – no quote.", ""]
    for section, grp in ev.groupby("Section", sort=False):
        md += [f"## {section}", "",
               "| Field | Category | Value | Basis | Quote from paper | Location | Found on page | Check | Reasoning |",
               "|---|---|---|---|---|---|---|---|---|"]
        for _, r in grp.iterrows():
            q = f"“{cell(r['Quote'])}”" if r["Quote"] else ""
            md.append(f"| {cell(r['Field'])} | {cell(r['Category'])} | {cell(r['Value'])} | {cell(r['Basis'])} | {q} | "
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
