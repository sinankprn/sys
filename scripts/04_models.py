"""Statistical modelling: which models were employed, and with what outcomes.

Outputs: output/tables/04_models.xlsx and output/figures/04_*.png
"""
import _path  # noqa: F401
import pandas as pd

from sysreview import coding
from sysreview.load import load
from sysreview.output import hbar, stacked_bar, write_tables


def main():
    v, _ = load()
    c = coding.coded_table(v)
    quant = c[c["Approach"] != "Qualitative"]

    fam_long = (v.loc[quant.index, "Statistical Models"].map(coding.model_families)
                .explode().dropna().rename("Model family").reset_index())
    families = (fam_long.groupby("Model family")["ID"]
                .agg(Papers="count", IDs=lambda s: ", ".join(map(str, sorted(s))))
                .sort_values("Papers", ascending=False))
    families["% of quant/mixed papers"] = (families["Papers"] / len(quant) * 100).round(1)

    lines = []
    for pid, text in v.loc[quant.index, "Statistical Models"].items():
        for line in coding.model_lines(text):
            lines.append({"ID": pid, "Reference": c.at[pid, "Reference"],
                          "Model as reported": line,
                          "Family": (coding.model_families(line) or ["Other"])[0]})
    model_lines = pd.DataFrame(lines)

    fam_year = pd.crosstab(fam_long["ID"].map(c["Year"]), fam_long["Model family"])
    fam_period = pd.crosstab(pd.cut(fam_long["ID"].map(c["Year"]).astype(float), [2000, 2014, 2019, 2030],
                                    labels=["≤2014", "2015-2019", "2020+"]), fam_long["Model family"])
    regression_based = quant["Model families"].str.contains("regression|logit|Probit|Multilevel", case=False)
    summary = pd.DataFrame({
        "Quantitative / mixed papers": [len(quant)],
        "Using any regression model": [int(regression_based.sum())],
        "Using multilevel models": [int(quant["Model families"].str.contains("Multilevel").sum())],
        "Descriptive / bivariate only": [int((~regression_based & ~quant["Model families"].str.contains("factor|QAP", case=False)).sum())],
    }).T.rename(columns={0: "Papers"})

    per_paper = quant[["Reference", "Year", "Approach", "Time design", "Model families"]].join(
        v[["Statistical Models", "Dependent Variables", "Data Analysis"]])
    per_paper["N models reported"] = v.loc[quant.index, "Statistical Models"].str.extract(r"(\d+) models?")[0]

    write_tables("04_models", {
        "Summary": summary, "Model families": families, "Models as reported": model_lines,
        "Families by period": fam_period, "Families by year": fam_year, "Per paper": per_paper,
    })
    hbar(families["Papers"], "Statistical models employed", "04_model_families",
         note=f"Quantitative and mixed-methods papers (n = {len(quant)}); a paper can use several.")
    stacked_bar(fam_period, "Model families by period", "04_models_by_period")
    print("04_models done")


if __name__ == "__main__":
    main()
