"""Turn free-text extraction fields into tidy, countable categories."""
from __future__ import annotations

import re

import pandas as pd

from . import config


def _split_list(text) -> list[str]:
    if pd.isna(text):
        return []
    parts = re.split(r",|;|\band\b|&", str(text))
    return [p.strip() for p in parts if p.strip()]


def authors(text) -> list[str]:
    if pd.isna(text):
        return []
    return [a.strip() for a in re.split(r",|;|&|\band\b", str(text)) if a.strip()]


def countries(text) -> list[str]:
    out = []
    for c in _split_list(text):
        c = re.sub(r"^the\s+", "", c, flags=re.I)
        c = {"The Netherlands": "Netherlands", "USA": "United States", "UK": "United Kingdom"}.get(c, c)
        c = c[0].upper() + c[1:] if c else c
        out.append(c)
    return out


def world_region(country: str) -> str:
    return config.COUNTRY_REGION.get(country, "Europe")


def sport_category(text) -> str:
    if pd.isna(text):
        return "Not reported"
    t = str(text)
    if t.lower().startswith("multi"):
        return "Multi-sport"
    t = re.sub(r"\([^)]*\)", "", t)          # drop parentheticals
    t = re.sub(r"\s+", " ", t).strip()
    return t[0].upper() + t[1:]


def approach(text) -> str:
    t = str(text).lower()
    if "mix" in t:
        return "Mixed methods"
    if "qual" in t:
        return "Qualitative"
    if "quant" in t:
        return "Quantitative"
    return "Not reported"


def time_design(text) -> str:
    t = str(text).lower()
    if t.startswith("both") or ("cross" in t and "longitudinal" in t):
        return "Both"
    if t.startswith("cross"):          # e.g. "Cross-sectional (2012 panel wave)"
        return "Cross-sectional"
    if "longitudinal" in t or "panel" in t:
        return "Longitudinal"
    return "Not reported"


def sample_band(n) -> str:
    n = pd.to_numeric(n, errors="coerce")
    if pd.isna(n):
        return "Not numeric"
    for upper, label in [(1, "1 (single case)"), (50, "2-50"), (500, "51-500"),
                         (5000, "501-5,000"), (float("inf"), ">5,000")]:
        if n <= upper:
            return label
    return "?"


SAMPLE_BAND_ORDER = ["1 (single case)", "2-50", "51-500", "501-5,000", ">5,000", "Not numeric"]


def tags(text, scheme) -> list[str]:
    if pd.isna(text):
        return []
    return [name for name, pat in scheme if re.search(pat, str(text), flags=re.I)]


def is_na_text(text) -> bool:
    """True for 'N/A (qualitative study)', 'None ...' style placeholders."""
    if pd.isna(text):
        return True
    return bool(re.match(r"^\s*(n/?a|none)\b", str(text), flags=re.I))


def model_lines(text) -> list[str]:
    if is_na_text(text):
        return []
    lines = [re.sub(r"^[•\-\*\d\.\s]+", "", l).strip() for l in str(text).splitlines()]
    return [l for l in lines if l]


def model_families(text) -> list[str]:
    fams = []
    for line in model_lines(text):
        for name, pat in config.MODEL_FAMILIES:
            if re.search(pat, line, flags=re.I):
                if name not in fams:
                    fams.append(name)
                break
        else:
            if "Other" not in fams:
                fams.append("Other")
    if not fams and isinstance(text, str) and re.search("descriptive", text, re.I):
        fams = ["Descriptive statistics"]
    return fams


def yes(v) -> bool:
    return str(v).strip().lower().startswith("y")


def coded_table(values: pd.DataFrame) -> pd.DataFrame:
    """One row per paper with simplified, analysis-ready columns."""
    from .load import short_ref

    df = pd.DataFrame(index=values.index)
    df["Reference"] = short_ref(values)
    df["Year"] = pd.to_numeric(values["Year of Publication"], errors="coerce").astype("Int64")
    df["Journal"] = values["Journal"]
    df["N authors"] = values["Authors"].map(lambda t: len(authors(t)))
    df["Countries"] = values["Country"].map(lambda t: "; ".join(countries(t)))
    df["N countries"] = values["Country"].map(lambda t: len(countries(t)))
    df["Multi-country"] = df["N countries"] > 1
    df["Sport category"] = values["Sport Investigated"].map(sport_category)
    df["Approach"] = values["Qualitative or Quantitative"].map(approach)
    df["Time design"] = values["Study Design"].map(time_design)
    df["Research method"] = values["Research Method"]
    df["Data collection"] = values["Data Collection Method"].map(
        lambda t: "; ".join(tags(t, config.COLLECTION_TAGS)))
    df["Sample size"] = pd.to_numeric(values["Final Club Sample Size"], errors="coerce").astype("Int64")
    df["Sample band"] = values["Final Club Sample Size"].map(sample_band)
    df["Respondent types"] = values["Respondents"].map(
        lambda t: "; ".join(tags(t, config.RESPONDENT_TAGS)))
    for d in config.DIMENSIONS + ["External Influences"]:
        df[config.DIMENSION_SHORT[d]] = values[d].map(yes)
    df["N dimensions"] = df[[config.DIMENSION_SHORT[d] for d in config.DIMENSIONS]].sum(axis=1)
    df["Critical elements used"] = values["Critical Elements Used"]
    df["Model families"] = values["Statistical Models"].map(lambda t: "; ".join(model_families(t)))
    return df
