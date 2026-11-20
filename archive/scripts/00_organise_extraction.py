"""Build tidy, organised copies of the extraction (the raw workbook is untouched).

output/organised_extraction.xlsx
  - Overview                   one row per paper with the coded/simplified columns
  - Indicators (quantitative)  one row per variable: role, dimension, definition, measure type
  - Themes (qualitative)       one row per qualitative theme, tagged with dimension
  - Limitations & future research  one row per point, with any note on where it came from

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
OVERVIEW_EXCLUDE = ["Respondent types"]   # still analysed in 02_study_design
THEME_COLS = ["ID", "Reference", "Approach", "Research question", "Dimension", "Theme", "Text"]


def limitations_future(v: pd.DataFrame, refs: pd.Series) -> pd.DataFrame:
    """One row per bullet point from the Limitations and Future Research columns."""
    rows = []
    for pid, rec in v.iterrows():
        for field, kind in [("Limitations", "Limitation"), ("Future Research", "Future research")]:
            text = rec.get(field)
            if pd.isna(text):
                continue
            note, points = "", []
            for line in str(text).splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.lower().startswith("note:"):
                    note = line[5:].strip()
                elif line.startswith(("•", "-", "*")):
                    points.append(line.lstrip("•-* ").strip())
                elif points:                      # wrapped continuation of the previous point
                    points[-1] += " " + line
                else:
                    points.append(line)
            for n, pt in enumerate(points, 1):
                rows.append({"ID": pid, "Reference": refs[pid], "Type": kind, "No.": n,
                             "Point": pt, "Note": note})
    return pd.DataFrame(rows, columns=["ID", "Reference", "Type", "No.", "Point", "Note"])


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
        "Overview": (c.drop(columns=OVERVIEW_EXCLUDE), True),
        "Indicators (quantitative)": (ind[INDICATOR_COLS], False),
        "Themes (qualitative)": (themes[THEME_COLS], False),
        "Limitations & future research": (limitations_future(v, c["Reference"]), False),
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
