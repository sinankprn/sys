"""Apply a completed paper checklist to organised_extraction.xlsx.

    python tools/apply_checklist.py sinanverification/paper_01_checklist.xlsx

Completed checklists are kept in sinanverification/ (blank ones are generated in checklists/).

For each checklist row:
  - Status "Suggest change" or "Decision needed", verdict Agree/Yes  -> the Suggested
    value is written to the spreadsheet cell named by the tag
  - verdict Disagree/No on a suggestion  -> no change; the decision and the note are logged
  - verdict Disagree/No on a "Matches" row  -> printed for follow-up (the value may be wrong)
  - blank verdict  -> printed; the paper is not marked as checked

Every applied or rejected suggestion is added to the "Change log" tab, and the paper
gets a row in the "Verification" tab. Formatting in the workbook is preserved.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "organised_extraction.xlsx"
SHEETS = {"O": "Overview", "I": "Indicators (quantitative)", "L": "Limitations & future research"}
LOG_HEADERS = ["Date", "Paper ID", "Reference", "Tag", "Sheet", "Column", "Item",
               "Old value", "New value", "Decision", "Reviewer note", "Evidence page"]
VER_HEADERS = ["Paper ID", "Reference", "Date checked", "Items checked", "Agreed",
               "Suggestions accepted", "Suggestions rejected", "Open items", "Checklist file"]


def verdict(v) -> str:
    v = str(v).strip().lower()
    if v in ("agree", "yes", "y"):
        return "agree"
    if v in ("disagree", "no", "n"):
        return "disagree"
    if v in ("unsure", "?"):
        return "unsure"
    return ""


def header_index(ws, code: str) -> int:
    for cell in ws[1]:
        if str(cell.value).split(" ")[0] == code:
            return cell.column
    raise KeyError(f"No column with code {code} in {ws.title}")


def paper_rows(ws, pid):
    """Row numbers of a paper's rows in a long tab, in sheet order."""
    idc = header_index(ws, ws.cell(1, 1).value.split(" ")[0])
    return [r for r in range(2, ws.max_row + 1) if str(ws.cell(r, idc).value) == str(pid)]


def get_or_create(wb, title, headers):
    if title in wb.sheetnames:
        return wb[title]
    ws = wb.create_sheet(title)
    ws.append(headers)
    return ws


def main(checklist_path):
    checklist_path = Path(checklist_path)
    pid = int(re.search(r"paper_(\d+)", checklist_path.name).group(1))
    ck = pd.read_excel(checklist_path, sheet_name="Checklist", dtype=str).fillna("")
    ck["v"] = ck["Your verdict"].map(verdict)

    wb = openpyxl.load_workbook(WORKBOOK)
    ov = wb["Overview"]
    id_col = header_index(ov, "O1")
    ref_col = header_index(ov, "O2")
    row = next(r for r in range(2, ov.max_row + 1) if str(ov.cell(r, id_col).value) == str(pid))
    reference_before = ov.cell(row, ref_col).value
    log = get_or_create(wb, "Change log", LOG_HEADERS)
    today = date.today().isoformat()

    accepted = rejected = 0
    follow_up = []
    for _, r in ck.iterrows():
        tag, v = r["Tag"], r["v"]
        if not v:
            follow_up.append(f"{tag}: no verdict")
            continue
        if v == "unsure":
            follow_up.append(f"{tag}: unsure - {r['Your note']}")
            continue
        if r["Status"] == "Matches":
            if v == "disagree":
                follow_up.append(f"{tag}: you disagreed with a matching value - {r['Your note']}")
            continue
        # A suggestion (Suggest change / Decision needed)
        m = re.match(r"^([OIL])(\d+)", tag)
        code = f"{m.group(1)}{m.group(2)}" if m else ""
        sheet = SHEETS.get(code[:1], "")
        col_name = code
        if sheet:
            try:
                col_name = wb[sheet].cell(1, header_index(wb[sheet], code)).value
            except KeyError:
                pass
        if v == "disagree":
            rejected += 1
            log.append([today, pid, reference_before, tag, sheet, col_name, r["Field"], r["In spreadsheet"],
                        r["In spreadsheet"], f"Kept (suggested: {r['Suggested']})", r["Your note"], r["Page"]])
            continue
        # Agreed. With no Suggested value, "Yes" means keep the current value.
        if not r["Suggested"].strip():
            log.append([today, pid, reference_before, tag, sheet, col_name, r["Field"], r["In spreadsheet"],
                        r["In spreadsheet"], "Kept (decision: current value confirmed)", r["Your note"], r["Page"]])
            continue
        # Agreed: write the suggested value
        if code.startswith("O"):
            col = header_index(ov, code)
            old = ov.cell(row, col).value
            new = r["Suggested"]
            if str(old) != str(new):
                ov.cell(row, col).value = (new == "True") if new in ("True", "False") else new
            accepted += 1
            log.append([today, pid, reference_before, tag, "Overview", ov.cell(1, col).value, r["Field"],
                        old, new, "Changed", r["Your note"], r["Page"]])
        elif (mi := re.match(r"^(I\d+)-V(\d+)(?:-(\d+))?$", tag)):
            # Indicators: column I<n> for variable(s) V<a>[-<b>] of this paper (row order in the tab)
            ws = wb["Indicators (quantitative)"]
            col = header_index(ws, mi.group(1))
            rows = paper_rows(ws, pid)
            a, b = int(mi.group(2)), int(mi.group(3) or mi.group(2))
            for v_no in range(a, b + 1):
                rr = rows[v_no - 1]
                old = ws.cell(rr, col).value
                ws.cell(rr, col).value = r["Suggested"]
                log.append([today, pid, reference_before, f"{tag} (V{v_no})", ws.title, ws.cell(1, col).value,
                            ws.cell(rr, header_index(ws, "I5")).value, old, r["Suggested"], "Changed",
                            r["Your note"], r["Page"]])
            accepted += 1
        elif (ml := re.match(r"^L5-(Lim|FR)(\d+)(\+?)$", tag)):
            ws = wb["Limitations & future research"]
            kind = "Limitation" if ml.group(1) == "Lim" else "Future research"
            n = int(ml.group(2))
            if ml.group(3) == "+":            # add a new point, directly under the paper's other rows
                prows = paper_rows(ws, pid)
                at = (prows[-1] + 1) if prows else ws.max_row + 1
                ws.insert_rows(at)
                for c, val in enumerate([pid, ov.cell(row, ref_col).value, kind, n, r["Suggested"], None], 1):
                    ws.cell(at, c).value = val
                log.append([today, pid, reference_before, tag, ws.title, "L5 Point", f"{kind} {n}",
                            "(no row)", r["Suggested"], "Added", r["Your note"], r["Page"]])
            else:
                rr = next(x for x in paper_rows(ws, pid)
                          if ws.cell(x, header_index(ws, "L3")).value == kind
                          and str(ws.cell(x, header_index(ws, "L4")).value) == str(n))
                old = ws.cell(rr, header_index(ws, "L5")).value
                if r["Suggested"].lower().startswith("delete"):
                    ws.delete_rows(rr)
                    log.append([today, pid, reference_before, tag, ws.title, "L5 Point", f"{kind} {n}",
                                old, "(row deleted)", "Deleted", r["Your note"], r["Page"]])
                else:
                    ws.cell(rr, header_index(ws, "L5")).value = r["Suggested"]
                    log.append([today, pid, reference_before, tag, ws.title, "L5 Point", f"{kind} {n}",
                                old, r["Suggested"], "Changed", r["Your note"], r["Page"]])
            accepted += 1
        else:
            follow_up.append(f"{tag}: agreed change could not be applied automatically ({r['Suggested']})")

    # Keep the Reference column in the other tabs in step with O2
    new_ref = ov.cell(row, ref_col).value
    if new_ref != reference_before:
        for title, code in [("Indicators (quantitative)", "I2"), ("Limitations & future research", "L2")]:
            ws = wb[title]
            idc, rc = header_index(ws, title[0] + "1"), header_index(ws, code)
            for rr in range(2, ws.max_row + 1):
                if str(ws.cell(rr, idc).value) == str(pid):
                    ws.cell(rr, rc).value = new_ref

    ver = get_or_create(wb, "Verification", VER_HEADERS)
    existing = [r for r in range(2, ver.max_row + 1) if str(ver.cell(r, 1).value) == str(pid)]
    open_items = "; ".join(follow_up)
    values = [pid, new_ref, today, len(ck), int((ck["v"] == "agree").sum()), accepted, rejected,
              open_items or "No open items", f"{checklist_path.parent.name}/{checklist_path.name}"]
    if existing:
        for c, val in enumerate(values, 1):
            ver.cell(existing[0], c).value = val
    else:
        ver.append(values)
    wb.save(WORKBOOK)

    print(f"Paper {pid}: {accepted} suggestion(s) applied, {rejected} rejected and logged.")
    for f in follow_up:
        print("  follow up:", f)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
