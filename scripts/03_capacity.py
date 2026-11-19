"""Analysis of capacity: which dimensions, how measured, what was looked at
(quantitative variables), and use of Doherty et al. (2014) critical elements.
Qualitative themes are analysed separately in 03b_qualitative_themes.py.

Outputs: output/tables/03_capacity.xlsx and output/figures/03_*.png
"""
import _path  # noqa: F401
import pandas as pd

from sysreview import coding, config
from sysreview.indicators import critical_element_matrix, indicator_table
from sysreview.load import load
from sysreview.output import hbar, hstacked, presence_grid, stacked_bar, write_tables, APPROACH_COLOURS

SHORT = [config.DIMENSION_SHORT[d] for d in config.DIMENSIONS]


def main():
    v, _ = load()
    c = coding.coded_table(v)
    ind = indicator_table(v)
    ind = ind.merge(c[["Reference", "Approach"]], left_on="ID", right_index=True)

    # 1. Which dimensions received attention
    dims = c[SHORT + ["External"]]
    attention = dims.sum().rename("Papers").to_frame()
    attention["%"] = (attention["Papers"] / len(c) * 100).round(1)
    by_approach = c.groupby("Approach")[SHORT + ["External"]].sum().T
    c["Period"] = pd.cut(c["Year"].astype(float), [2000, 2014, 2030], labels=["≤2014", "2015+"])
    by_period = c.groupby("Period", observed=False)[SHORT].mean().T.mul(100).round(0)
    by_period.columns = [f"% of papers {p}" for p in by_period.columns]
    n_dims = c["N dimensions"].value_counts().sort_index().rename("Papers").to_frame()
    n_dims.index.name = "Dimensions covered (of 5)"
    co = dims[SHORT].astype(int).T.dot(dims[SHORT].astype(int))
    paper_dims = c[["Reference", "Approach"] + SHORT + ["External", "N dimensions"]]

    # 2. What was looked at / how measured (quantitative variables only;
    #    qualitative themes are in 03b_qualitative_themes.py)
    cap = ind[ind["Is capacity dimension"]]
    quant = cap
    indicators_per_dim = pd.crosstab(cap["Dimension"], cap["Role"])
    measure_by_dim = pd.crosstab(quant["Dimension"], quant["Measure type"])
    measure_overall = quant["Measure type"].value_counts().to_frame("Indicators")
    papers_per_measure = (quant.groupby("Measure type")["ID"].nunique().rename("Papers").to_frame())
    role_by_dim = (cap.groupby(["Dimension", "Role"])["ID"].nunique().unstack(fill_value=0))
    role_by_dim.columns = [f"Papers with {r.lower()}s" for r in role_by_dim.columns]
    # Capacity as outcome vs predictor
    as_dv = ind[ind["Role"] == "Dependent variable"].groupby("ID")["Dimension"].apply(
        lambda s: "; ".join(sorted(set(x for x in s if x in config.DIMENSIONS))))
    as_iv = ind[ind["Role"] == "Independent variable"].groupby("ID")["Dimension"].apply(
        lambda s: "; ".join(sorted(set(x for x in s if x in config.DIMENSIONS))))
    roles = c[["Reference", "Approach"]].join(as_dv.rename("Capacity as outcome (DV)")).join(
        as_iv.rename("Capacity as predictor (IV)")).fillna("")
    other_groups = ind[~ind["Is capacity dimension"] & (ind["Dimension"] != "Not grouped")]
    other_constructs = other_groups.groupby("Dimension")["ID"].agg(
        Indicators="count", IDs=lambda s: ", ".join(map(str, sorted(set(s))))).sort_values("Indicators", ascending=False)
    indicator_list = cap[["ID", "Reference", "Approach", "Role", "Dimension", "Indicator", "Measure type", "Text"]]

    # 3. Critical elements
    ce = critical_element_matrix(v)
    ce_counts = ce.sum().rename("Papers (keyword match)").to_frame()
    ce_flat = ce.copy()
    ce_flat.columns = [f"{d}: {e}" for d, e in ce.columns]
    ce_flat.insert(0, "Critical Elements Used (sheet)", v["Critical Elements Used"])
    ce_flat.insert(0, "Reference", c["Reference"])
    ce_usage = pd.crosstab(v["Critical Elements Used"],
                           pd.cut(c["Year"].astype(float), [2000, 2013, 2030],
                                  labels=["Before 2014", "2014 onwards"]))
    ce_notes = v[["Critical Elements Used", "Critical Elements Notes"]].join(c["Reference"])

    write_tables("03_capacity", {
        "Dimension attention": attention, "By approach": by_approach, "By period": by_period,
        "Dimensions per paper": n_dims, "Co-occurrence": co, "Paper x dimension": paper_dims,
        "Indicators per dimension": indicators_per_dim, "Measure type x dimension": measure_by_dim,
        "Measure types": measure_overall.join(papers_per_measure),
        "Papers per role": role_by_dim, "Outcome vs predictor": roles,
        "Indicator list": indicator_list, "Other constructs": other_constructs,
        "Critical elements count": ce_counts, "Critical elements x paper": ce_flat,
        "CE use by period": ce_usage, "CE notes": ce_notes,
    })

    hbar(attention["Papers"].rename(index={"External": "External influences"}),
         "Capacity dimensions examined", "03_dimension_attention")
    stacked_bar(by_approach.drop(columns=[], errors="ignore")[
        [x for x in ["Quantitative", "Qualitative", "Mixed methods"] if x in by_approach]],
        "Dimensions examined, by approach", "03_dimensions_by_approach", colours=APPROACH_COLOURS)
    grid = c.set_index("Reference")[SHORT + ["External"]]
    presence_grid(grid, "Dimensions examined in each paper", "03_paper_dimension_grid")
    mt = measure_by_dim.copy()
    mt.index = [config.DIMENSION_SHORT.get(i, i) for i in mt.index]
    hstacked(mt, "How capacity indicators were measured (quantitative variables)", "03_measurement",
             xlabel="Number of variables")
    ce_lab = ce_counts["Papers (keyword match)"]
    ce_lab.index = [f"{d}: {e}" for d, e in ce_lab.index]
    hbar(ce_lab, "Critical elements found in paper variables/themes", "03_critical_elements",
         note="Keyword matches - check each against the paper.")
    print("03_capacity done")


if __name__ == "__main__":
    main()
