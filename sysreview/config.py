"""Project-wide settings: file locations, field groups and coding schemes.

Edit the coding schemes here (not inside the scripts) if you want to change
how free text is grouped into categories.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_WORKBOOK = ROOT / "data" / "raw" / "extraction.xlsx"
DATA_SHEET = "Sheet1"
CORRECTIONS_CSV = ROOT / "data" / "corrections" / "corrections.csv"
VERIFICATIONS_CSV = ROOT / "data" / "corrections" / "verifications.csv"
ROLES_CSV = ROOT / "data" / "corrections" / "indicator_roles.csv"
OUTPUT = ROOT / "output"
TABLES = OUTPUT / "tables"
FIGURES = OUTPUT / "figures"
REVIEW = OUTPUT / "review"

# The five Hall et al. (2003) dimensions, plus the extra flag used in the sheet.
DIMENSIONS = [
    "Human Resources Capacity",
    "Financial Capacity",
    "Infrastructure and Process Capacity",
    "Planning and Development Capacity",
    "Relationship and Network Capacity",
]
DIMENSION_SHORT = {
    "Human Resources Capacity": "HR",
    "Financial Capacity": "Financial",
    "Infrastructure and Process Capacity": "Infrastructure",
    "Planning and Development Capacity": "Planning",
    "Relationship and Network Capacity": "Relationships",
    "External Influences": "External",
}

# Field groups, used to order the review workbook and the QA report.
SECTIONS = {
    "Publication": ["Authors", "Paper Title", "Year of Publication", "Journal", "DOI"],
    "Aims": ["Research Question/s"],
    "Sample": ["Sport Investigated", "Sampling Strategy", "Sampling", "Criteria",
               "Final Club Sample Size", "Country", "Region", "Respondents"],
    "Design": ["Study Design", "Qualitative or Quantitative", "Research Method",
               "Data Collection Method", "Data Analysis"],
    "Capacity": DIMENSIONS + ["External Influences", "Capacity Dimension Notes",
                              "Critical Elements Used", "Critical Elements Notes"],
    "Modelling": ["Statistical Models", "Dependent Variables",
                  "Human Resources Capacity IV", "Financial Capacity IV",
                  "Relationship and Network Capacity IV",
                  "Infrastructure and Process Capacity IV",
                  "Planning and Development Capacity IV", "Other IV",
                  "Independent Variables", "Control Variables"],
    "Qualitative": ["Key Themes (Qualitative Studies)"],
    "Findings": ["Limitations", "Future Research"],
}

# Fields that may legitimately be blank (optional notes).
OPTIONAL_FIELDS = {"Capacity Dimension Notes"}

# Per-dimension IV columns are only expected for quantitative / mixed papers.
PER_DIMENSION_IV = [
    "Human Resources Capacity IV", "Financial Capacity IV",
    "Relationship and Network Capacity IV", "Infrastructure and Process Capacity IV",
    "Planning and Development Capacity IV", "Other IV",
]

# Statistical model families: first matching pattern wins per bullet line, but a
# paper can belong to several families. Order matters (specific before general).
MODEL_FAMILIES = [
    ("Social network analysis (QAP)", r"\bQAP\b|network analysis"),
    ("Multilevel / mixed-effects", r"multilevel|mixed[- ]effects|mixed models|random intercept"),
    ("Probit regression", r"probit"),
    ("Ordered logit", r"ordered logit|ordinal logit"),
    ("Fractional logit", r"fractional"),
    ("Logistic regression", r"logistic|\blogit\b"),
    ("Quantile regression", r"quantile"),
    ("Linear regression (OLS)", r"\bOLS\b|linear regression|multiple regression|regression \(OLS"),
    ("Factor analysis (EFA/CFA)", r"factor analysis"),
    ("ANOVA / t-test", r"ANOVA|t-test"),
    ("Non-parametric tests", r"Mann-Whitney|Kruskal|Chi-square|Wilcoxon"),
    ("Correlation / bivariate tests", r"correlation|bivariate"),
    ("Qualitative analysis (mixed-methods strand)", r"thematic|content analysis"),
    ("Descriptive statistics", r"descriptive"),
]

# Roles a variable can play in the Indicators sheet. Not every analysis has an
# outcome: group comparisons, correlations and factor analyses use the last five.
VARIABLE_ROLES = [
    "Outcome (DV)",          # regression / model outcome
    "Predictor (IV)",        # regression / model predictor of interest
    "Control",               # included to adjust, not interpreted
    "Moderator / interaction",
    "Matching variable",     # used to build comparison groups
    "Grouping variable",     # defines the groups in ANOVA / t-test / chi-square / Mann-Whitney
    "Compared variable",     # measured and compared across groups
    "Associated variable",   # correlation: neither side is the outcome
    "Scale item / factor",   # factor analysis / scale development
    "Measured only",         # descriptive, no analytic role
    "Unclear",
]
# Model families that have an outcome variable.
OUTCOME_MODEL_FAMILIES = {
    "Social network analysis (QAP)", "Multilevel / mixed-effects", "Probit regression",
    "Ordered logit", "Fractional logit", "Logistic regression", "Quantile regression",
    "Linear regression (OLS)",
}
COMPARISON_FAMILIES = {"ANOVA / t-test", "Non-parametric tests"}

# Doherty, Misener & Cuskelly (2014) critical elements, with keyword patterns used
# to find them in each paper's variables / themes. CHECK this list against
# Table 1 of Doherty et al. (2014) and add or rename elements as needed.
CRITICAL_ELEMENTS = {
    "Human Resources Capacity": {
        "Human capital": r"human capital",
        "Common focus": r"common focus|inner ?cohesion",
        "Enthusiasm": r"enthusias",
        "Volunteer succession": r"succession",
        "Sufficient volunteers": r"sufficient volunteers",
        "Volunteer continuity": r"continuity",
        "Development and support": r"development and support|training of volunteers",
    },
    "Financial Capacity": {
        "Stable revenues": r"stable revenue",
        "Alternative sources of revenue": r"alternative (sources|revenue)|revenue diversification",
        "Stable expenses": r"stable expense",
        "Fiscal responsibility": r"fiscal responsib|balanced budget|broke even|break ?even",
        "Contingency fund": r"contingency",
    },
    "Infrastructure and Process Capacity": {
        "Formalisation": r"formali[sz]",
        "Adequate facilities": r"adequate facilit|own (infrastructure|facilit)",
        "Communication": r"\bcommunication\b",
    },
    "Planning and Development Capacity": {
        "Strategic planning": r"strategic plan",
        "Plan implementation": r"plan implementation",
        "Creativity": r"creativ",
    },
    "Relationship and Network Capacity": {
        "Engagement with partners": r"engagement with partners|partner engagement",
        "Balanced relationships": r"balanced relationship",
        "Dependable relationships": r"dependable",
        "Personal connection": r"personal connection",
        "Bureaucratic partners": r"bureaucratic partner",
    },
}

# Respondent types: fixed names, several per paper (joined with "; ").
# Each name is added when its pattern matches the Respondents text.
RESPONDENT_TYPES = [
    ("Board members / club leaders",
     r"board|president|chair|executive|secretar|treasurer|manager|leadership|club administrator"),
    ("Club representatives (role not specified)", r"club representative|organisation representative"),
    ("Paid staff", r"paid staff|paid administrator|office employee|\bstaff\b"),
    ("Other volunteers", r"other volunteers|implementation-level volunteers"),
    ("Coaches", r"coach"),
    ("Officials (referees / umpires / league)", r"umpire|referee|league official"),
    ("Players / athletes", r"player|athlete"),
    ("Club members", r"member survey|club members"),
    ("Parents", r"parent"),
    ("Spectators", r"spectator"),
    ("Other stakeholders", r"stakeholder|software developer"),
]
RESPONDENT_ORDER = [name for name, _ in RESPONDENT_TYPES]
RESPONDENT_UNSPECIFIED = "Club representatives (role not specified)"

# Research method: ONE fixed category per paper (first matching rule wins).
RESEARCH_METHOD_CATEGORIES = [
    ("Mixed methods", r"mixed method"),
    ("Social network analysis", r"network analysis"),
    ("Case study (single)", r"case study \(single"),
    ("Case study (multiple)", r"case study \(multiple"),
    ("Case study (type not stated)", r"case study"),
    ("Focus groups", r"focus group"),
    ("Interviews", r"interview"),
    ("Survey: clubs + members (multilevel)", r"nested|multilevel"),
    ("Survey: single wave", r"one wave|single wave"),
    ("Survey: repeated waves (panel)", r"panel|waves"),
    ("Survey: single wave", r"survey"),
]
RESEARCH_METHOD_ORDER = [
    "Survey: single wave", "Survey: repeated waves (panel)", "Survey: clubs + members (multilevel)",
    "Case study (single)", "Case study (multiple)", "Case study (type not stated)",
    "Interviews", "Focus groups", "Mixed methods", "Social network analysis", "Not classified",
]

# Data collection tags.
COLLECTION_TAGS = [
    ("Online survey", r"online survey"),
    ("Telephone survey", r"telephone"),
    ("Paper survey", r"paper version"),
    ("Survey (mode unspecified)", r"^survey|; survey"),
    ("Interviews", r"interview"),
    ("Focus groups", r"focus group"),
    ("Observation", r"observation"),
    ("Documents / secondary data", r"secondary data|document"),
]

# Countries -> world region, for an aggregated view.
COUNTRY_REGION = {
    "Australia": "Oceania", "Canada": "North America", "United States": "North America",
}  # everything else defaults to Europe
