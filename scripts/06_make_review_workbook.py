"""Create a re-review workbook: one row per paper x field, with QA flags, a
decision dropdown and space for the corrected value and page reference.

    python scripts/06_make_review_workbook.py --reviewer SK
    python scripts/06_make_review_workbook.py --reviewer SK --papers 3,14,30
    python scripts/06_make_review_workbook.py --reviewer SK --unverified-only
    python scripts/06_make_review_workbook.py --reviewer R2 --blind --papers 1-6

--blind hides the current values so a second reviewer extracts independently;
compare the two files afterwards with 08_agreement.py.

Output: output/review/review_<reviewer>.xlsx
"""
import argparse
from datetime import date

import _path  # noqa: F401
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from sysreview import config, qa
from sysreview.load import load, short_ref

DECISIONS = ["Confirmed", "Corrected", "Not reported in paper", "Unsure - discuss"]
FILL = {"High": "F8D0CF", "Medium": "FCE8C3", "Info": "FFFFFF"}


def parse_ids(text, all_ids):
    if not text:
        return list(all_ids)
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [i for i in out if i in set(all_ids)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewer", required=True)
    ap.add_argument("--papers", help="e.g. 1,4,7-10 (default: all)")
    ap.add_argument("--unverified-only", action="store_true", help="only fields not yet ticked")
    ap.add_argument("--blind", action="store_true", help="hide current values (independent second extraction)")
    args = ap.parse_args()

    v, ticks = load()
    refs = short_ref(v)
    issues, _ = qa.run_all(v, ticks)
    ids = parse_ids(args.papers, v.index)

    field_section = {f: s for s, fs in config.SECTIONS.items() for f in fs}
    fields = [f for s in config.SECTIONS.values() for f in s if f in v.columns]

    wb = Workbook()
    # --- instructions
    ws0 = wb.active
    ws0.title = "How to use"
    lines = [
        f"Re-review workbook for {args.reviewer} - created {date.today().isoformat()}",
        "",
        "1. Work paper by paper (see 'Papers' for a suggested order: highest priority first).",
        "2. Open the PDF. For each row in 'Review', read 'Current value' against the paper.",
        "3. Choose a Decision: Confirmed / Corrected / Not reported in paper / Unsure - discuss.",
        "4. If Corrected, type the full replacement text in 'Corrected value'.",
        "5. Always record where you found it in 'Page / location' (e.g. p.7, Table 2).",
        "6. Red rows = likely problem, amber = check carefully (see 'QA flags').",
        "7. When done, save and run:  python scripts/07_apply_review.py output/review/<this file>",
        "   Corrections are logged to data/corrections/ - the raw workbook is never overwritten.",
    ]
    if args.blind:
        lines.insert(3, "BLIND MODE: current values are hidden. Enter what the paper says in 'Corrected value'.")
    for i, l in enumerate(lines, 1):
        ws0.cell(i, 1, l)
    ws0["A1"].font = Font(bold=True, size=13)
    ws0.column_dimensions["A"].width = 110

    # --- papers
    wsp = wb.create_sheet("Papers")
    sev = pd.crosstab(issues["ID"], issues["Severity"]).reindex(v.index, fill_value=0)
    hdr = ["ID", "Reference", "Title", "DOI", "High flags", "Medium flags", "Fields unticked",
           "PDF found?", "Review complete?", "Date", "Notes"]
    wsp.append(hdr)
    order = sorted(ids, key=lambda i: -(sev.get("High", pd.Series(0, index=v.index))[i] * 5
                                          + sev.get("Medium", pd.Series(0, index=v.index))[i] * 2
                                          + (~ticks.loc[i]).sum() * 0.5))
    for pid in order:
        wsp.append([pid, refs[pid], v.at[pid, "Paper Title"], v.at[pid, "DOI"],
                    int(sev.get("High", pd.Series(0, index=v.index))[pid]),
                    int(sev.get("Medium", pd.Series(0, index=v.index))[pid]),
                    int((~ticks.loc[pid]).sum()), "", "", "", ""])
    yn = DataValidation(type="list", formula1='"Yes,No"', allow_blank=True)
    wsp.add_data_validation(yn)
    yn.add(f"H2:I{len(order) + 1}")

    # --- review rows
    ws = wb.create_sheet("Review")
    hdr = ["ID", "Reference", "Section", "Field", "Current value", "Ticked before",
           "QA flags", "Decision", "Corrected value", "Page / location", "Notes", "Reviewer"]
    ws.append(hdr)
    widths = [5, 22, 11, 26, 70, 8, 40, 18, 60, 16, 30, 10]
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    flag_map = issues.groupby(["ID", "Field"]).apply(
        lambda d: (d["Severity"].map({"High": 0, "Medium": 1, "Info": 2}).min(),
                   "\n".join(f"[{s}] {t}" for s, t in zip(d["Severity"], d["Detail"]))),
        include_groups=False).to_dict()
    r = 1
    for pid in order:
        for f in fields:
            already = bool(ticks.at[pid, f]) if f in ticks.columns else False
            flag = flag_map.get((pid, f))
            if args.unverified_only and already and not flag:
                continue
            val = v.at[pid, f]
            cur = "" if args.blind else ("" if pd.isna(val) else str(val))
            ws.append([pid, refs[pid], field_section.get(f, ""), f, cur,
                       "✓" if already else "", flag[1] if flag else "", "", "", "", "", args.reviewer])
            r += 1
            sevlvl = {0: "High", 1: "Medium"}.get(flag[0]) if flag else None
            for cell in ws[r]:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                if sevlvl:
                    cell.fill = PatternFill("solid", fgColor=FILL[sevlvl])
    dv = DataValidation(type="list", formula1='"' + ",".join(DECISIONS) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"H2:H{r}")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1C5CAB")
    ws.freeze_panes = "E2"
    ws.auto_filter.ref = f"A1:L{r}"

    config.REVIEW.mkdir(parents=True, exist_ok=True)
    out = config.REVIEW / f"review_{args.reviewer}{'_blind' if args.blind else ''}.xlsx"
    wb.save(out)
    print(f"06 review workbook: {len(order)} papers, {r - 1} rows -> {out}")


if __name__ == "__main__":
    main()
