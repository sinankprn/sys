"""Qualitative themes: kept separate from the quantitative indicators.

Covers qualitative and mixed-methods papers (Key Themes column): which capacity
dimensions the themes fall under, which non-capacity theme groups appear, and
the full theme list.

Outputs: output/tables/03b_qualitative_themes.xlsx and output/figures/03b_*.png
"""
import _path  # noqa: F401
import pandas as pd

from sysreview import coding, config
from sysreview.indicators import theme_table
from sysreview.load import load
from sysreview.output import SERIES, hbar, presence_grid, write_tables

SHORT = [config.DIMENSION_SHORT[d] for d in config.DIMENSIONS]


def main():
    v, _ = load()
    c = coding.coded_table(v)
    qual = c[c["Approach"] != "Quantitative"]
    t = theme_table(v).merge(c[["Reference", "Approach"]], left_on="ID", right_index=True)

    papers = qual[["Reference", "Year", "Approach", "Research method", "Data collection",
                   "Sample size", "Respondent types"]].join(v[["Data Analysis"]])
    papers["Themes extracted"] = t.groupby("ID").size().reindex(qual.index, fill_value=0)
    papers["Themes grouped by capacity dimension"] = (
        t[t["Is capacity dimension"]].groupby("ID").size().reindex(qual.index, fill_value=0))

    cap = t[t["Is capacity dimension"]]
    themes_per_dim = (cap.groupby("Dimension")
                      .agg(Themes=("Theme", "count"), Papers=("ID", "nunique"),
                           IDs=("ID", lambda s: ", ".join(map(str, sorted(set(s))))))
                      .reindex(config.DIMENSIONS).fillna({"Themes": 0, "Papers": 0}))
    paper_x_dim = (pd.crosstab(cap["ID"], cap["Dimension"])
                   .reindex(index=qual.index, columns=config.DIMENSIONS, fill_value=0))
    paper_x_dim.columns = SHORT
    paper_x_dim.insert(0, "Reference", qual["Reference"])

    other = t[~t["Is capacity dimension"]]
    other_groups = (other.groupby("Dimension")
                    .agg(Themes=("Theme", "count"),
                         IDs=("ID", lambda s: ", ".join(map(str, sorted(set(s))))))
                    .sort_values("Themes", ascending=False))
    other_groups.index = other_groups.index.str.replace("^Other: ", "", regex=True)
    other_groups.index.name = "Theme group (not a capacity dimension)"

    # Flagged dimensions vs dimensions actually used to group themes
    flagged = qual[SHORT].astype(bool)
    grouped = paper_x_dim[SHORT].astype(bool)
    framing = pd.DataFrame({
        "Reference": qual["Reference"],
        "Dimensions flagged Yes": flagged.apply(lambda r: ", ".join(r.index[r]), axis=1),
        "Dimensions used to group themes": grouped.apply(lambda r: ", ".join(r.index[r]), axis=1),
    })
    framing["Themes organised by dimension?"] = grouped.any(axis=1).map({True: "Yes", False: "No (inductive / other framing)"})

    theme_list = t[["ID", "Reference", "Approach", "Research question", "Dimension", "Theme", "Text"]]

    write_tables("03b_qualitative_themes", {
        "Qualitative papers": papers, "Themes per dimension": themes_per_dim,
        "Paper x dimension": paper_x_dim, "Framing": framing,
        "Other theme groups": other_groups, "Theme list": theme_list,
    })

    hbar(themes_per_dim["Themes"].rename(index=config.DIMENSION_SHORT).astype(int),
         "Qualitative themes per capacity dimension", "03b_themes_per_dimension",
         xlabel="Number of themes", colour=SERIES[1],
         note=f"Qualitative and mixed-methods papers (n = {len(qual)}).")
    presence_grid(qual.set_index("Reference")[SHORT],
                  "Dimensions examined - qualitative and mixed-methods papers", "03b_paper_dimension_grid")
    print("03b_qualitative_themes done")


if __name__ == "__main__":
    main()
