"""Break the variable / theme text blocks into one row per indicator.

The extraction text uses a consistent layout:

    Human Resources Capacity          <- heading (a dimension or other group)
    1. Board capacity (continuous, 5-point Likert scale): description
    2. ...

This module walks those lines and returns a long table:
    ID | Role (DV / IV / Control / Theme) | Dimension | Indicator | Measure type | Text
which answers "what did they look at with capacity?" and "how was it measured?".
"""
from __future__ import annotations

import re

import pandas as pd

from . import config
from .coding import is_na_text

ROLE_FIELDS = {
    "Dependent variable": "Dependent Variables",
    "Independent variable": "Independent Variables",
    "Control variable": "Control Variables",
    "Qualitative theme": "Key Themes (Qualitative Studies)",
}

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
    if is_na_text(text):
        return []
    rows, current = [], "Not grouped"
    for raw_line in str(text).splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("scope:"):
            continue
        m = ITEM.match(line)
        if not m:
            dim = _heading_dimension(line)
            if dim:
                current = dim
            elif not re.match(r"^RQ\d", line):
                current = "Other: " + re.split(r"[\(:]", line)[0].strip()[:60]
            continue
        body = m.group(1).strip()
        # Several controls can be packed into one comma list ("Age, gender, ...")
        name = re.split(r"[:\(]", body)[0].strip(" .")
        dim_here = current
        if current == "Not grouped":   # e.g. "volunteers_capita (Human Resources): ..."
            inline = re.search(r"\(([A-Z][A-Za-z ]+?)(?: Capacity)?\)", body)
            if inline and _heading_dimension(inline.group(1)):
                dim_here = _heading_dimension(inline.group(1))
        rows.append({
            "Role": role,
            "Dimension": dim_here,
            "Indicator": name[:120],
            "Measure type": measure_type(body) if role != "Qualitative theme" else "Qualitative (themes)",
            "Text": body,
        })
    return rows


def indicator_table(values: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pid, rec in values.iterrows():
        for role, field in ROLE_FIELDS.items():
            for r in parse_block(rec.get(field), role):
                rows.append({"ID": pid, **r})
    df = pd.DataFrame(rows)
    df["Is capacity dimension"] = df["Dimension"].isin(config.DIMENSIONS)
    return df


def critical_element_matrix(values: pd.DataFrame) -> pd.DataFrame:
    """Paper x critical element: True where the element's keywords appear in
    the paper's variables or themes. Keyword hits are a prompt to check, not a
    final coding decision."""
    fields = list(ROLE_FIELDS.values()) + config.PER_DIMENSION_IV + ["Critical Elements Notes"]
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
