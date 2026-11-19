"""Publication characteristics: year, authors, countries, sport, journal.

Outputs: output/tables/01_publication.xlsx and output/figures/01_*.png
"""
import _path  # noqa: F401
import pandas as pd

from sysreview import coding
from sysreview.load import load
from sysreview.output import explode_count, hbar, stacked_bar, write_tables, APPROACH_COLOURS


def main():
    v, _ = load()
    c = coding.coded_table(v)

    # Year
    years = range(int(c["Year"].min()), int(c["Year"].max()) + 1)
    by_year = pd.crosstab(c["Year"], c["Approach"]).reindex(years, fill_value=0)
    by_year["Total"] = by_year.sum(axis=1)
    by_year["Cumulative"] = by_year["Total"].cumsum()
    by_year.index.name = "Year"
    by_period = c.groupby(pd.cut(c["Year"].astype(float), [2000, 2009, 2014, 2019, 2030],
                                 labels=["≤2009", "2010-2014", "2015-2019", "2020+"]),
                          observed=False).size().rename("Papers").to_frame()
    by_period.index.name = "Period"

    # Authors
    author_long = v["Authors"].map(coding.authors).explode().rename("Author").reset_index()
    author_counts = (author_long.groupby("Author")["ID"]
                     .agg(Papers="count", IDs=lambda s: ", ".join(map(str, sorted(s))))
                     .sort_values("Papers", ascending=False))
    first_authors = v["Authors"].map(lambda t: coding.authors(t)[0]).value_counts().rename("First-author papers")
    author_counts = author_counts.join(first_authors).fillna({"First-author papers": 0})
    team_size = c["N authors"].describe().round(2).to_frame("Authors per paper")

    # Countries
    country_long = v["Country"].map(coding.countries).explode().rename("Country").reset_index()
    country_counts = (country_long.groupby("Country")["ID"]
                      .agg(Papers="count", IDs=lambda s: ", ".join(map(str, sorted(s))))
                      .sort_values("Papers", ascending=False))
    country_counts["World region"] = [coding.world_region(x) for x in country_counts.index]
    single_vs_multi = c["Multi-country"].map({True: "Multi-country", False: "Single country"}).value_counts().to_frame("Papers")
    lead_country = (c.loc[~c["Multi-country"], "Countries"].value_counts().rename("Single-country papers").to_frame())

    # Sport
    multisport = c["Multi-sport"].value_counts().to_frame("Papers")
    multisport.index.name = "Multi-sport sample"
    sports_long = c["Sports"].str.split("; ").explode()
    sport_counts = sports_long.value_counts().to_frame("Papers")
    sport_counts.index.name = "Sport"
    sport_detail = c[["Reference", "Multi-sport", "Sports"]].join(v[["Sport Investigated"]])

    # Journal
    journal_counts = (c.reset_index().groupby("Journal")
                      .agg(Papers=("ID", "count"), IDs=("ID", lambda s: ", ".join(map(str, sorted(s)))),
                           First=("Year", "min"), Latest=("Year", "max"))
                      .sort_values("Papers", ascending=False))

    write_tables("01_publication", {
        "Papers": c[["Reference", "Year", "Journal", "N authors", "Countries", "Multi-sport", "Sports"]],
        "By year": by_year, "By period": by_period,
        "Authors": author_counts, "Team size": team_size,
        "Countries": country_counts, "Single vs multi": single_vs_multi,
        "Single-country papers": lead_country,
        "Multi-sport": multisport, "Sports": sport_counts, "Sport detail": sport_detail,
        "Journals": journal_counts,
    })

    stacked_bar(by_year[[x for x in ["Quantitative", "Qualitative", "Mixed methods"] if x in by_year]],
                "Publications per year, by approach", "01_publications_by_year", colours=APPROACH_COLOURS)
    hbar(explode_count(v["Country"], coding.countries), "Countries studied", "01_countries",
         note="Multi-country papers count once for each country.")
    hbar(sport_counts["Papers"], "Sports investigated", "01_sports",
         note="'Not specified' = multi-sport samples that do not name the sports. A paper can name two sports.")
    hbar(multisport["Papers"], "Multi-sport vs single-sport samples", "01_multisport")
    hbar(journal_counts["Papers"], "Journals", "01_journals")
    top = author_counts[author_counts["Papers"] > 1]["Papers"]
    if len(top):
        hbar(top, "Authors with more than one included paper", "01_authors")
    print("01_publication done")


if __name__ == "__main__":
    main()
