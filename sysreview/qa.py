"""Data-quality checks on the extraction. Each check returns issue rows:
    ID | Field | Severity | Check | Detail
Severity: High = probably wrong or missing; Medium = needs a look; Info = confirm.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request

import pandas as pd

from . import coding, config
from .indicators import critical_element_matrix, indicator_table, theme_table

DOHERTY_YEAR = 2014


def _issue(pid, field, sev, check, detail):
    return {"ID": pid, "Field": field, "Severity": sev, "Check": check, "Detail": detail}


def check_blanks(v, c):
    out = []
    for pid, rec in v.iterrows():
        quantish = c.at[pid, "Approach"] != "Qualitative"
        blank_iv = []
        for f in v.columns:
            if f in config.OPTIONAL_FIELDS or not pd.isna(rec[f]):
                continue
            if f in config.PER_DIMENSION_IV:
                dim = f.replace(" IV", "")
                if quantish and dim in config.DIMENSIONS and coding.yes(rec.get(dim)):
                    blank_iv.append(config.DIMENSION_SHORT[dim])
            else:
                out.append(_issue(pid, f, "High", "Blank field", "No value entered."))
        if blank_iv:
            out.append(_issue(pid, "Independent Variables", "Medium", "Blank per-dimension IV columns",
                              f"Dimensions coded Yes but their IV column is blank: {', '.join(blank_iv)}. "
                              "Fill them, or drop those columns and rely on 'Independent Variables'."))
    return out


def check_not_reported(v):
    out, pat = [], re.compile(r"not reported|not specified|not stated|unclear|not clear", re.I)
    for pid, rec in v.iterrows():
        for f in v.columns:
            val = rec[f]
            if isinstance(val, str) and pat.search(val):
                hits = sorted({m.group(0).lower() for m in pat.finditer(val)})
                lines = [l.strip() for l in val.splitlines() if pat.search(l)]
                out.append(_issue(pid, f, "Info", "Recorded as not reported",
                                  f"{', '.join(hits)} - confirm against paper: " + " | ".join(lines)[:300]))
    return out


def check_consistency(v, c):
    out = []
    ind = indicator_table(v)
    themes = theme_table(v)
    ce = critical_element_matrix(v)
    for pid, rec in v.iterrows():
        appr, year = c.at[pid, "Approach"], c.at[pid, "Year"]
        models = rec["Statistical Models"]
        # approach vs models
        if appr == "Qualitative" and not coding.is_na_text(models):
            out.append(_issue(pid, "Statistical Models", "High", "Approach vs models",
                              "Qualitative paper but statistical models listed."))
        if appr != "Qualitative" and coding.is_na_text(models):
            out.append(_issue(pid, "Statistical Models", "Medium", "Approach vs models",
                              f"{appr} paper with no inferential model: '{str(models)[:80]}'. Confirm."))
        if appr == "Qualitative" and coding.is_na_text(rec["Key Themes (Qualitative Studies)"]):
            out.append(_issue(pid, "Key Themes (Qualitative Studies)", "High", "Approach vs themes",
                              "Qualitative paper without key themes."))
        # dimension flags vs what the variables/themes actually contain
        found = set(ind.loc[ind["ID"] == pid, "Dimension"]) | set(themes.loc[themes["ID"] == pid, "Dimension"])
        for d in config.DIMENSIONS:
            flag = coding.yes(rec[d])
            if flag and d not in found:
                out.append(_issue(pid, d, "Medium", "Dimension flag vs variables",
                                  "Coded Yes, but no variable/theme was found under this dimension heading."))
            if not flag and d in found:
                out.append(_issue(pid, d, "High", "Dimension flag vs variables",
                                  "Coded No, but variables/themes are listed under this dimension."))
        # critical elements
        ce_hits = [e for (_, e), hit in ce.loc[pid].items() if hit]
        used = str(rec["Critical Elements Used"]).strip()
        if used.lower() == "no" and len(ce_hits) >= 3:
            out.append(_issue(pid, "Critical Elements Used", "Medium", "Critical elements",
                              f"Coded No, but {len(ce_hits)} element keywords found: {', '.join(ce_hits)}."))
        if used.lower() == "yes" and pd.notna(year) and year < DOHERTY_YEAR:
            out.append(_issue(pid, "Critical Elements Used", "High", "Critical elements",
                              f"Coded Yes but published {year}, before Doherty et al. (2014)."))
        notes = str(rec["Critical Elements Notes"])
        if pd.notna(year):
            if "Published before Doherty" in notes and year >= DOHERTY_YEAR:
                out.append(_issue(pid, "Critical Elements Notes", "High", "Critical elements",
                                  f"Note says published before 2014, but year is {year}."))
            if "Published after Doherty" in notes and year < DOHERTY_YEAR:
                out.append(_issue(pid, "Critical Elements Notes", "High", "Critical elements",
                                  f"Note says published after 2014, but year is {year}."))
        # sample size
        n = pd.to_numeric(rec["Final Club Sample Size"], errors="coerce")
        if pd.isna(n):
            out.append(_issue(pid, "Final Club Sample Size", "High", "Sample size",
                              f"Not numeric: '{rec['Final Club Sample Size']}'."))
        crit = str(rec["Criteria"])
        m = re.search(r"Final sample:\s*([^\n]+)", crit)
        if m and re.search(r"participant|interview|people|respondent|individual|member", m.group(1), re.I) \
                and not re.search(r"club|organi[sz]ation|CSO|VSC|case", m.group(1), re.I):
            out.append(_issue(pid, "Final Club Sample Size", "Medium", "Sample unit",
                              f"Value {rec['Final Club Sample Size']} may count people, not clubs: '{m.group(1)[:120]}'."))
        if m and pd.notna(n):
            nums = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", m.group(1))]
            if nums and int(n) not in nums:
                out.append(_issue(pid, "Final Club Sample Size", "Medium", "Sample size",
                                  f"Sheet value {int(n)} does not appear in Criteria 'Final sample: {m.group(1)[:120]}'."))
        # fixed categories that could not be pinned down
        rm = c.at[pid, "Research method"]
        if rm in ("Case study (type not stated)", "Not classified"):
            out.append(_issue(pid, "Research Method", "Medium", "Research method category",
                              f"Classified as '{rm}' from '{rec['Research Method']}'. "
                              "Edit the text (e.g. 'Case study (single)' or 'Case study (multiple)') to fix."))
        if c.at[pid, "Respondent type"] == config.RESPONDENT_FALLBACK:
            out.append(_issue(pid, "Respondents", "Info", "Respondent category",
                              "Role of respondents not specified - check the paper for who completed the survey."))
        # design wording
        if c.at[pid, "Time design"] == "Not reported":
            out.append(_issue(pid, "Study Design", "High", "Design", f"Unrecognised design '{rec['Study Design']}'."))
        if c.at[pid, "Time design"] == "Longitudinal" and re.search(r"one wave|single wave", str(rec["Research Method"]), re.I):
            out.append(_issue(pid, "Study Design", "Medium", "Design", "Longitudinal but method says one wave."))
        # bibliographic
        doi = str(rec["DOI"])
        if not re.search(r"10\.\d{4,9}/\S+", doi):
            out.append(_issue(pid, "DOI", "High", "DOI format", f"Unrecognised DOI '{doi}'."))
        if pd.isna(year) or not 1990 <= year <= 2026:
            out.append(_issue(pid, "Year of Publication", "High", "Year", f"Implausible year '{year}'."))
        # measurement detail missing for variables
        q = ind[(ind["ID"] == pid) & ind["Source column"].isin(["Independent Variables", "Dependent Variables"])]
        missing = q[q["Measure type"] == "Not stated"]
        if len(q) and len(missing) / len(q) > 0.4:
            out.append(_issue(pid, "Independent Variables", "Medium", "Measurement detail",
                              f"{len(missing)} of {len(q)} variables have no measurement type/scale recorded "
                              f"(e.g. {', '.join(missing['Indicator'].head(4))})."))
    # duplicate DOIs / titles
    for f in ["DOI", "Paper Title"]:
        key = v[f].astype(str).str.lower().str.strip()
        for pid in key[key.duplicated(keep=False)].index:
            out.append(_issue(pid, f, "High", "Duplicate", f"Same {f} as another paper."))
    # shared samples
    key = v["Country"].astype(str) + "|" + v["Region"].astype(str) + "|" + v["Final Club Sample Size"].astype(str)
    for pid in key[key.duplicated(keep=False)].index:
        others = [str(i) for i in key[key == key[pid]].index if i != pid]
        out.append(_issue(pid, "Final Club Sample Size", "Info", "Shared dataset",
                          f"Same country/region/N as paper(s) {', '.join(others)}: likely the same sample. "
                          "Record a 'Dataset' ID so samples are not double counted."))
    # country list
    try:
        allowed = set(pd.read_excel(config.RAW_WORKBOOK, sheet_name="Lists").iloc[:, 0].dropna().astype(str))
        allowed |= {"Netherlands"}
        for pid, rec in v.iterrows():
            for ctry in coding.countries(rec["Country"]):
                if allowed and ctry not in allowed:
                    out.append(_issue(pid, "Country", "Info", "Country list",
                                      f"'{ctry}' is not in the Lists sheet (dashboard may miss it)."))
    except Exception:
        pass
    return out


def check_unverified(v, ticks):
    out = []
    for pid in v.index:
        if pid not in ticks.index:
            continue
        unt = [f for f in ticks.columns if not ticks.at[pid, f]]
        if unt:
            out.append(_issue(pid, "(all)", "Info", "Not yet verified",
                              f"{len(unt)} of {len(ticks.columns)} fields unticked."))
    return out


# ---------------------------------------------------------------- Crossref
def _norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def crossref_check(v, sleep=0.5):
    """Compare title / year / journal / first author with Crossref metadata.
    Needs internet access to api.crossref.org."""
    out, rows, failures = [], [], 0
    for pid, rec in v.iterrows():
        m = re.search(r"10\.\d{4,9}/\S+", str(rec["DOI"]))
        if not m:
            continue
        doi = m.group(0).rstrip(".")
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sysreview-extraction-check/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                msg = json.load(r)["message"]
        except Exception as e:  # noqa: BLE001
            failures += 1
            if failures >= 3 and not rows:
                print(f"Crossref unreachable ({e}); skipping Crossref checks.")
                return [], pd.DataFrame()
            out.append(_issue(pid, "DOI", "Medium", "Crossref", f"Lookup failed: {e}"))
            continue
        cr_title = (msg.get("title") or [""])[0]
        cr_journal = (msg.get("container-title") or [""])[0]
        cr_years = {p[0] for k in ("published-print", "published-online", "issued")
                    for p in (msg.get(k) or {}).get("date-parts", [[None]]) if p and p[0]}
        cr_authors = [a.get("family", "") for a in msg.get("author", [])]
        rows.append({"ID": pid, "Crossref title": cr_title, "Crossref journal": cr_journal,
                     "Crossref year(s)": ", ".join(map(str, sorted(cr_years))),
                     "Crossref authors": ", ".join(cr_authors)})
        if _norm(cr_title)[:60] != _norm(rec["Paper Title"])[:60]:
            out.append(_issue(pid, "Paper Title", "Medium", "Crossref", f"Crossref title: '{cr_title}'"))
        if _norm(cr_journal) != _norm(rec["Journal"]):
            out.append(_issue(pid, "Journal", "Medium", "Crossref", f"Crossref journal: '{cr_journal}'"))
        try:
            y = int(rec["Year of Publication"])
        except (TypeError, ValueError):
            y = None
        if cr_years and y not in cr_years:
            out.append(_issue(pid, "Year of Publication", "Medium", "Crossref",
                              f"Crossref year(s): {sorted(cr_years)} (online-first vs print can differ; pick one rule)."))
        sheet_authors = coding.authors(rec["Authors"])
        if cr_authors and len(cr_authors) != len(sheet_authors):
            out.append(_issue(pid, "Authors", "Medium", "Crossref",
                              f"{len(sheet_authors)} authors in sheet vs {len(cr_authors)} in Crossref: {', '.join(cr_authors)}"))
        elif cr_authors and _norm(cr_authors[0]) not in _norm(sheet_authors[0] if sheet_authors else ""):
            out.append(_issue(pid, "Authors", "Medium", "Crossref",
                              f"First author differs: Crossref '{cr_authors[0]}'."))
        time.sleep(sleep)
    return out, pd.DataFrame(rows)


def run_all(v, ticks, crossref=False):
    c = coding.coded_table(v)
    issues = (check_blanks(v, c) + check_not_reported(v) + check_consistency(v, c)
              + check_unverified(v, ticks))
    cr = pd.DataFrame()
    if crossref:
        extra, cr = crossref_check(v)
        issues += extra
    df = pd.DataFrame(issues)
    df["Reference"] = df["ID"].map(c["Reference"])
    order = {"High": 0, "Medium": 1, "Info": 2}
    df = df.sort_values(["ID", "Severity", "Field"], key=lambda s: s.map(order) if s.name == "Severity" else s)
    return df[["ID", "Reference", "Field", "Severity", "Check", "Detail"]], cr
