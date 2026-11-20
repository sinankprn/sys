"""Find missing, inconsistent and unverified data, and rank papers for re-review.

    python scripts/05_quality_checks.py              # offline checks
    python scripts/05_quality_checks.py --crossref   # + compare bibliographic
                                                     #   fields with Crossref (needs internet)

Outputs: output/tables/05_quality_checks.xlsx
"""
import argparse

import _path  # noqa: F401
import pandas as pd

from sysreview import coding, qa
from sysreview.load import load
from sysreview.output import write_tables


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crossref", action="store_true", help="check DOIs against Crossref")
    args = ap.parse_args()

    v, ticks = load()
    c = coding.coded_table(v)
    issues, cr = qa.run_all(v, ticks, crossref=args.crossref)

    # Per-paper priority: High issues weigh most, then unticked fields.
    sev = pd.crosstab(issues["ID"], issues["Severity"]).reindex(v.index, fill_value=0)
    for s in ["High", "Medium", "Info"]:
        if s not in sev:
            sev[s] = 0
    unticked = (~ticks).sum(axis=1).reindex(v.index, fill_value=0)
    papers = c[["Reference", "Approach"]].copy()
    papers["Fields verified"] = ticks.sum(axis=1).astype(str) + " / " + str(ticks.shape[1])
    papers["Fully verified"] = unticked == 0
    papers["High"] = sev["High"]
    papers["Medium"] = sev["Medium"]
    papers["Info"] = sev["Info"]
    papers["Priority score"] = sev["High"] * 5 + sev["Medium"] * 2 + unticked * 0.5
    papers = papers.sort_values("Priority score", ascending=False)

    # Field completeness: share of papers with a real value, and with a tick
    comp = pd.DataFrame({
        "Filled": v.notna().sum(),
        "Placeholder (N/A, None, Not reported)": v.apply(lambda s: s.map(
            lambda x: isinstance(x, str) and (coding.is_na_text(x) or "not reported" in x.lower()))).sum(),
        "Ticked": ticks.sum().reindex(v.columns),
    })
    comp["Blank"] = len(v) - comp["Filled"]
    comp.index.name = "Field"

    by_check = issues.groupby(["Severity", "Check"]).size().rename("Issues").to_frame()

    tables = {"Paper priority": papers, "Issues": issues.drop(columns=[]).reset_index(drop=True).set_index("ID"),
              "Issues by check": by_check, "Field completeness": comp}
    if len(cr):
        tables["Crossref metadata"] = cr.set_index("ID")
    path = write_tables("05_quality_checks", tables)
    print(f"05_quality_checks done: {len(issues)} issues "
          f"({(issues['Severity'] == 'High').sum()} high, {(issues['Severity'] == 'Medium').sum()} medium) -> {path}")


if __name__ == "__main__":
    main()
