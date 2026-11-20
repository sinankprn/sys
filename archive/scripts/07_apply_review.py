"""Read completed review workbook(s) and log the outcome.

    python scripts/07_apply_review.py output/review/review_SK.xlsx [more files...]

- 'Corrected' / 'Not reported in paper' rows  -> data/corrections/corrections.csv
- 'Confirmed' rows                            -> data/corrections/verifications.csv
- 'Variable roles' tab, Confirmed role       -> data/corrections/indicator_roles.csv
- 'Unsure - discuss' rows                     -> printed, and saved to output/review/to_discuss.xlsx

Every later script loads the raw sheet and applies these logs on top, so the
raw extraction is never overwritten and each change has a reviewer, a page
reference and a date. Re-running with the same file is safe (later entries for
the same paper+field replace earlier ones).
"""
import sys
from datetime import date

import _path  # noqa: F401
import pandas as pd

from sysreview import config
from sysreview.load import read_corrections, read_raw


def main(files):
    if not files:
        sys.exit(__doc__)
    raw, _ = read_raw()
    corr_rows, ver_rows, discuss = [], [], []
    today = date.today().isoformat()
    for f in files:
        df = pd.read_excel(f, sheet_name="Review")
        df = df[df["Decision"].notna()]
        for _, r in df.iterrows():
            pid, field, dec = int(r["ID"]), r["Field"], r["Decision"]
            base = {"ID": pid, "Field": field, "Reviewer": r.get("Reviewer"),
                    "Location in paper": r.get("Page / location"), "Date": today, "Source file": str(f)}
            if dec == "Confirmed":
                ver_rows.append(base)
            elif dec in ("Corrected", "Not reported in paper"):
                new = r.get("Corrected value")
                if pd.isna(new) or str(new).strip() == "":
                    if dec == "Corrected":
                        print(f"  ! ID {pid} '{field}': marked Corrected but no corrected value - skipped")
                        continue
                    new = "Not reported"
                old = raw.at[pid, field] if field in raw.columns else None
                corr_rows.append({**base, "Old value": old, "New value": new,
                                  "Decision": dec, "Notes": r.get("Notes")})
            elif str(dec).startswith("Unsure"):
                discuss.append(r)

    role_rows = []
    for f in files:
        try:
            vr = pd.read_excel(f, sheet_name="Variable roles")
        except ValueError:
            continue
        for _, r in vr[vr["Confirmed role"].notna()].iterrows():
            role_rows.append({"ID": int(r["ID"]), "Source column": r["Source column"],
                              "Indicator": r["Indicator"], "Role": r["Confirmed role"],
                              "Suggested role": r["Suggested role"], "Reviewer": r.get("Reviewer"),
                              "Location in paper": r.get("Page / location"), "Notes": r.get("Notes"),
                              "Date": today, "Source file": str(f)})

    def merge(path, rows, cols, key=("ID", "Field")):
        new = pd.DataFrame(rows, columns=cols)
        if path.exists():
            new = pd.concat([pd.read_csv(path), new], ignore_index=True)
        new = new.drop_duplicates(subset=list(key), keep="last")
        path.parent.mkdir(parents=True, exist_ok=True)
        new.to_csv(path, index=False)
        return len(new)

    n_corr = merge(config.CORRECTIONS_CSV, corr_rows,
                   ["ID", "Field", "Old value", "New value", "Decision", "Reviewer",
                    "Location in paper", "Date", "Notes", "Source file"])
    n_ver = merge(config.VERIFICATIONS_CSV, ver_rows,
                  ["ID", "Field", "Reviewer", "Location in paper", "Date", "Source file"])
    n_roles = merge(config.ROLES_CSV, role_rows,
                    ["ID", "Source column", "Indicator", "Role", "Suggested role", "Reviewer",
                     "Location in paper", "Notes", "Date", "Source file"],
                    key=("ID", "Source column", "Indicator"))
    print(f"Logged {len(role_rows)} variable roles ({n_roles} total).")
    print(f"Logged {len(corr_rows)} corrections ({n_corr} total) and "
          f"{len(ver_rows)} confirmations ({n_ver} total).")
    if discuss:
        out = config.REVIEW / "to_discuss.xlsx"
        pd.DataFrame(discuss).to_excel(out, index=False)
        print(f"{len(discuss)} rows marked 'Unsure - discuss' -> {out}")
    print("Now re-run:  python scripts/run_all.py")


if __name__ == "__main__":
    main(sys.argv[1:])
