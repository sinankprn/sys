"""Build a tidy, organised copy of the extraction (the raw workbook is untouched).

Output: output/organised_extraction.xlsx with
  - Overview      one row per paper with the coded/simplified columns
  - one tab per section (Publication, Sample, Design, Capacity, Modelling, Findings)
  - Indicators    one row per variable/theme, tagged with dimension and measure type
  - Verification  which fields are ticked, per paper
"""
import _path  # noqa: F401
import pandas as pd

from sysreview import coding, config
from sysreview.indicators import indicator_table
from sysreview.load import load
from sysreview.output import format_sheet


def main():
    v, ticks = load()
    c = coding.coded_table(v)
    ind = indicator_table(v).merge(c[["Reference"]], left_on="ID", right_index=True)

    path = config.OUTPUT / "organised_extraction.xlsx"
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        c.to_excel(xw, sheet_name="Overview")
        for section, fields in config.SECTIONS.items():
            cols = [f for f in fields if f in v.columns]
            v[cols].join(c["Reference"]).loc[:, ["Reference"] + cols].to_excel(xw, sheet_name=section)
        ind[["ID", "Reference", "Role", "Dimension", "Indicator", "Measure type", "Text"]] \
            .to_excel(xw, sheet_name="Indicators", index=False)
        ver = ticks.replace({True: "✓", False: ""})
        ver.insert(0, "Verified", ticks.sum(axis=1).astype(str) + "/" + str(ticks.shape[1]))
        ver.insert(0, "Reference", c["Reference"])
        ver.to_excel(xw, sheet_name="Verification")
        for ws in xw.sheets.values():
            format_sheet(ws)
    print(f"00_organise_extraction done -> {path}")


if __name__ == "__main__":
    main()
