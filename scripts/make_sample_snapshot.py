"""
Builds a made-up sample aggregate_snapshot.json, shaped exactly like what
export_snapshot.py (in the local student_data_tool project) produces from
real data -- purely so this public dashboard has something to demo with.
No real Cerritos College data is used or represented here.

Run this from student_data_tool's own environment (it imports that
project's kpi_compute/export_snapshot modules), then copy the output
into this project's sample_data/ folder. Kept here only as a reference
for how the sample was built, not meant to run standalone in this repo.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "../student_data_tool")
import export_snapshot  # noqa: E402

rng = np.random.default_rng(0)


def _fake_cohort(cohort_name, n, maturity):
    """maturity in [0, 1]: how far along this cohort is, so later cohorts
    (still in year 1) show mostly-empty later-year columns, like real data."""
    lcp = rng.choice(["AHC", "ATST", "BAL", "ED", "EHS", "HSW"], n)
    eth = rng.choice(["Hispanic/Latino", "White", "Asian", "Black or African American", "Two or More Races"], n)
    df = pd.DataFrame({
        "Cohort_Name": cohort_name,
        "LCP_current": lcp,
        "major_classification_current": rng.choice(
            ["Transfer/Degree-Seeking", "CTE Certificate", "Non-CTE Certificate", "Unknown"], n, p=[0.6, 0.15, 0.15, 0.1]),
        "cte_classification_current": rng.choice([0, 1], n, p=[0.6, 0.4]),
        "Ethnicity": eth,
        "Gender": rng.choice(["Male", "Female", "Unknown"], n, p=[0.46, 0.52, 0.02]),
        "EdPlan_ay1": np.where(rng.random(n) < 0.95, "Has CSEP/DPP by end of year 1", "Does not have CSEP/DPP by end of year 1"),
        "EdPlan_ay2": np.where(maturity >= 0.4, np.where(rng.random(n) < 0.97, "Has CSEP/DPP by end of year 2", "Does not have CSEP/DPP by end of year 2"), None),
        "EdPlan_ay3": np.where(maturity >= 0.7, np.where(rng.random(n) < 0.98, "Has CSEP/DPP by end of year 3", "Does not have CSEP/DPP by end of year 3"), None),
        "Persisted_f1_sp1": np.where(rng.random(n) < 0.78, "Persisted from F1 to Sp1", "Did not persist from F1 to Sp1"),
        "Retained_f1_f2": np.where(maturity >= 0.4, np.where(rng.random(n) < 0.62, "Retained from F1 to F2", "Was not retained from F1 to F2"), None),
        "Retained_f1_sp2": np.where(maturity >= 0.4, np.where(rng.random(n) < 0.55, "Retained from F1 to Sp2", "Was not retained from F1 to Sp2"), None),
        "English_Term_firstpassed": np.where(rng.random(n) < 0.3 + 0.4 * maturity, "1253", np.where(rng.random(n) < 0.5, "Did not pass", "N/A because no attempt")),
        "Math_Term_firstpassed": np.where(rng.random(n) < 0.2 + 0.3 * maturity, "1253", np.where(rng.random(n) < 0.5, "Did not pass", "N/A because no attempt")),
        "CompletedUnits_DA_end_of_ay1": rng.integers(0, 35, n),
        "CompletedUnits_DA_end_of_ay2": np.where(maturity >= 0.4, rng.integers(10, 50, n), None),
        "CompletedUnits_DA_end_of_ay3": np.where(maturity >= 0.7, rng.integers(20, 65, n), None),
        "CompletedUnits_CTE_ay1_ctecert": np.where(rng.random(n) < 0.4, 1, 0),
        "Awards_all": np.where(rng.random(n) < 0.05 + 0.15 * maturity, "AA-CERT", None),
        "Graduated": np.where(rng.random(n) < 0.05 + 0.15 * maturity, "Graduated", "Has not graduated"),
    })
    return df


frames = [
    _fake_cohort("Fall 24", 400, maturity=1.0),
    _fake_cohort("Fall 25", 400, maturity=0.6),
    _fake_cohort("Fall 26", 400, maturity=0.1),
]
df = pd.concat(frames, ignore_index=True)

snapshot = export_snapshot.build_snapshot(df)
export_snapshot.write_snapshot(snapshot, "sample_data/sample_aggregate_snapshot.json")
print("wrote sample_data/sample_aggregate_snapshot.json")
