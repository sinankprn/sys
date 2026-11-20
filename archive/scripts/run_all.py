"""Run the whole pipeline: organise -> summaries (01-04) -> quality checks (05).

    python scripts/run_all.py              # offline
    python scripts/run_all.py --crossref   # also check DOIs against Crossref
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["00_organise_extraction.py", "01_publication.py", "02_study_design.py",
         "03_capacity.py", "03b_qualitative_themes.py", "04_models.py", "05_quality_checks.py"]

if __name__ == "__main__":
    extra = sys.argv[1:]
    for step in STEPS:
        args = [sys.executable, str(HERE / step)] + (extra if step.startswith("05") else [])
        if subprocess.run(args).returncode:
            sys.exit(f"{step} failed")
    print("\nAll done. See output/organised_extraction.xlsx, output/tables/ and output/figures/.")
