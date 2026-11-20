"""Build, for one paper: a checklist, an evidence table, and a highlighted PDF.

    python tools/evidence.py papers/paper_01.pdf evidence/paper_01.csv

Input  evidence/paper_XX.csv, one row per piece of evidence:
    Tag        item number shown in the checklist and beside the highlight, e.g. O12a
               (column code from CODEBOOK.md + letter), L5-Lim1, I-V3
    Section    Overview / Indicators / Limitations & future research
    Field      spreadsheet column or item, e.g. "Club sample size"
    Category   colour category from HIGHLIGHT_COLOURS.md
    Value      the value currently in organised_extraction.xlsx
    Suggested  proposed new value (blank if the value matches)
    Status     Matches / Suggest change / Decision needed
    Basis      Stated / Inferred / Not found
    Quote      exact words copied from the paper (blank for Not found)
    Location   where to look, e.g. "PDF p.6, Method" or "Table 2, PDF p.8"
    Reasoning  why, citing the CODEBOOK.md rule

Output
    checklists/paper_XX_checklist.xlsx      one row per tag, with columns to tick off
    evidence/paper_XX.md                    the same evidence as a readable table
    highlighted/paper_XX_highlighted.pdf    every quote highlighted in its category colour
                                            (plain = Stated, wavy underline = Inferred),
                                            its tag printed in the margin, a comment on each
                                            highlight, and a legend/index first page

A quote that cannot be found word for word in the PDF is not highlighted and is
marked "NOT FOUND", so paraphrases and misquotes are caught.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import pymupdf
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
COLOUR_FILE = ROOT / "HIGHLIGHT_COLOURS.md"
HIGHLIGHT_DIR = ROOT / "highlighted"
CHECKLIST_DIR = ROOT / "checklists"
INFERRED_UNDERLINE = (0.15, 0.15, 0.15)
FIELDS = ["Tag", "Section", "Field", "Category", "Value", "Suggested", "Status",
          "Basis", "Quote", "Location", "Reasoning"]
STATUS_FILL = {"Matches": "D9EAD3", "Suggest change": "FCE5B0", "Decision needed": "F4C7C3"}


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


def hexcol(rgb):
    return "".join(f"{round(c * 255):02X}" for c in rgb)


def text_bounds(page):
    """Left and right edges of the text block on a page (the page margins)."""
    xs = [(w[0], w[2]) for w in page.get_text("words")]
    if not xs:
        return 50, page.rect.width - 50
    return min(x0 for x0, _ in xs), max(x1 for _, x1 in xs)


def place_tag(page, line_rect, used, bounds):
    """Rectangle in the page margin (left margin for the left half of the page,
    right margin otherwise), level with the highlighted line; moved down if it
    would overlap an earlier tag."""
    w, h = 32, 9
    left, right = bounds
    if line_rect.x0 < page.rect.width / 2:
        x0 = max(1, left - w - 3)
    else:
        x0 = min(page.rect.width - w - 1, right + 3)
    r = pymupdf.Rect(x0, line_rect.y0, x0 + w, line_rect.y0 + h)
    while any(r.intersects(u) for u in used):
        r += (0, h + 1, 0, h + 1)
    used.append(r)
    return r


def main(pdf_path, csv_path):
    pdf_path, csv_path = Path(pdf_path), Path(csv_path)
    ev = pd.read_csv(csv_path, dtype=str).fillna("")
    missing = [c for c in FIELDS if c not in ev.columns]
    if missing:
        sys.exit(f"{csv_path} is missing columns: {missing}")
    if ev["Tag"].duplicated().any():
        sys.exit(f"Duplicate tags: {sorted(ev.loc[ev['Tag'].duplicated(), 'Tag'])}")
    colours = load_colours()
    unknown = sorted(set(ev["Category"]) - set(colours))
    if unknown:
        sys.exit(f"Unknown Category values {unknown}. Use one of: {list(colours)}")

    doc = pymupdf.open(pdf_path)
    if not any(p.get_text().strip() for p in doc):
        sys.exit("This PDF has no text layer (scanned image). Run OCR first, e.g. ocrmypdf.")

    found_pages, checks, used_tag_space = [], [], {}
    for _, r in ev.iterrows():
        basis = r["Basis"].strip().lower()
        if not r["Quote"].strip() or basis.startswith("not found"):
            found_pages.append("")
            checks.append("No quote")
            continue
        hit = find_quote(doc, r["Quote"], page_hint(r["Location"], doc))
        if hit is None:
            found_pages.append("")
            checks.append("NOT FOUND")
            continue
        pno, rects = hit
        label = doc[pno].get_label() or str(pno + 1)
        found_pages.append(label if label == str(pno + 1) else f"{label} (PDF p.{pno + 1})")
        checks.append("Highlighted")
        page = doc[pno]                       # keep a reference: annots need a live page
        lines = merge_line_rects(rects)
        colour = colours[r["Category"]]
        info = dict(title=f"{r['Tag']} | {r['Field']}",
                    content=f"[{r['Tag']}] {r['Field']}\nIn spreadsheet: {r['Value']}"
                            + (f"\nSuggested: {r['Suggested']}" if r["Suggested"] else "")
                            + f"\nStatus: {r['Status']}\nBasis: {r['Basis']}"
                            + (f"\nReasoning: {r['Reasoning']}" if r["Reasoning"] else ""))
        annot = page.add_highlight_annot(lines)
        annot.set_colors(stroke=colour)
        annot.set_info(**info)
        annot.update()
        if basis.startswith("inferred"):
            sq = page.add_squiggly_annot(lines)
            sq.set_colors(stroke=INFERRED_UNDERLINE)
            sq.set_info(**info)
            sq.update()
        tag_rect = place_tag(page, lines[0], used_tag_space.setdefault(pno, []), text_bounds(page))
        tag = page.add_freetext_annot(tag_rect, r["Tag"], fontsize=6.5, text_color=(0, 0, 0),
                                      fill_color=colour,
                                      align=1)
        tag.set_info(title=info["title"])   # content would replace the tag text
        tag.update()

    ev["Page"] = found_pages
    ev["Quote check"] = checks

    # ---- Legend + index page at the front of the highlighted PDF
    summary = doc.new_page(0)
    y = 40
    summary.insert_text((40, y), f"Evidence index: {pdf_path.name}", fontsize=12)
    y += 16
    for txt in ["Each highlight has a tag in the margin (e.g. O12a) matching the checklist row.",
                "Colour = category. Plain highlight = Stated. Wavy underline = Inferred. "
                "Click a highlight or tag for the reasoning.",
                "Tag codes = spreadsheet columns (CODEBOOK.md). Page numbers below are PDF pages "
                "of the original paper (this index page excluded)."]:
        summary.insert_text((40, y), txt, fontsize=7.5)
        y += 10
    y += 4
    used = [c for c in colours if c in set(ev["Category"])]
    for k, cat in enumerate(used):
        x = 40 + (k % 2) * 260
        yy = y + (k // 2) * 12
        summary.draw_rect(pymupdf.Rect(x, yy - 7, x + 18, yy + 2), color=None, fill=colours[cat])
        summary.insert_text((x + 24, yy), cat, fontsize=7.5)
    y += ((len(used) + 1) // 2) * 12 + 12
    for _, r in ev.iterrows():
        if y > 810:
            summary = doc.new_page(summary.number + 1)
            y = 40
        where = f"p.{r['Page']}" if r["Page"] else r["Quote check"].lower()
        summary.draw_rect(pymupdf.Rect(40, y - 7, 70, y + 2), color=None, fill=colours[r["Category"]])
        summary.insert_text((43, y), r["Tag"], fontsize=6.5)
        flag = "" if r["Status"] == "Matches" else f"  [{r['Status'].upper()}]"
        summary.insert_text((76, y), f"{r['Field']}: {str(r['Value'])[:60]}  ->  {where}{flag}", fontsize=7.5)
        y += 11
    HIGHLIGHT_DIR.mkdir(exist_ok=True)
    out_pdf = HIGHLIGHT_DIR / (csv_path.stem + "_highlighted.pdf")
    doc.save(out_pdf, garbage=3, deflate=True)

    # ---- Checklist workbook
    CHECKLIST_DIR.mkdir(exist_ok=True)
    out_xlsx = CHECKLIST_DIR / (csv_path.stem + "_checklist.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "Checklist"
    hdr = ["Tag", "Field", "Category", "In spreadsheet", "Suggested", "Status", "Basis", "Page",
           "Quote from paper", "Reasoning", "Highlight checked", "Your verdict", "Your note"]
    ws.append(hdr)
    for _, r in ev.iterrows():
        ws.append([r["Tag"], r["Field"], r["Category"], r["Value"], r["Suggested"], r["Status"],
                   r["Basis"], r["Page"] or r["Quote check"], r["Quote"], r["Reasoning"], "", "", ""])
        row = ws.max_row
        ws.cell(row, 1).fill = PatternFill("solid", fgColor=hexcol(colours[r["Category"]]))
        ws.cell(row, 3).fill = PatternFill("solid", fgColor=hexcol(colours[r["Category"]]))
        if r["Status"] in STATUS_FILL:
            ws.cell(row, 6).fill = PatternFill("solid", fgColor=STATUS_FILL[r["Status"]])
        for c in ws[row]:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1C5CAB")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for col, wdt in zip("ABCDEFGHIJKLM", [8, 20, 18, 28, 28, 15, 9, 7, 50, 50, 11, 14, 30]):
        ws.column_dimensions[col].width = wdt
    n = ws.max_row
    dv1 = DataValidation(type="list", formula1='"Yes,No"', allow_blank=True)
    dv2 = DataValidation(type="list", formula1='"Yes,No,Unsure"', allow_blank=True)
    ws.add_data_validation(dv1)
    ws.add_data_validation(dv2)
    dv1.add(f"K2:K{n}")
    dv2.add(f"L2:L{n}")
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:M{n}"
    guide = wb.create_sheet("How to use")
    for i, line in enumerate([
        f"Checklist for {pdf_path.name}",
        "",
        "1. Open the highlighted PDF (highlighted folder) next to this sheet.",
        "2. For each row, find the tag in the PDF margin (e.g. O12a). Page = PDF page of the original paper.",
        "3. Read the highlighted text in context. 'Highlight checked' = Yes once you've looked at it.",
        "4. 'Your verdict': Yes = you agree (with the Suggested value, if there is one; otherwise with the value).",
        "   No = you disagree; say why or what it should be in 'Your note'. Unsure = discuss.",
        "5. Rows with Status 'Suggest change' or 'Decision needed' are the ones that change the data.",
        "   When done, send the file back; tools/apply_checklist.py writes agreed changes and logs everything.",
        "6. Tags start with the spreadsheet column code (O = Overview, I = Indicators, L = Limitations).",
        "   Definitions and rules for each code are in CODEBOOK.md; colours in HIGHLIGHT_COLOURS.md.",
    ], 1):
        guide.cell(i, 1, line)
    guide["A1"].font = Font(bold=True, size=13)
    guide.column_dimensions["A"].width = 110
    wb.save(out_xlsx)

    # ---- Markdown evidence table
    def cell(s):
        return str(s).replace("|", "\\|").replace("\n", " ")
    md = [f"# Evidence: {pdf_path.name}", "",
          f"Checklist: `checklists/{out_xlsx.name}`. Highlighted copy: `highlighted/{out_pdf.name}`. "
          "Tags match the margin tags in the PDF and the column codes in CODEBOOK.md. "
          "Colours: HIGHLIGHT_COLOURS.md.", ""]
    for section, grp in ev.groupby("Section", sort=False):
        md += [f"## {section}", "",
               "| Tag | Field | In spreadsheet | Suggested | Status | Basis | Quote from paper | Page | Reasoning |",
               "|---|---|---|---|---|---|---|---|---|"]
        for _, r in grp.iterrows():
            q = f"“{cell(r['Quote'])}”" if r["Quote"] else ""
            md.append(f"| {r['Tag']} | {cell(r['Field'])} | {cell(r['Value'])} | {cell(r['Suggested'])} | "
                      f"{r['Status']} | {r['Basis']} | {q} | {r['Page'] or r['Quote check']} | {cell(r['Reasoning'])} |")
        md.append("")
    out_md = csv_path.with_suffix(".md")
    out_md.write_text("\n".join(md), encoding="utf-8")

    bad = (ev["Quote check"] == "NOT FOUND").sum()
    print(f"{len(ev)} items, {(ev['Quote check'] == 'Highlighted').sum()} highlighted, {bad} quotes not found; "
          f"{(ev['Status'] != 'Matches').sum()} need a decision")
    print(f"-> {out_xlsx}\n-> {out_md}\n-> {out_pdf}")
    return bad


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(1 if main(*sys.argv[1:]) else 0)
