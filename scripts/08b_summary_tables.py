#!/usr/bin/env python3
"""Compact tables from results/m5/08_multiyear_inventory.csv for the paper (no new simulation)."""
import pandas as pd
from pathlib import Path
R = Path(__file__).resolve().parent.parent / "results/m5"
d = pd.read_csv(R / "08_multiyear_inventory.csv")
h = d[d.target == "hospital"]
keep = ["dow4", "hgbr", "chronos", "lasso", "rnn"]
rows = []
for Y, g in h.groupby("year"):
    g = g.set_index("model")
    r = {"year": Y, "short_days": int(g.loc["dow4", "target_short_days"]),
         "hospital_waste_pct": g.loc["dow4", "hospital_waste_pct"],
         "hospital_emergency_units": g.loc["dow4", "hospital_emergency_units"]}
    for m in keep:
        r[f"{m}_waste_pct"] = g.loc[m, "waste_pct_mean"]
        r[f"{m}_emerg"] = g.loc[m, "emergency_units_mean"]
        r[f"{m}_lost"] = g.loc[m, "wasted_plus_emergency_mean"]
    r["hgbr_gap_pts"] = g.loc["hgbr", "waste_gap_vs_dow4"]
    r["hgbr_seeds_better"] = int(g.loc["hgbr", "seeds_less_waste_than_dow4"])
    r["chronos_gap_pts"] = g.loc["chronos", "waste_gap_vs_dow4"]
    r["chronos_seeds_better"] = int(g.loc["chronos", "seeds_less_waste_than_dow4"])
    r["hgbr_lost_gap"] = g.loc["hgbr", "lost_gap_vs_dow4"]
    r["chronos_lost_gap"] = g.loc["chronos", "lost_gap_vs_dow4"]
    rows.append(r)
t = pd.DataFrame(rows)
mean = t.mean(numeric_only=True).astype(object); mean["year"] = "mean 2012-2018"
t = pd.concat([t, mean.to_frame().T], ignore_index=True)
t.to_csv(R / "08_summary_for_paper.csv", index=False)
# robustness: wins of hgbr vs dow4 on waste at 20/50 short days
w = pd.read_csv(R / "08_winner_by_year.csv")
print(t.round(2).T.to_string())
print(w[(w.scope.isin(["dow4_vs_hgbr", "dow4_vs_chronos", "hgbr_vs_chronos", "study_models", "all_models"]))]
      .groupby(["target", "metric", "scope"])["winner"].value_counts().to_string())
