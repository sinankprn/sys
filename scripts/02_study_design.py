"""Study design: approach, time design, sample sizes, respondents, methods.

Outputs: output/tables/02_study_design.xlsx and output/figures/02_*.png
"""
import _path  # noqa: F401
import pandas as pd

from sysreview import coding, config
from sysreview.load import load
from sysreview.output import APPROACH_COLOURS, explode_count, hbar, stacked_bar, write_tables


def main():
    v, _ = load()
    c = coding.coded_table(v)

    approach = c["Approach"].value_counts().to_frame("Papers")
    approach["%"] = (approach["Papers"] / len(c) * 100).round(1)
    time = c["Time design"].value_counts().to_frame("Papers")
    time["%"] = (time["Papers"] / len(c) * 100).round(1)
    approach_x_time = pd.crosstab(c["Approach"], c["Time design"], margins=True, margins_name="Total")
    method = v["Research Method"].value_counts().to_frame("Papers")
    collection = explode_count(v["Data Collection Method"],
                               lambda t: coding.tags(t, config.COLLECTION_TAGS)).to_frame("Papers")

    # Sample sizes
    ss = c[["Reference", "Approach", "Time design", "Sample size", "Sample band"]].copy()
    ss["Sample as written"] = v["Final Club Sample Size"]
    ss["Final sample (from Criteria)"] = v["Criteria"].str.extract(r"Final sample:\s*([^\n]+)")[0]
    ss["Sampling"] = v["Sampling Strategy"] + " | " + v["Sampling"].fillna("")
    sample_stats = (c.groupby("Approach")["Sample size"]
                    .agg(["count", "min", "median", "mean", "max", "sum"]).round(1))
    bands = (pd.crosstab(c["Sample band"], c["Approach"])
             .reindex([b for b in coding.SAMPLE_BAND_ORDER if b in set(c["Sample band"])]))
    # Papers that appear to share one dataset (same country, region and N) – do not sum their samples.
    key = v["Country"].astype(str) + " | " + v["Region"].astype(str) + " | " + v["Final Club Sample Size"].astype(str)
    shared = key[key.duplicated(keep=False)]
    shared_data = (pd.DataFrame({"Dataset key": shared, "Reference": c.loc[shared.index, "Reference"]})
                   .sort_values("Dataset key"))

    # Respondents
    resp_long = v["Respondents"].map(lambda t: coding.tags(t, config.RESPONDENT_TAGS)).explode().dropna()
    respondents = resp_long.value_counts().to_frame("Papers")
    multi_level = c["Respondent types"].str.contains("Club members|Parents").sum()
    respondents.loc["(Papers surveying individuals as well as clubs)"] = multi_level
    resp_detail = v[["Respondents"]].join(c[["Reference", "Respondent types"]])

    write_tables("02_study_design", {
        "Approach": approach, "Time design": time, "Approach x time": approach_x_time,
        "Research method": method, "Data collection": collection,
        "Sample sizes": ss, "Sample stats": sample_stats, "Sample bands": bands,
        "Shared datasets": shared_data,
        "Respondents": respondents, "Respondent detail": resp_detail,
    })

    stacked_bar(pd.crosstab(c["Time design"], c["Approach"])[
        [x for x in ["Quantitative", "Qualitative", "Mixed methods"] if x in set(c["Approach"])]],
        "Time design by approach", "02_design", colours=APPROACH_COLOURS)
    stacked_bar(bands, "Sample size (clubs or cases)", "02_sample_bands", colours=APPROACH_COLOURS)
    hbar(respondents["Papers"].drop("(Papers surveying individuals as well as clubs)"),
         "Who responded", "02_respondents", note="A paper can have several respondent types.")
    hbar(collection["Papers"], "Data collection methods", "02_collection",
         note="A paper can use several methods.")
    print("02_study_design done")


if __name__ == "__main__":
    main()
