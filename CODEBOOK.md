# Codebook

What every column in `organised_extraction.xlsx` means, the values it can take, and
the rule for deciding a value. Every paper check cites these rules by number
(e.g. "Codebook O-15"). If a paper raises a case the rules don't cover, decide it,
add the rule here, and log it under [Decisions log](#decisions-log).

Rules marked **(proposed)** are suggestions that still need your confirmation.

---

## 1. Framework: Hall et al. (2003) organisational capacity

All capacity coding follows Hall et al.'s (2003) conceptual framework of
organisational capacity. The framework has three parts:

| Part of the model | Position in figure | Used for |
|---|---|---|
| **Capacity dimensions** | Middle (inside the oval) | The five capacity columns (O-15 to O-19) and the Dimension column for indicators |
| **External factors** | Left | The External column (O-20) and external indicators |
| **Outputs and outcomes** | Right | Outcome variables that are results of capacity, not capacity itself |

### 1.1 Capacity dimensions (middle)

| Dimension | Hall et al. (2003) content | Examples in community sport clubs |
|---|---|---|
| **Human Resources Capacity** | Competence: core competencies, knowledge, skills, talents, know-how. Hall places it at the centre because it drives the other four | Volunteers, paid staff, board, coaches; their numbers, skills, training, enthusiasm, succession, retention |
| **Financial Capacity** | Expenses, revenues, assets, liabilities | Revenue sources and diversification, membership fees, subsidies, sponsorship, breaking even, reserves, financial problems |
| **Infrastructure and Process Capacity** | Infrastructure, processes **and culture**; products related to the internal structure or day-to-day operations (e.g. databases, manuals); information technology | Facilities (own or public, availability, condition), formalisation, policies, communication, IT and digitalisation, **organisational culture** |
| **Planning and Development Capacity** | Planning, research and development (e.g. strategic planning about mission, services and products, programme design, proposals) | Strategic and long-term plans, plan implementation, creativity, new programmes, readiness to develop |
| **Relationship and Network Capacity** | Relationships with clients, members, funders, collaborators, donors, suppliers, customers | Partnerships and cooperation with schools, municipalities, federations, sponsors, other clubs; quality of those relationships |

Organisational culture belongs to **Infrastructure and Process Capacity**.
Hall et al. list "processes and culture" in that box, so culture is not a separate
dimension.

### 1.2 External factors (left)

| Group | Hall et al. (2003) content | Examples in community sport clubs |
|---|---|---|
| **Environmental constraints and facilitators** | Economy, political environment, public policy, legal/regulatory, public trust, societal values, societal needs, demographics, competition with nonprofits, businesses and government, physical environment | Demographic change, competition from commercial providers or other clubs, government policy and bureaucracy, COVID-19 restrictions, community size, region |
| **Access to resources** | Human resources, technology, capital, information, public support (brand equity) | Availability of external funding or volunteers in the community, access to public facilities, support from an external agent |
| **Historical factors** | Past behaviour, activity and effectiveness; norms and values | Club age, tradition, past partnerships and their legacy |

### 1.3 Outputs and outcomes (right)

Services provided, populations served, goods produced, advocacy, policy influenced,
changes in behaviour. In clubs these include programme offers, membership growth,
social integration, health promotion, and inclusion of specific groups. These are
**results** of capacity, not capacity itself.

### 1.4 Critical elements (Doherty, Misener & Cuskelly, 2014)

Doherty et al. (2014) break each of Hall's five dimensions into critical elements
for community sport clubs:

| Dimension | Critical elements |
|---|---|
| Human Resources | Human capital, common focus, enthusiasm, volunteer succession, sufficient volunteers, volunteer continuity, development and support |
| Financial | Stable revenues, alternative sources of revenue, stable expenses, fiscal responsibility |
| Infrastructure and Process | Formalisation, adequate facilities, communication |
| Planning and Development | Strategic planning, creativity, plan implementation |
| Relationship and Network | Engagement with partners, bureaucratic partners, balanced relationships, dependable relationships, personal connection |

---

## 2. Overview tab (one row per paper)

| # | Column | Values | Rule |
|---|---|---|---|
| O-1 | ID | 1–30 | Fixed paper number. Never reused. |
| O-2 | Reference | `Surname & Surname (Year)` or `Surname et al. (Year)` | Use full surnames as printed, including compound ones (e.g. *Alonso Restrepo*). The year must equal the Year column. |
| O-3 | DOI | `https://doi.org/…` | As printed on the paper. |
| O-4 | Year | yyyy | **Print issue year.** If the paper appeared online first in an earlier year, note that in the evidence table. |
| O-5 | Journal | Full journal title | Title case, as on the journal's website. |
| O-6 | Countries | Country names separated by `; ` | Every country where data were collected. England, Scotland and Wales are listed separately when the paper does. |
| O-7 | Multi-sport | Yes / No | **Yes** if the sample covers more than one sport (including two named sports). **No** for a single sport. |
| O-8 | Sports | Sports separated by `; `, or `Not specified` | Name every sport the paper names. Use `Not specified` when the sample is multi-sport but the sports are not named. |
| O-9 | Approach | Quantitative / Qualitative / Mixed methods | As the paper describes its design. Mixed methods requires both strands to be analysed. |
| O-10 | Time design | Cross-sectional / Longitudinal / Both | **Longitudinal** only when the same units are measured at two or more time points. Retrospective accounts collected once are **cross-sectional**. One wave of a panel is cross-sectional. |
| O-11 | Research method | Survey: single wave · Survey: repeated waves (panel) · Survey: clubs + members (multilevel) · Case study (single) · Case study (multiple) · Interviews · Focus groups · Mixed methods · Social network analysis | **(proposed)** A case study with one case (one event, programme or organisation) is *single*, even if data come from several clubs. Two or more cases compared is *multiple*. |
| O-12 | Data collection | Online survey · Paper survey · Telephone survey · Survey (mode unspecified) · Interviews · Focus groups · Observation · Documents / secondary data, separated by `; ` | Every method used to collect data analysed in the paper. |
| O-13 | Club sample size | Number | Number of clubs or organisations in the final analysed sample. For case studies, the number of clubs studied. |
| O-14 | Participant sample size | Number or blank | Number of people who provided data (interviewees, focus-group participants, individual survey respondents such as members). Leave blank when the unit is the club and one representative answered per club. |
| O-15 | HR | TRUE / FALSE | **(proposed)** TRUE if the paper measures, analyses or reports findings on at least one element of this dimension (§1.1) as a variable or theme. A mention in the literature review alone is FALSE. |
| O-16 | Financial | TRUE / FALSE | As O-15. |
| O-17 | Infrastructure | TRUE / FALSE | As O-15. Organisational culture counts here (§1.1). |
| O-18 | Planning | TRUE / FALSE | As O-15. |
| O-19 | Relationships | TRUE / FALSE | As O-15. |
| O-20 | External | TRUE / FALSE | TRUE if the paper measures, analyses or reports findings on **any factor on the left of Hall's model** (§1.2): environmental constraints or facilitators, access to resources, or historical factors. This includes external agents, policy, COVID-19, demographics and competition. |
| O-21 | Critical elements used | Yes / Partly / No | **Yes**: data are coded or measured using Doherty et al.'s (2014) critical elements across the dimensions. **Partly**: some elements are used or adapted, or cited to justify specific variables. **No**: not used. |
| O-22 | Model families | Families separated by `; `, or blank | Statistical models used for the main analyses: Linear regression (OLS), Multilevel / mixed-effects, Logistic regression, Probit regression, Ordered logit, Fractional logit, Quantile regression, ANOVA / t-test, Non-parametric tests, Correlation / bivariate tests, Factor analysis (EFA/CFA), Social network analysis (QAP), Descriptive statistics. Blank for qualitative papers. |

---

## 3. Indicators (quantitative) tab (one row per variable)

| # | Column | Values | Rule |
|---|---|---|---|
| I-1 | ID | Paper ID | |
| I-2 | Reference | As O-2 | |
| I-3 | Role | Outcome (DV) · Predictor (IV) · Control · Moderator / interaction · Matching variable · Grouping variable · Compared variable · Associated variable · Scale item / factor · Measured only · Unclear | Role in the paper's **main** analysis. Models with an outcome: Outcome / Predictor / Control. Group comparisons (ANOVA, t-test, chi-square, Mann-Whitney): Grouping / Compared. Correlations: Associated. Factor analysis: Scale item. Descriptive: Measured only. |
| I-4 | Dimension | One of the five capacity dimensions (§1.1) · **External** (§1.2) · **Outputs and outcomes** (§1.3) · **Not capacity** (e.g. club size, sport type, year dummies) | **(proposed)** Classify by Hall's model rather than by the paper's own labels. Culture goes to Infrastructure and Process. Contextual factors such as community size, region, competition and demographic problems go to External. The current `Other: …` and `Not grouped` labels should be re-coded into these categories. |
| I-5 | Indicator | Variable name as used in the paper | Keep the paper's name (including codes such as `PROB_FIN`). |
| I-6 | Definition | Text or blank | What the variable captures, in the paper's words where possible, without scale or statistics. Leave blank if the paper gives no definition. |
| I-7 | Measure type | Binary / dummy · Likert / rating scale · Ratio / percentage / share · Count / amount · Categorical / ordinal bands · Composite index / factor · Network ties · Not stated | How the variable is scored in the analysis. |
| I-8 | Text | Original extraction text | Kept for reference. Do not edit. |

---

## 4. Limitations & future research tab (one row per point)

| # | Column | Values | Rule |
|---|---|---|---|
| L-1 | Type | Limitation / Future research | A **limitation** is a weakness the authors acknowledge. **Future research** is a direction they explicitly recommend. A limitation is not repeated as future research unless the authors also make it a recommendation. |
| L-2 | No. | 1, 2, … | Order within paper and type. |
| L-3 | Point | Paraphrase in UK English | One idea per row. |
| L-4 | Note | Text or blank | Where the points came from if the paper has no dedicated section. |

---

## 5. Evidence rules for paper checks

| Basis | Meaning |
|---|---|
| **Stated** | The paper says it directly. The quote shows it. |
| **Inferred** | A judgement applying a codebook rule. The reasoning names the rule. |
| **Not found** | The paper doesn't report it. The reasoning lists the sections searched. |

Every quote must be copied word for word from the PDF. The highlighter only marks
quotes it finds exactly, so a paraphrase is flagged ✗. Highlight colours are listed
in [HIGHLIGHT_COLOURS.md](HIGHLIGHT_COLOURS.md).

---

## Decisions log

| Date | Rule | Decision | Prompted by |
|---|---|---|---|
| 2026-11-20 | §1 | Capacity dimensions follow Hall et al. (2003), middle of the model. External = anything on the left of the model | User |
| 2026-11-20 | O-4 | Year = print issue year | User's edits to papers 1 and 2 |
| 2026-11-20 | §1.1 | Organisational culture belongs to Infrastructure and Process Capacity (Hall's "processes and culture") | Hall et al. (2003) figure |
