"""Write a paper's E3 (Effect sizes) and E4 (P-values) cells from its effects table.

    python tools/effects.py evidence/paper_03_effects.csv
    python tools/effects.py evidence/paper_03_effects.csv --dry-run     # print only

The table has one row per line of the cell (see CODEBOOK.md section 6).
Model-level columns (Model, Label, Family, Outcome, N, Effect type, Location) only need
filling on the first row of each model; they carry down. The tool:
  - writes both cells in the fixed template, with the same numbering in E3 and E4
  - checks Family against O22 and Variable against the paper's Indicators (I5)
  - logs the old and new cell text to sinanverification/verification_log.xlsx
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "organised_extraction.xlsx"
LOGBOOK = ROOT / "sinanverification" / "verification_log.xlsx"
GROUPS = ["quantitative", "mixed methods"]
KINDS = ["Fit", "Intercept", "Predictor", "Control"]
MODEL_COLS = ["Model", "Label", "Family", "Outcome", "N", "Effect type", "Location"]
COLUMNS = MODEL_COLS + ["Contrast", "Kind", "Variable", "Category", "Estimate", "SE", "CI",
                        "Estimate 2 label", "Estimate 2", "Statistic", "p"]
NO_MODELS = "No statistical models"


def clean(v) -> str:
    return "" if pd.isna(v) else str(v).strip()


def p_text(p: str, stars: list[str]) -> str:
    """Normalise the p column: stars -> 'p < x'; blank -> 'n.s.'; anything else as written."""
    if p == "" or p.lower() in ("ns", "n.s."):
        return "n.s."
    if set(p) == {"*"}:
        return f"p < {stars[len(p) - 1]}"
    return p


def effect_text(r) -> str:
    out = r["Estimate"] or "not reported"
    if r["SE"]:
        out += f" (SE {r['SE']})"
    if r["CI"]:
        out += f" [95% CI {r['CI']}]"
    if r["Estimate 2"]:
        out += f"; {r['Estimate 2 label']} = {r['Estimate 2']}"
    return out


def p_line(r, stars) -> str:
    p = p_text(r["p"], stars)
    return f"{r['Statistic']}, {p}" if r["Statistic"] else p


def name(r) -> str:
    return f"{r['Variable']} – {r['Category']}" if r["Category"] else r["Variable"]


def render(df: pd.DataFrame, stars: list[str]) -> tuple[str, str]:
    e3, e4 = [], []
    for model, m in df.groupby("Model", sort=False):
        first = m.iloc[0]
        label = f"{first['Label']}; " if first["Label"] else ""
        head = f"{model.upper()} ({label}{first['Family']}): {first['Outcome']}"
        e3 += [head, f"Effect size: {first['Effect type']} · N = {first['N']}"]
        e4 += [head]
        if first["Location"]:
            e3.append(f"Source: {first['Location']}")
        for contrast, c in m.groupby("Contrast", sort=False):
            if contrast:
                e3.append(contrast); e4.append(contrast)
            n = 0
            for kind in KINDS:
                rows = c[c["Kind"] == kind]
                if rows.empty:
                    continue
                if kind in ("Predictor", "Control"):
                    heading = "Predictors" if kind == "Predictor" else "Controls"
                    e3.append(heading); e4.append(heading)
                for _, r in rows.iterrows():
                    if kind in ("Fit", "Intercept"):
                        lab = r["Variable"] or "Intercept"
                        e3.append(f"{lab}: {effect_text(r)}")
                        e4.append(f"{lab}: {p_line(r, stars)}")
                    else:
                        n += 1
                        e3.append(f"{n}. {name(r)}: {effect_text(r)}")
                        e4.append(f"{n}. {name(r)}: {p_line(r, stars)}")
        e3.append(""); e4.append("")
    return "\n".join(e3).strip(), "\n".join(e4).strip()


def find_paper(wb, pid):
    for g in GROUPS:
        ws = wb[f"Effect sizes ({g})"]
        for r in range(2, ws.max_row + 1):
            if str(ws.cell(r, 1).value) == str(pid):
                return g, ws, r
    sys.exit(f"Paper {pid} is not in any Effect sizes sheet")


def check(df, wb, group, pid) -> list[str]:
    problems = []
    for col in ("Kind",):
        bad = sorted(set(df[col]) - set(KINDS))
        if bad:
            problems.append(f"Kind must be one of {KINDS}: {bad}")
    ov = pd.DataFrame(wb[f"Overview ({group})"].values)
    ov.columns = ov.iloc[0]; ov = ov[1:]
    o22 = [c for c in ov.columns if str(c).startswith("O22")][0]
    allowed = clean(ov[ov.iloc[:, 0].astype(str) == str(pid)][o22].iloc[0])
    for fam in df["Family"].unique():
        if fam not in allowed:
            problems.append(f"Family '{fam}' is not in this paper's O22 ({allowed})")
    sheet = f"Indicators ({group})"
    if sheet in wb.sheetnames:
        ind = pd.DataFrame(wb[sheet].values); ind.columns = ind.iloc[0]; ind = ind[1:]
        i5 = [c for c in ind.columns if str(c).startswith("I5")][0]
        known = set(ind[ind.iloc[:, 0].astype(str) == str(pid)][i5].astype(str))
        vars_ = df[df["Kind"].isin(["Predictor", "Control"])]["Variable"].unique()
        missing = [v for v in vars_ if v not in known]
        if missing:
            problems.append("Not in the Indicators sheet (I5) for this paper: " + "; ".join(missing))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--stars", default=".05,.01,.001",
                    help="p thresholds for *, **, *** as in the paper's table note")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    pid = int(re.search(r"paper_(\d+)", a.csv).group(1))
    df = pd.read_csv(a.csv, dtype=str).fillna("")
    df = df.reindex(columns=COLUMNS, fill_value="")
    df = df.map(lambda v: v.strip())
    for col in MODEL_COLS:                       # carry model-level values down
        df[col] = df[col].replace("", pd.NA).ffill().fillna("")
    stars = [s.strip() for s in a.stars.split(",")]

    wb = openpyxl.load_workbook(WORKBOOK)
    group, ws, row = find_paper(wb, pid)
    problems = check(df, wb, group, pid)
    e3, e4 = render(df, stars)
    for p in problems:
        print("CHECK:", p)
    if a.dry_run:
        print(e3, "\n=====\n", e4, sep="")
        return
    old3, old4 = ws.cell(row, 3).value, ws.cell(row, 4).value
    ws.cell(row, 3).value, ws.cell(row, 4).value = e3, e4
    wb.save(WORKBOOK)

    lg = openpyxl.load_workbook(LOGBOOK); cl = lg["Change log"]
    ref = ws.cell(row, 2).value
    for code, old, new in (("E3", old3, e3), ("E4", old4, e4)):
        if old != new:
            cl.append([date.today().isoformat(), pid, ref, code, ws.title, code, "Whole cell",
                       old, new, "Changed", f"Written by tools/effects.py from {Path(a.csv).name}",
                       ", ".join(df["Location"].unique())])
    lg.save(LOGBOOK)
    print(f"Paper {pid}: E3/E4 written to '{ws.title}'" + ("" if old3 != e3 or old4 != e4 else " (no change)"))


if __name__ == "__main__":
    main()
