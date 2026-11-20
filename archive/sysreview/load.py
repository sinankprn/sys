"""Read the extraction sheet, separate values from ✓ ticks, apply corrections."""
from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd

from . import config

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def read_raw(path: Path | str = config.RAW_WORKBOOK):
    """Return (values, ticks) DataFrames, both indexed by paper ID.

    In Sheet1 every field is followed by a narrow ✓ column; pandas names those
    '✓', '✓.1', ... so we pair each tick column with the field to its left.
    """
    raw = pd.read_excel(path, sheet_name=config.DATA_SHEET)
    raw = raw.dropna(subset=["ID"])
    raw["ID"] = raw["ID"].astype(int)
    cols = list(raw.columns)
    fields, tick_map = [], {}
    for i, c in enumerate(cols):
        if str(c).startswith("✓"):
            continue
        fields.append(c)
        if i + 1 < len(cols) and str(cols[i + 1]).startswith("✓"):
            tick_map[c] = cols[i + 1]
    values = raw[fields].set_index("ID")
    ticks = pd.DataFrame({f: raw[t].fillna(False).astype(bool) for f, t in tick_map.items()})
    ticks.index = raw["ID"]
    ticks = ticks.drop(columns=["ID"], errors="ignore")
    # Normalise text: strip whitespace, turn empty strings into NaN.
    for c in values.columns:
        if values[c].dtype == object:
            values[c] = values[c].map(lambda v: v.strip() if isinstance(v, str) else v)
            values[c] = values[c].replace({"": pd.NA})
    return values, ticks


def read_corrections(path: Path | str = config.CORRECTIONS_CSV) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=["ID", "Field", "Old value", "New value",
                                     "Reviewer", "Location in paper", "Date"])
    return pd.read_csv(path, dtype={"ID": int})


def load(apply_corrections: bool = True):
    """Values and ticks with any logged corrections applied on top of the raw sheet.

    The raw workbook is never modified: corrections live in
    data/corrections/corrections.csv (written by 07_apply_review.py), so every
    change is auditable and reversible.
    """
    values, ticks = read_raw()
    if apply_corrections:
        corr = read_corrections()
        for _, r in corr.iterrows():
            if r["ID"] in values.index and r["Field"] in values.columns:
                new = r["New value"]
                if r["Field"] in ("Year of Publication", "Final Club Sample Size"):
                    num = pd.to_numeric(new, errors="coerce")
                    new = int(num) if pd.notna(num) and float(num).is_integer() else (num if pd.notna(num) else new)
                values.at[r["ID"], r["Field"]] = new
                if r["Field"] in ticks.columns:
                    ticks.at[r["ID"], r["Field"]] = True
        if Path(config.VERIFICATIONS_CSV).exists():
            ver = pd.read_csv(config.VERIFICATIONS_CSV, dtype={"ID": int})
            for _, r in ver.iterrows():
                if r["ID"] in ticks.index and r["Field"] in ticks.columns:
                    ticks.at[r["ID"], r["Field"]] = True
    return values, ticks


def short_ref(values: pd.DataFrame) -> pd.Series:
    """'Balduck et al. (2014)' style label for each paper."""
    def one(row):
        authors = [a.strip() for a in str(row["Authors"]).split(",") if a.strip()]
        first = authors[0].split()[-1] if authors else "?"
        if len(authors) == 2:
            first += " & " + authors[1].split()[-1]
        elif len(authors) > 2:
            first += " et al."
        return f"{first} ({row['Year of Publication']})"
    return values.apply(one, axis=1)
