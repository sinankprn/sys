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

Optional input  evidence/paper_XX_indicators.csv, one row per variable (quantitative papers):
    Tag, Indicator, Role, Suggested role, Dimension, Suggested dimension, Definition,
    Suggested definition, Measure type, Suggested measure type, Status, Basis, Quote,
    Location, Reasoning. A Suggested value of "?" marks an open question.

Output
    checklists/paper_XX_checklist.xlsx      sheets mirroring the spreadsheet tabs (Overview,
                                            Indicators with one row per variable, Limitations)
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


IND_FIELDS = ["Tag", "Indicator", "Role", "Suggested role", "Dimension", "Suggested dimension",
              "Definition", "Suggested definition", "Measure type", "Suggested measure type",
              "Status", "Basis", "Quote", "Location", "Reasoning"]
IND_ATTRS = [("Role", "I3"), ("Dimension", "I4"), ("Definition", "I6"), ("Measure type", "I7")]
AMBER, RED = "FCE5B0", "F4C7C3"
ROLES = ["Outcome (DV)", "Predictor (IV)", "Control", "Descriptive only"]   # CODEBOOK.md I3, in this order


ROLE_DEFINITIONS = [   # keep in step with CODEBOOK.md section 3.1
    ["Outcome (DV)", "The variable an analysis tries to explain, or the measure it compares across groups or time points.",
     "Called dependent variable or outcome. In a group comparison (ANOVA, t-test, chi-square, Mann-Whitney) it is the measure compared.",
     "Paper 2: management capacity compared across club-size groups."],
    ["Predictor (IV)", "A variable used to explain the outcome, or that defines the groups being compared, whose effect the authors interpret.",
     "Called independent variable, predictor, determinant; linked to a hypothesis.",
     "Paper 2: club size (the four ANOVA groups). Paper 7: programme participation."],
    ["Control", "Included only to adjust for differences between clubs or to match groups; its effect is not interpreted.",
     "Called control variable or covariate; 'controlling for'. Includes matching variables.",
     "Community size, region dummies, sport type, survey year."],
    ["Descriptive only", "Reported but not used in any model or group-comparison test.",
     "Appears only in descriptive tables, correlations or factor/scale analysis.",
     "Paper 9: all variables. Paper 4: club age."],
]


def role_problems(value: str) -> str:
    """'' if the value is valid: allowed roles, separated by '; ', in ROLES order, no repeats."""
    if value in ("", "?"):
        return ""
    parts = [p.strip() for p in value.split(";")]
    if any(p not in ROLES for p in parts):
        return f"'{value}' has a role outside {ROLES}"
    order = [ROLES.index(p) for p in parts]
    if order != sorted(set(order)):
        return f"'{value}' must list roles once each, in the order {ROLES}"
    return ""


def shown(current, suggested):
    """Cell text: the current value, or 'current → suggested' when a change is proposed."""
    if not suggested:
        return current
    if suggested == "?":
        return f"{current}  (?)"
    return f"{current}  →  {suggested}"


def indicator_items(ind, colours):
    """Turn indicator rows into highlight items (one per variable)."""
    rows = []
    for _, r in ind.iterrows():
        dim = r["Suggested dimension"] if r["Suggested dimension"] not in ("", "?") else r["Dimension"]
        cat = dim if dim in colours else "Not capacity"
        changes = [f"{a}: {shown(r[a], r['Suggested ' + a.lower()])}" for a, _ in IND_ATTRS
                   if r["Suggested " + a.lower()]]
        rows.append({"Tag": r["Tag"], "Section": "Indicators", "Field": r["Indicator"], "Category": cat,
                     "Value": f"{r['Role']} | {r['Dimension']} | {r['Measure type']}",
                     "Suggested": "; ".join(changes), "Status": r["Status"], "Basis": r["Basis"],
                     "Quote": r["Quote"], "Location": r["Location"], "Reasoning": r["Reasoning"]})
    return pd.DataFrame(rows, columns=FIELDS)


def style_header(ws):
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1C5CAB")
        c.alignment = Alignment(wrap_text=True, vertical="top")


def add_dropdowns(ws, col_checked, col_verdict, first, last):
    dv1 = DataValidation(type="list", formula1='"Yes,No"', allow_blank=True)
    dv2 = DataValidation(type="list", formula1='"Yes,No,Unsure"', allow_blank=True)
    ws.add_data_validation(dv1)
    ws.add_data_validation(dv2)
    dv1.add(f"{col_checked}{first}:{col_checked}{last}")
    dv2.add(f"{col_verdict}{first}:{col_verdict}{last}")


def simple_sheet(wb, title, rows, colours):
    """Overview / Limitations sheet: one row per tag."""
    ws = wb.create_sheet(title)
    ws.append(["Tag", "Field", "In spreadsheet", "Suggested", "Status", "Basis", "Page",
               "Quote from paper", "Reasoning", "Highlight checked", "Your verdict", "Your note"])
    for _, r in rows.iterrows():
        ws.append([r["Tag"], r["Field"], r["Value"], r["Suggested"], r["Status"], r["Basis"],
                   r["Page"] or r["Quote check"], r["Quote"], r["Reasoning"], "", "", ""])
        n = ws.max_row
        ws.cell(n, 1).fill = PatternFill("solid", fgColor=hexcol(colours[r["Category"]]))
        if r["Status"] in STATUS_FILL:
            ws.cell(n, 5).fill = PatternFill("solid", fgColor=STATUS_FILL[r["Status"]])
        if r["Suggested"]:
            ws.cell(n, 4).fill = PatternFill("solid", fgColor=AMBER)
        for c in ws[n]:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    style_header(ws)
    for col, wdt in zip("ABCDEFGHIJKL", [9, 22, 30, 30, 15, 9, 13, 50, 50, 11, 12, 30]):
        ws.column_dimensions[col].width = wdt
    add_dropdowns(ws, "J", "K", 2, max(ws.max_row, 2))
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:L{ws.max_row}"
    return ws


def indicator_sheet(wb, ind, shared, colours):
    """One row per variable, mirroring the spreadsheet's Indicators tab."""
    ws = wb.create_sheet("Indicators")
    ws.append(["Tag", "I3 Role", "I4 Dimension", "I5 Indicator", "I6 Definition", "I7 Measure type",
               "Status", "Page", "Quote from paper", "Reasoning", "Highlight checked", "Your verdict", "Your note"])
    for _, r in ind.iterrows():
        role, dim_c, defi, meas = [shown(r[a], r["Suggested " + a.lower()]) for a, _ in IND_ATTRS]
        ws.append([r["Tag"], role, dim_c, r["Indicator"], defi, meas, r["Status"],
                   r["Page"] or r["Quote check"], r["Quote"], r["Reasoning"], "", "", ""])
        n = ws.max_row
        dim = r["Suggested dimension"] if r["Suggested dimension"] not in ("", "?") else r["Dimension"]
        ws.cell(n, 1).fill = PatternFill("solid", fgColor=hexcol(colours.get(dim, colours["Not capacity"])))
        for a, col in [("Role", 2), ("Dimension", 3), ("Definition", 5), ("Measure type", 6)]:
            sug = r["Suggested " + a.lower()]
            if sug:
                ws.cell(n, col).fill = PatternFill("solid", fgColor=RED if sug == "?" else AMBER)
        if r["Status"] in STATUS_FILL:
            ws.cell(n, 7).fill = PatternFill("solid", fgColor=STATUS_FILL[r["Status"]])
        for c in ws[n]:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    last_var = ws.max_row
    style_header(ws)
    if len(shared):
        ws.append([])
        ws.append(["Evidence that applies to several variables"])
        ws.cell(ws.max_row, 1).font = Font(bold=True)
        for _, r in shared.iterrows():
            ws.append([r["Tag"], "", "", r["Field"], "", "", r["Status"], r["Page"] or r["Quote check"],
                       r["Quote"], r["Reasoning"], "", "", ""])
            n = ws.max_row
            ws.cell(n, 1).fill = PatternFill("solid", fgColor=hexcol(colours[r["Category"]]))
            for c in ws[n]:
                c.alignment = Alignment(wrap_text=True, vertical="top")
    for col, wdt in zip("ABCDEFGHIJKLM", [8, 24, 26, 26, 40, 20, 14, 13, 45, 45, 11, 12, 28]):
        ws.column_dimensions[col].width = wdt
    add_dropdowns(ws, "K", "L", 2, ws.max_row)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:M{last_var}"
    return ws


def main(pdf_path, csv_path):
    pdf_path, csv_path = Path(pdf_path), Path(csv_path)
    ev = pd.read_csv(csv_path, dtype=str).fillna("")
    missing = [c for c in FIELDS if c not in ev.columns]
    if missing:
        sys.exit(f"{csv_path} is missing columns: {missing}")
    colours = load_colours()
    ind_path = csv_path.with_name(csv_path.stem + "_indicators.csv")
    ind = pd.read_csv(ind_path, dtype=str).fillna("") if ind_path.exists() else pd.DataFrame(columns=IND_FIELDS)
    missing = [c for c in IND_FIELDS if c not in ind.columns]
    if missing:
        sys.exit(f"{ind_path} is missing columns: {missing}")
    bad_roles = sorted({role_problems(v) for v in list(ind["Role"]) + list(ind["Suggested role"])} - {""})
    if bad_roles:
        sys.exit("Role values break CODEBOOK.md I3: " + "; ".join(bad_roles))
    items = pd.concat([ev, indicator_items(ind, colours)], ignore_index=True)
    if items["Tag"].duplicated().any():
        sys.exit(f"Duplicate tags: {sorted(items.loc[items['Tag'].duplicated(), 'Tag'])}")
    unknown = sorted(set(items["Category"]) - set(colours))
    if unknown:
        sys.exit(f"Unknown Category values {unknown}. Use one of: {list(colours)}")

    doc = pymupdf.open(pdf_path)
    if not any(p.get_text().strip() for p in doc):
        sys.exit("This PDF has no text layer (scanned image). Run OCR first, e.g. ocrmypdf.")

    found_pages, checks, used_tag_space = [], [], {}
    for _, r in items.iterrows():
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
                                      fill_color=colour, align=1)
        tag.set_info(title=info["title"])   # content would replace the tag text
        tag.update()

    items["Page"] = found_pages
    items["Quote check"] = checks
    pages = dict(zip(items["Tag"], zip(items["Page"], items["Quote check"])))
    ev["Page"] = [pages[t][0] for t in ev["Tag"]]
    ev["Quote check"] = [pages[t][1] for t in ev["Tag"]]
    ind["Page"] = [pages[t][0] for t in ind["Tag"]]
    ind["Quote check"] = [pages[t][1] for t in ind["Tag"]]

    # ---- Legend + index page at the front of the highlighted PDF
    summary = doc.new_page(0)
    y = 40
    summary.insert_text((40, y), f"Evidence index: {pdf_path.name}", fontsize=12)
    y += 16
    for txt in ["Each highlight has a tag in the margin (e.g. O12a, I-V3) matching a row in the checklist.",
                "Colour = category. Plain highlight = Stated. Wavy underline = Inferred. "
                "Click a highlight or tag for the reasoning.",
                "Tag codes = spreadsheet columns (CODEBOOK.md). I-V = variable rows. Page numbers are "
                "pages of the original paper (this index page excluded)."]:
        summary.insert_text((40, y), txt, fontsize=7.5)
        y += 10
    y += 4
    used = [c for c in colours if c in set(items["Category"])]
    for k, cat in enumerate(used):
        x = 40 + (k % 2) * 260
        yy = y + (k // 2) * 12
        summary.draw_rect(pymupdf.Rect(x, yy - 7, x + 18, yy + 2), color=None, fill=colours[cat])
        summary.insert_text((x + 24, yy), cat, fontsize=7.5)
    y += ((len(used) + 1) // 2) * 12 + 12
    for _, r in items.iterrows():
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

    # ---- Checklist workbook: one sheet per spreadsheet tab
    CHECKLIST_DIR.mkdir(exist_ok=True)
    out_xlsx = CHECKLIST_DIR / (csv_path.stem + "_checklist.xlsx")
    wb = Workbook()
    guide = wb.active
    guide.title = "How to use"
    for i, line in enumerate([
        f"Checklist for {pdf_path.name}",
        "",
        "The sheets mirror organised_extraction.xlsx: Overview, Indicators, Limitations.",
        "1. Open the highlighted PDF (highlighted folder) next to this file.",
        "2. For each row, find its tag in the PDF margin (e.g. O12a, I-V3) and read the highlighted text in context.",
        "   Set 'Highlight checked' to Yes once you've looked at it.",
        "3. Proposed changes appear in the cell itself: 'current  →  suggested' (amber).",
        "   A red cell marked '(?)' is an open question: answer it in 'Your note'.",
        "4. 'Your verdict': Yes = agree with the row (the suggested values if there are any, otherwise the current ones).",
        "   No = disagree; say why or what it should be in 'Your note'. Unsure = discuss.",
        "5. Indicators: one row per variable, with the spreadsheet's columns in the same order (I3 Role, I4 Dimension,",
        "   I5 Indicator, I6 Definition, I7 Measure type). One verdict covers the whole row.",
        "6. When done, save it to sinanverification/ and send it back: agreed changes are applied and logged.",
        "The 'Role definitions' sheet explains the four roles used in I3 Role.",
        "Column codes and rules: CODEBOOK.md. Colours: HIGHLIGHT_COLOURS.md.",
    ], 1):
        guide.cell(i, 1, line)
    guide["A1"].font = Font(bold=True, size=13)
    guide.column_dimensions["A"].width = 115
    rd = wb.create_sheet("Role definitions")
    rd.append(["Role (I3)", "Definition", "How to recognise it", "Example"])
    for row in ROLE_DEFINITIONS:
        rd.append(row)
    style_header(rd)
    for col, wdt in zip("ABCD", [18, 50, 60, 50]):
        rd.column_dimensions[col].width = wdt
    for r_ in rd.iter_rows(min_row=2):
        for c in r_:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    rd.append([])
    rd.append(["Roles come from models and group-comparison tests; correlations, factor analysis and descriptives add no role. "
               "Two roles only when a variable plays different roles in different models/tests (e.g. paper 3). "
               "Full rules: CODEBOOK.md section 3.1."])
    simple_sheet(wb, "Overview", ev[ev["Section"] == "Overview"], colours)
    indicator_sheet(wb, ind, ev[ev["Section"] == "Indicators"], colours)
    simple_sheet(wb, "Limitations", ev[ev["Section"].str.startswith("Limitations")], colours)
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
    if len(ind):
        md += ["## Indicators (one row per variable)", "",
               "| Tag | I3 Role | I4 Dimension | I5 Indicator | I6 Definition | I7 Measure type | Status | Quote from paper | Page | Reasoning |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in ind.iterrows():
            c = [cell(shown(r[a], r["Suggested " + a.lower()])) for a, _ in IND_ATTRS]
            md.append(f"| {r['Tag']} | {c[0]} | {c[1]} | {cell(r['Indicator'])} | {c[2]} | {c[3]} | {r['Status']} | "
                      f"“{cell(r['Quote'])}” | {r['Page'] or r['Quote check']} | {cell(r['Reasoning'])} |")
        md.append("")
    out_md = csv_path.with_suffix(".md")
    out_md.write_text("\n".join(md), encoding="utf-8")

    bad = (items["Quote check"] == "NOT FOUND").sum()
    print(f"{len(items)} items, {(items['Quote check'] == 'Highlighted').sum()} highlighted, {bad} quotes not found; "
          f"{(items['Status'] != 'Matches').sum()} need a decision")
    print(f"-> {out_xlsx}\n-> {out_md}\n-> {out_pdf}")
    return bad


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(1 if main(*sys.argv[1:]) else 0)
