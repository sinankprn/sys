"""Build tidy, organised copies of the extraction (the raw workbook is untouched).

output/organised_extraction.xlsx
  - Overview                   one row per paper with the coded/simplified columns
  - Indicators (quantitative)  one row per variable: role, dimension, definition, measure type
  - Themes (qualitative)       one row per qualitative theme, tagged with dimension

output/extraction_by_section.xlsx
  - one tab per section of the extraction (Publication, Aims, Sample, Design,
    Capacity, Modelling, Qualitative, Findings), full text as extracted
  - Verification               which fields are ticked, per paper
"""
import _path  # noqa: F401
import pandas as pd

from sysreview import coding, config
from sysreview.indicators import indicator_table, theme_table
from sysreview.load import load
from sysreview.output import format_sheet

INDICATOR_COLS = ["ID", "Reference", "Role", "Dimension", "Indicator", "Definition", "Measure type", "Text"]
THEME_COLS = ["ID", "Reference", "Approach", "Research question", "Dimension", "Theme", "Text"]


def _write(path, sheets: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, (df, index) in sheets.items():
            df.to_excel(xw, sheet_name=name, index=index)
        for ws in xw.sheets.values():
            format_sheet(ws)
    return path


def main():
    v, ticks = load()
    c = coding.coded_table(v)
    ind = indicator_table(v).merge(c[["Reference"]], left_on="ID", right_index=True)
    themes = theme_table(v).merge(c[["Reference", "Approach"]], left_on="ID", right_index=True)

    main_path = _write(config.OUTPUT / "organised_extraction.xlsx", {
        "Overview": (c, True),
        "Indicators (quantitative)": (ind[INDICATOR_COLS], False),
        "Themes (qualitative)": (themes[THEME_COLS], False),
    })

    sections = {}
    for section, fields in config.SECTIONS.items():
        cols = [f for f in fields if f in v.columns]
        sections[section] = (v[cols].join(c["Reference"]).loc[:, ["Reference"] + cols], True)
    ver = ticks.replace({True: "✓", False: ""})
    ver.insert(0, "Verified", ticks.sum(axis=1).astype(str) + "/" + str(ticks.shape[1]))
    ver.insert(0, "Reference", c["Reference"])
    sections["Verification"] = (ver, True)
    section_path = _write(config.OUTPUT / "extraction_by_section.xlsx", sections)

    print(f"00_organise_extraction done -> {main_path}, {section_path}")


if __name__ == "__main__":
    main()
