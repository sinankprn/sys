"""Break the variable / theme text blocks into one row per indicator.

The extraction text uses a consistent layout:

    Human Resources Capacity          <- heading (a dimension or other group)
    1. Board capacity (continuous, 5-point Likert scale): description
    2. ...

This module walks those lines and returns two separate long tables:

- indicator_table(): quantitative variables only
    ID | Source column | Role | Role basis | Dimension | Indicator | Measure type | Text
  Role is fitted to the paper's analysis (outcome/predictor/control for models;
  grouping/compared/associated/etc. for ANOVA, correlations, EFA, descriptives).
  answers "what did they look at with capacity?" and "how was it measured?".
- theme_table(): qualitative themes only (Key Themes column)
    ID | Research question | Dimension | Theme | Text
"""
from __future__ import annotations

import re

import pandas as pd

from . import config
from .coding import is_na_text, model_families

ROLE_FIELDS = {
    "Dependent variable": "Dependent Variables",
    "Independent variable": "Independent Variables",
    "Control variable": "Control Variables",
}
THEME_FIELD = "Key Themes (Qualitative Studies)"

MEASURE_TYPES = [
    ("Likert / rating scale", r"likert|\d-point|1 = no problem|1 = not at all|1 = strongly|scale\)|rating|\b1 \(?[a-z ]*\)? ?to [5-7]\b|\b1 to [5-7]\b"),
    ("Binary / dummy", r"binary|dummy|yes ?/ ?no|\(yes\)|1 = yes|1 = agree|0 = |0/1|\byes or no\b|\bvs\b"),
    ("Categorical / ordinal bands", r"ordinal|categor|bands|ref\.|reference\)|< ?€|<\d"),
    ("Composite index / factor", r"composite|index|factor|sum score|alpha|α|mean of"),
    ("Ratio / percentage / share", r"%|share|proportion|ratio|per member|per capita|_capita|divided by"),
    ("Count / amount", r"count|number of|€|eur\b|us\$|hours|years|\bage\b"),
    ("Network ties", r"\bties\b|dyadic|matri"),
]


def measure_type(text: str) -> str:
    for name, pat in MEASURE_TYPES:
        if re.search(pat, text, flags=re.I):
            return name
    return "Not stated"


def _heading_dimension(line: str) -> str | None:
    low = line.lower()
    for d in config.DIMENSIONS + ["External Influences"]:
        if low.startswith(d.lower()):
            return d
    # Short/variant spellings used in some papers' headings
    for key, d in [("human resource", "Human Resources Capacity"),
                   ("financ", "Financial Capacity"),
                   ("infrastructure", "Infrastructure and Process Capacity"),
                   ("planning", "Planning and Development Capacity"),
                   ("relationship", "Relationship and Network Capacity"),
                   ("network", "Relationship and Network Capacity"),
                   ("external", "External Influences")]:
        if low.startswith(key):
            return d
    return None


ITEM = re.compile(r"^\s*(?:\d+[\.\)]|[•\-\*])\s*(.+)$")


def parse_block(text, role: str) -> list[dict]:
    """Parse one text block into rows. role='Qualitative theme' for Key Themes."""
    if is_na_text(text):
        return []
    rows, current, rq, heading, scope = [], "Not grouped", "", "", ""
    for raw_line in str(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("scope:"):
            scope = line
            continue
        m = ITEM.match(line)
        if not m:
            rq_match = re.match(r"^(RQ\d+)\s*:?\s*(.*)$", line)
            if rq_match:
                rq = line
                current = "Not grouped"
                continue
            dim = _heading_dimension(line)
            current = dim if dim else "Other: " + re.split(r"[\(:]", line)[0].strip()[:60]
            heading = line
            continue
        body = m.group(1).strip()
        name = re.split(r"[:\(]", body)[0].strip(" .")
        dim_here = current
        if current == "Not grouped":   # e.g. "volunteers_capita (Human Resources): ..."
            inline = re.search(r"\(([A-Z][A-Za-z ]+?)(?: Capacity)?\)", body)
            if inline and _heading_dimension(inline.group(1)):
                dim_here = _heading_dimension(inline.group(1))
        row = {"Role": role, "Research question": rq, "Dimension": dim_here,
               "Indicator": name[:120], "Text": body, "_context": f"{scope} {heading}"}
        if role != "Qualitative theme":
            row["Measure type"] = measure_type(body)
        rows.append(row)
    return rows


SOURCE_LABEL = {"Dependent variable": "Dependent Variables",
                "Independent variable": "Independent Variables",
                "Control variable": "Control Variables"}


def analysis_profile(models_text) -> dict:
    fams = set(model_families(models_text))
    # Also scan placeholder text such as "N/A (descriptive; ... correlations only)"
    if isinstance(models_text, str):
        fams |= {name for name, pat in config.MODEL_FAMILIES if re.search(pat, models_text, re.I)}
    return {
        "outcome_model": bool(fams & config.OUTCOME_MODEL_FAMILIES),
        "comparison": bool(fams & config.COMPARISON_FAMILIES),
        "correlation": "Correlation / bivariate tests" in fams,
        "factor": "Factor analysis (EFA/CFA)" in fams,
    }


def auto_role(source: str, context: str, text: str, prof: dict) -> tuple[str, str]:
    """Best-guess role and the basis for it. Basis wording ending in 'check'
    means the guess is weak and worth confirming against the paper."""
    cue = f"{context} {text}".lower()
    if "grouping" in cue:
        return "Grouping variable", "Stated in extraction (heading)"
    if "matching" in cue:
        return "Matching variable", "Stated in extraction (heading)"
    if re.search(r"moderat|interaction", cue):
        return "Moderator / interaction", "Stated in extraction (text)"
    if re.search(r"no iv/dv roles|measured variables", cue):
        if prof["comparison"]:
            return "Compared variable", "Extraction says no IV/DV roles; paper uses group comparisons - check"
        return "Measured only", "Stated in extraction (heading)"

    if prof["outcome_model"]:
        role = {"Dependent variable": "Outcome (DV)", "Independent variable": "Predictor (IV)",
                "Control variable": "Control"}[source]
        if prof["comparison"] or prof["factor"]:
            return role, f"From '{SOURCE_LABEL[source]}' column; paper also runs comparisons/factor analysis - check which analysis"
        return role, f"From '{SOURCE_LABEL[source]}' column"

    # No model with an outcome: translate DV/IV/control into analysis-appropriate roles
    if prof["comparison"]:
        role = "Compared variable" if source == "Dependent variable" else "Grouping variable"
        return role, "No outcome model; paper uses group comparisons - check"
    if prof["correlation"]:
        return "Associated variable", "No outcome model; correlations only"
    if prof["factor"]:
        return "Scale item / factor", "No outcome model; factor analysis"
    return "Measured only", "No outcome model; descriptive"


def read_role_overrides() -> pd.DataFrame:
    p = config.ROLES_CSV
    if not p.exists():
        return pd.DataFrame(columns=["ID", "Source column", "Indicator", "Role"])
    return pd.read_csv(p, dtype={"ID": int})


def indicator_table(values: pd.DataFrame, apply_overrides: bool = True) -> pd.DataFrame:
    """Quantitative variables, one row each. Qualitative themes are excluded.

    Source column = where the variable sits in the extraction sheet.
    Role          = what it does in the analysis (see config.VARIABLE_ROLES),
                    guessed automatically and overridden by reviewer decisions in
                    data/corrections/indicator_roles.csv.
    """
    rows = []
    for pid, rec in values.iterrows():
        prof = analysis_profile(rec.get("Statistical Models"))
        for source, field in ROLE_FIELDS.items():
            for r in parse_block(rec.get(field), source):
                role, basis = auto_role(source, r["_context"], r["Text"], prof)
                rows.append({"ID": pid, "Source column": SOURCE_LABEL[source], "Role": role,
                             "Role basis": basis, "Dimension": r["Dimension"],
                             "Indicator": r["Indicator"], "Measure type": r["Measure type"],
                             "Text": r["Text"]})
    df = pd.DataFrame(rows, columns=["ID", "Source column", "Role", "Role basis", "Dimension",
                                     "Indicator", "Measure type", "Text"])
    if apply_overrides:
        ov = read_role_overrides()
        if len(ov):
            key = ["ID", "Source column", "Indicator"]
            df = df.merge(ov[key + ["Role"]].rename(columns={"Role": "_override"}), on=key, how="left")
            hit = df["_override"].notna()
            df.loc[hit, "Role"] = df.loc[hit, "_override"]
            df.loc[hit, "Role basis"] = "Confirmed by reviewer"
            df = df.drop(columns="_override")
    df["Is capacity dimension"] = df["Dimension"].isin(config.DIMENSIONS)
    return df


def theme_table(values: pd.DataFrame) -> pd.DataFrame:
    """Qualitative themes from the Key Themes column, one row per theme."""
    rows = []
    for pid, rec in values.iterrows():
        for r in parse_block(rec.get(THEME_FIELD), "Qualitative theme"):
            r.pop("_context", None)
            rows.append({"ID": pid, "Research question": r["Research question"],
                         "Dimension": r["Dimension"], "Theme": r["Indicator"], "Text": r["Text"]})
    df = pd.DataFrame(rows, columns=["ID", "Research question", "Dimension", "Theme", "Text"])
    df["Is capacity dimension"] = df["Dimension"].isin(config.DIMENSIONS)
    return df


def critical_element_matrix(values: pd.DataFrame) -> pd.DataFrame:
    """Paper x critical element: True where the element's keywords appear in
    the paper's variables or themes. Keyword hits are a prompt to check, not a
    final coding decision."""
    fields = list(ROLE_FIELDS.values()) + [THEME_FIELD] + config.PER_DIMENSION_IV + ["Critical Elements Notes"]
    out = {}
    for pid, rec in values.iterrows():
        blob = " \n".join(str(rec.get(f, "")) for f in fields if not pd.isna(rec.get(f)))
        row = {}
        for dim, elements in config.CRITICAL_ELEMENTS.items():
            for el, pat in elements.items():
                row[(config.DIMENSION_SHORT[dim], el)] = bool(re.search(pat, blob, flags=re.I))
        out[pid] = row
    m = pd.DataFrame(out).T
    m.columns = pd.MultiIndex.from_tuples(m.columns, names=["Dimension", "Critical element"])
    m.index.name = "ID"
    return m
