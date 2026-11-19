"""Inter-reviewer agreement between two review workbooks (ideally both --blind).

    python scripts/08_agreement.py output/review/review_A_blind.xlsx output/review/review_B_blind.xlsx

For each paper x field, each reviewer's value = 'Corrected value' if given,
otherwise 'Current value'. Reports % agreement per field, Cohen's kappa for
the categorical fields, and a list of disagreements to resolve.

Output: output/tables/08_agreement.xlsx
"""
import re
import sys

import _path  # noqa: F401
import pandas as pd

from sysreview import coding
from sysreview.output import write_tables

CATEGORICAL = {
    "Qualitative or Quantitative": coding.approach,
    "Study Design": coding.time_design,
    "Human Resources Capacity": coding.yes, "Financial Capacity": coding.yes,
    "Infrastructure and Process Capacity": coding.yes,
    "Planning and Development Capacity": coding.yes,
    "Relationship and Network Capacity": coding.yes, "External Influences": coding.yes,
    "Critical Elements Used": lambda x: str(x).strip().lower(),
    "Sport Investigated": coding.sport_category,
    "Year of Publication": lambda x: str(x).strip()[:4],
    "Final Club Sample Size": lambda x: re.sub(r"[^\d]", "", str(x)),
}


def values_of(path):
    df = pd.read_excel(path, sheet_name="Review")
    val = df["Corrected value"].where(df["Corrected value"].notna(), df["Current value"])
    return pd.Series(val.values, index=pd.MultiIndex.from_arrays([df["ID"], df["Field"]]))


def norm(field, x):
    if pd.isna(x):
        return ""
    if field in CATEGORICAL:
        return str(CATEGORICAL[field](x))
    return re.sub(r"\s+", " ", str(x)).strip().lower()


def kappa(a, b):
    cats = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((list(a).count(c) / n) * (list(b).count(c) / n) for c in cats)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def main(a_path, b_path):
    a, b = values_of(a_path), values_of(b_path)
    common = a.index.intersection(b.index)
    rows = []
    for pid, field in common:
        va, vb = norm(field, a[(pid, field)]), norm(field, b[(pid, field)])
        rows.append({"ID": pid, "Field": field, "Agree": va == vb,
                     "Reviewer A": a[(pid, field)], "Reviewer B": b[(pid, field)]})
    df = pd.DataFrame(rows)
    per_field = df.groupby("Field")["Agree"].agg(["count", "mean"]).rename(
        columns={"count": "Papers", "mean": "% agreement"})
    per_field["% agreement"] = (per_field["% agreement"] * 100).round(1)
    per_field["Cohen's kappa"] = [
        round(kappa([norm(f, a[(i, f)]) for i, _ in df[df.Field == f][["ID", "Field"]].values],
                    [norm(f, b[(i, f)]) for i, _ in df[df.Field == f][["ID", "Field"]].values]), 2)
        if f in CATEGORICAL else None for f in per_field.index]
    disagreements = df[~df["Agree"]].drop(columns="Agree").assign(**{"Resolved value": "", "Resolved by": ""})
    write_tables("08_agreement", {"Per field": per_field, "Disagreements": disagreements.set_index("ID")})
    print(f"Overall agreement {df['Agree'].mean() * 100:.1f}% over {len(df)} items; "
          f"{len(disagreements)} disagreements -> output/tables/08_agreement.xlsx")
    print("Free-text fields will rarely match word-for-word; judge those by reading the Disagreements tab.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
