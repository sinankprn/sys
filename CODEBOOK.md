# Codebook

What every column in `organised_extraction.xlsx` means, the values it can take, and
the rule for deciding a value.

**Column codes.** Every column header in the spreadsheet starts with a code:
**O** = Overview tab, **I** = Indicators (quantitative) tab, **L** = Limitations &
future research tab. For example, `O15 HR` is column 15 of the Overview. The same
code is used here, in each paper's checklist, and on the tag beside each highlight
in the PDFs.

Rules marked **(proposed)** still need your confirmation. If a paper raises a case
the rules don't cover, decide it, add the rule here, and log it under
[Decisions log](#decisions-log).

---

## 1. Framework: Hall et al. (2003)

All capacity coding follows the conceptual model of nonprofit and voluntary
organisational capacity in Hall et al. (2003). The model has three parts:

| Part | Position in Hall's figure | Spreadsheet columns |
|---|---|---|
| **External influences** | Left | O20 External |
| **Organisational capacities** | Middle | O15 HR, O16 Financial, O17 Infrastructure, O18 Planning, O19 Relationships |
| **Outputs and outcomes** | Right | No Overview column. Used to classify outcome variables (I4) |

Hall et al. define capacity as an organisation's ability to fulfil its mission by
drawing on three types of capital:
- **financial capital**
- **human capital**, the people or "thinking part" of the organisation
- **structural capital**, what remains "when the people from an organization have gone home"

Structural capacity has three sub-types: relationship and network, infrastructure
and process, and planning and development. Human capital is "the key element that
leads to the development of all other capacities".

### 1.1 Organisational capacities (O15–O19)

| Code | Column | Hall et al. (2003) definition | Includes, in community sport clubs | Boundary rules |
|---|---|---|---|---|
| **O15** | HR | **Human Resources Capacity**: the ability to deploy human capital (paid staff and volunteers) within the organisation, and the competencies, knowledge, attitudes, motivation and behaviours of these people | Number and share of volunteers and paid staff; board, coaches, officials; skills, qualifications and training; enthusiasm, commitment, common focus; recruitment, retention and succession problems | Members as *participants* are not HR (club size is "Not capacity"); members as *volunteers* are HR |
| **O16** | Financial | **Financial Capacity**: the ability to develop and deploy financial capital, i.e. revenues, expenses, assets and liabilities | Revenue amount and sources, diversification, membership fees, subsidies **received**, sponsorship income, expenses, reserves and assets, debt, breaking even, financial problems | Whether outside funding *exists or is available* in the environment is External (access to resources). The club's own revenue from it is Financial |
| **O17** | Infrastructure | **Infrastructure and Process Capacity** (structural): the ability to deploy or rely on infrastructure, processes **and culture**, products related to internal structure or day-to-day operations (e.g. databases, manuals, policies and procedures), information technology and intellectual property | Facilities (own, public, availability, condition); formalisation, policies and procedures, defined roles; internal communication; IT and digitalisation; **organisational culture and values** | Culture always belongs here, not in a separate dimension. A *policy document or plan for the future* is Planning (O18); day-to-day *procedures* are Infrastructure |
| **O18** | Planning | **Planning and Development Capacity** (structural): the ability to develop and draw on organisational strategic plans, programme plans and designs (including fundraising and volunteer management), policies and proposals | Strategic or long-term plans, plan implementation, programme design and new offers, development concepts, volunteer-management or fundraising plans, creativity, readiness to build capacity | Having *programmes* is an output (right of the model). *Planning or designing* them is Planning |
| **O19** | Relationships | **Relationship and Network Capacity** (structural): the ability to draw on relationships with clients, members, funders, partners, government, the media, corporations, volunteers and the public | Cooperation and partnerships with schools, municipalities, federations, other clubs, companies and sponsors; relationship quality (balanced, dependable, personal); network ties | The *relationship* is Relationships. Changes in the wider environment that partners belong to, e.g. government policy, are External (O20) |

### 1.2 External influences (O20)

Hall et al.: "three main types of external factors that can affect the performance
of nonprofit and voluntary organizations". An organisation's ability to develop or
maintain its capacities depends on them.

| Type | Hall et al. (2003) definition | Includes, in community sport clubs |
|---|---|---|
| **Environmental constraints and facilitators** | The political environment, public policy, the legal and regulatory framework, public trust and confidence in nonprofit institutions, societal values, societal needs, the demographic composition of the population, and competition among nonprofits, businesses and government. These are interdependent | Government and federation policy, bureaucracy and regulation, COVID-19 restrictions, demographic change, competition from commercial providers or other clubs, community size or urbanisation as context, economic conditions |
| **Access to resources** | Financial resources, human resources and technology available to the organisation. These are affected by the environmental factors | Availability of public funding programmes, of volunteers in the community, of public facilities; support, resources or withdrawal of an **external agent** |
| **Historical factors** | Past behaviours, activities and effectiveness (e.g. fundraising practices, ethical or unethical conduct, abuses of trust, perceived contributions), and norms and values (e.g. an ethos that attracts or discourages people or funders) | Club age and tradition, past partnerships and their legacy, earlier scandals or successes, sporting traditions in a country |

**O20 rule:** TRUE only if the paper's **data are segmented into external
influences**. That means it measures external factors as variables (e.g. "problems
with demographic development", "competition from commercial providers", policy or
COVID-19 measures), or it codes and reports findings under an external-influence
category (environmental constraints and facilitators, access to resources,
historical factors). A study whose topic or context involves an outside actor or
event is **not** enough on its own. For example, paper 1 studies an external agent's
withdrawal, but codes all its findings into the five capacities, so O20 is FALSE.
Mentions in the introduction or literature review are FALSE.

### 1.3 Outputs and outcomes (right of the model)

What the organisation produces and the results it intends. Hall et al.:
"outputs are secondary to the intended outcome of those outputs". In clubs these
include sport programmes and services offered, populations served (e.g. youth,
women, people with disabilities, people in poverty), membership development,
social integration, health effects, and advocacy. These are **results** of capacity,
not capacity. They are used only to classify outcome variables (I4).

### 1.4 Critical elements (Doherty, Misener & Cuskelly, 2014)

Doherty et al. (2014) break each of Hall's five capacities into critical elements
for community sport clubs:

| Capacity | Critical elements |
|---|---|
| Human Resources | Human capital, common focus, enthusiasm, volunteer succession, sufficient volunteers, volunteer continuity, development and support |
| Financial | Stable revenues, alternative sources of revenue, stable expenses, fiscal responsibility |
| Infrastructure and Process | Formalisation, adequate facilities, communication |
| Planning and Development | Strategic planning, creativity, plan implementation |
| Relationship and Network | Engagement with partners, bureaucratic partners, balanced relationships, dependable relationships, personal connection |

### 1.5 Rule for the capacity columns (O15–O19)

**(proposed)** TRUE if the paper measures, analyses or reports findings on at least
one element of that capacity (§1.1) as a variable or qualitative theme, whatever the
paper calls it. Classify by Hall's definitions, not the authors' labels. For example,
"cultural capacity" counts as O17. A mention only in the introduction or literature
review is FALSE.

---

## 2. Overview tab (one row per paper)

| Code | Column | Values | Rule |
|---|---|---|---|
| O1 | ID | 1–30 | Fixed paper number. Never reused. |
| O2 | Reference | `Surname & Surname (Year)` or `Surname et al. (Year)` | Full surnames as printed, including compound ones (e.g. *Alonso Restrepo*). The year must equal O4. |
| O3 | DOI | `https://doi.org/…` | As printed on the paper. |
| O4 | Year | yyyy | **Print issue year.** If the paper appeared online first in an earlier year, note that in the evidence. |
| O5 | Journal | Full journal title | As on the journal's website. |
| O6 | Countries | Country names separated by `; ` | Every country where data were collected. England, Scotland and Wales are listed separately when the paper does. |
| O7 | Multi-sport | Yes / No | **Yes** if the sample covers more than one sport (including two named sports). **No** for a single sport. |
| O8 | Sports | Sports separated by `; `, or `Not specified` | Every sport the paper names. `Not specified` when multi-sport but the sports aren't named. |
| O9 | Approach | Quantitative / Qualitative / Mixed methods | As the paper describes its design. Mixed methods requires both strands to be analysed. |
| O10 | Time design | Cross-sectional / Longitudinal / Both | **Longitudinal** only when the same units are measured at two or more time points. Retrospective accounts collected once, and one wave of a panel, are cross-sectional. |
| O11 | Research method | Survey: single wave · Survey: repeated waves (panel) · Survey: clubs + members (multilevel) · Case study · Interviews · Focus groups · Mixed methods · Social network analysis | Case studies are not split into single and multiple. |
| O12 | Data collection | Online survey · Paper survey · Telephone survey · Survey (mode unspecified) · Interviews · Focus groups · Observation · Documents / secondary data, separated by `; ` | Every method used to collect data that is analysed in the paper. |
| O13 | Club sample size | Number | Clubs or organisations in the final analysed sample. For case studies, the number of clubs studied. |
| O14 | Participant sample size | Number or blank | People who provided data (interviewees, focus-group participants, individual respondents such as members). Blank when one representative answered per club. |
| O15–O19 | HR, Financial, Infrastructure, Planning, Relationships | TRUE / FALSE | See §1.1 and §1.5. |
| O20 | External | TRUE / FALSE | See §1.2. |
| O21 | Critical elements used | Yes / Partly / No | **Yes**: data are coded or measured using Doherty et al.'s (2014) critical elements across the capacities. **Partly**: some elements are used or adapted, or cited to justify specific variables. **No**: not used. |
| O22 | Model families | Families separated by `; `, or blank | Statistical models used for the main analyses: Linear regression (OLS), Multilevel / mixed-effects, Logistic regression, Probit regression, Ordered logit, Fractional logit, Quantile regression, ANOVA / t-test, Non-parametric tests, Correlation / bivariate tests, Factor analysis (EFA/CFA), Social network analysis (QAP), Descriptive statistics. Blank for qualitative papers. |

---

## 3. Indicators (quantitative) tab (one row per variable)

| Code | Column | Values | Rule |
|---|---|---|---|
| I1 | ID | Paper ID | |
| I2 | Reference | As O2 | |
| I3 | Role | **Outcome (DV)** · **Predictor (IV)** · **Control** · **Measured only**. Several roles are separated by `; ` in that order, e.g. `Measured only; Outcome (DV)` is wrong, `Outcome (DV); Measured only` is right | One role for **each analysis the variable appears in**, combined. **Outcome**: what a model predicts or explains, including the measure compared across groups in ANOVA, t-tests, chi-square or Mann-Whitney tests. **Predictor**: a variable of interest used to explain the outcome, including the variable that defines the groups in those comparisons. **Control**: included to adjust or to match groups, not interpreted (includes matching variables). **Measured only**: used without a direction (descriptive statistics, correlations, factor analysis inputs). Which analysis gave which role is recorded in the evidence (Reasoning). |
| I4 | Dimension | Human Resources Capacity · Financial Capacity · Infrastructure and Process Capacity · Planning and Development Capacity · Relationship and Network Capacity · **External** · **Outputs and outcomes** · **Not capacity** | **(proposed)** Classify by Hall's model (§1), not by the paper's labels. Culture → Infrastructure and Process. Community size, region, competition, demographic or policy problems → External. Programme offers, members served, social functions → Outputs and outcomes. Club size, sport type, year dummies → Not capacity. The current `Other: …` and `Not grouped` labels should be re-coded into these. |
| I5 | Indicator | Variable name as used in the paper | Keep the paper's name (including codes such as `PROB_FIN`). |
| I6 | Definition | Text or blank | What the variable captures, in the paper's words where possible, without scale or statistics. Blank if the paper gives no definition. |
| I7 | Measure type | Binary / dummy · Likert / rating scale · Ratio / percentage / share · Count / amount · Categorical / ordinal bands · Composite index / factor · Network ties · Not stated | How the variable is scored in the analysis. |
| I8 | Text | Original extraction text | Kept for reference. Do not edit. |

---

## 4. Limitations & future research tab (one row per point)

| Code | Column | Values | Rule |
|---|---|---|---|
| L1 | ID | Paper ID | |
| L2 | Reference | As O2 | |
| L3 | Type | Limitation / Future research | A **limitation** is a weakness the authors acknowledge. **Future research** is a direction they recommend, including when it's phrased as a gap that needs attention (e.g. "an area in need of attention"). One sentence can therefore give both a limitation row and a future-research row. |
| L4 | No. | 1, 2, … | Order within paper and type. |
| L5 | Point | Paraphrase in UK English | One idea per row. |
| L6 | Note | Text or blank | Where the points came from if the paper has no dedicated section. |

---

## 5. Paper checks

Each checked paper has three linked outputs:
- a **checklist** (`checklists/paper_XX_checklist.xlsx`)
- an **evidence table** (`evidence/paper_XX.md`)
- a **highlighted PDF** (`highlighted/paper_XX_highlighted.pdf`)

The checklist has one sheet per spreadsheet tab. On the **Indicators** sheet each
variable is one row (tag `I-V1`, `I-V2`, …) with the spreadsheet's columns in the
same order: I3 Role, I4 Dimension, I5 Indicator, I6 Definition, I7 Measure type. A
proposed change appears in the cell as `current → suggested`. Evidence that applies
to several variables at once is tagged `I-S1`, `I-S2`, …

Every other item has a **tag**: the column code, plus a letter when one column has more
than one piece of evidence. For example, `O12a` and `O12b` are two quotes for Data
collection. Limitation and future-research points are tagged `L5-Lim1`, `L5-FR2`,
and so on. A `+` marks a point that is missing and suggested for adding (e.g. `L5-FR3+`). The tag is printed beside
the highlight in the PDF.

| Basis | Meaning |
|---|---|
| **Stated** | The paper says it directly. The quote shows it. |
| **Inferred** | A judgement applying a codebook rule. The reasoning names the rule. |
| **Not found** | The paper doesn't report it. The reasoning lists the sections searched. |

| Status | Meaning |
|---|---|
| **Matches** | The paper supports the value in the spreadsheet. |
| **Suggest change** | The paper or a codebook rule points to a different value (shown under Suggested). |
| **Decision needed** | The rules don't settle it. Decide, then add a rule to this codebook. |

Every quote is copied word for word from the PDF. The highlighter only marks quotes
it finds exactly, so a paraphrase is flagged ✗. Colours are in
[HIGHLIGHT_COLOURS.md](HIGHLIGHT_COLOURS.md).

---

## Decisions log

| Date | Rule | Decision | Prompted by |
|---|---|---|---|
| 2026-11-20 | §1 | Capacity columns follow Hall et al. (2003), the middle of the model. External = the three types of external influences on the left | User |
| 2026-11-20 | §1.1, §1.2 | Definitions taken from Hall et al. (2003), pp. 5–7 | User (Hall et al. text) |
| 2026-11-20 | O4 | Year = print issue year | User's edits to papers 1 and 2 |
| 2026-11-20 | O17 | Organisational culture belongs to Infrastructure and Process ("processes and culture") | Hall et al. (2003) |
| 2026-11-20 | All | Column codes O1–O22, I1–I8, L1–L6 added to spreadsheet headers | User |
| 2026-11-20 | O11 | Case studies are recorded as "Case study", with no single/multiple split. Papers 10, 12, 13 and 20 re-coded to match | Paper 1 checklist (O11) |
| 2026-11-20 | O20 | External = TRUE only when the data are segmented into external influences (measured as variables or coded as categories). A topic involving an outside actor is not enough | Paper 1 checklist (O20a–c) |
| 2026-11-20 | I3 | Role limited to 6 values. Matching variable → Control (7 variables, papers 7 and 27); Associated variable → Measured only (20 variables, paper 9) | Paper 2 checklist redesign |
| 2026-11-20 | I3 | Roles reduced to 4; a variable takes one role per analysis it appears in, separated by "; ". Compared variable → Outcome (DV) (59 variables, papers 2, 7, 26); Grouping variable → Predictor (IV) (6 variables, papers 2, 7, 27) | Paper 2 (EFA + ANOVA + correlations on the same variables) |
| 2026-11-20 | L3 | A gap described as needing attention counts as a future-research suggestion, even when it is also a limitation | Paper 1 checklist (L5-FR2) |
