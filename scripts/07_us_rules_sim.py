#!/usr/bin/env python3
"""
Milestone 4, step 4: rerun the realistic simulation under published US rules.

Demand is still the public Aachen 2018 (and 2017) series. This is US rules
applied to German demand, not a US hospital. Educational / advisory only.

US rules are taken from research/us_platelet_policies.md (public hospital and
AABB/FDA sources). This script does not edit that file.

  - ABO fallback: identical, then plasma-compatible (O patients get A/B/AB;
    A and B patients get AB), then other non-O, then group O to non-O last.
  - A second policy: first-in-first-out of any ABO (oldest unit first).
  - RhD-positive units may go to RhD-negative patients, except a tagged share
    of RhD-negative demand treated as females aged 50 or under. That share is
    an assumption (no source gives it for platelet recipients); we run 0%,
    15%, and 30%.
  - Shelf life: all 5-day pathogen-reduced (released day 2, 4 usable days),
    all 7-day LVDS (released day 3, 5 usable days), and a 50/50 mix.
    Shipping assumption: the existing 2-day order lead already includes
    transit, so units arrive with the full remaining life after release
    (4 days for PRT, 5 days for LVDS). No extra shipping delay is added.
  - US ABO/RhD shares from Stanford Blood Center (AABB Technical Manual
    18th Edition figures), page opened 13 Nov 2026:
    https://stanfordbloodcenter.org/donate-blood/blood-donation-facts/blood-types/

Compared with the German-rules result at the hospital's shortage-day count.

Run:  PYTHONPATH=scripts .venv/bin/python scripts/07_us_rules_sim.py
"""

from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd

import lib_m4 as L

RESULTS = L.RESULTS_DIR
CHARTS = L.CHART_DIR
YEAR = 2018  # main comparison year (matches milestone 3)
MODELS = ["dow4", "hgbr"]


def us_cfg(life: dict, abo_mode: str, prot_share: float) -> dict:
    cfg = deepcopy(L.m3.BASE)
    cfg["group_share"] = dict(L.US_GROUP_SHARE)
    cfg["abo_mode"] = abo_mode
    cfg["allow_rhpos_to_rhneg"] = True
    cfg["life_on_arrival"] = life
    cfg["rhdneg_female_le50_share"] = prot_share
    return cfg


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    df, y, authors = L.load_series()
    _, eval_start, eval_end = L.year_window(YEAR)
    hospital = L.hospital_actual(df, eval_start, eval_end)
    target_sd = hospital["shortage_days"]

    feat = L.m2.hgbr_feature_table(y)
    base = L.m2.baseline_forecasts(y)
    fcs = {"dow4": base["dow4"],
           "hgbr": L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{YEAR - 1}-12-31"))}
    fcs_sigma = {"dow4": base["dow4"],
                 "hgbr": L.m2.hgbr_forecasts(feat, pd.Timestamp(f"{YEAR - 2}-12-31"))}
    sigma = L.sigma_for_year(y, fcs_sigma, YEAR)
    win = {k: (L.m2.window_sum(fc, 2), L.m2.window_sum(fc, 4)) for k, fc in fcs.items()}

    scenarios = {
        "German rules (current sim)": L.m3.BASE,
        "US, plasma-first, 50/50 mix": us_cfg({4: 0.5, 5: 0.5}, "us_plasma_first", 0.15),
        "US, oldest-unit-first, 50/50 mix": us_cfg({4: 0.5, 5: 0.5}, "fifo_any_abo", 0.15),
        "US, plasma-first, all 5-day": us_cfg({4: 1.0}, "us_plasma_first", 0.15),
        "US, plasma-first, all 7-day": us_cfg({5: 1.0}, "us_plasma_first", 0.15),
        "US, plasma-first, 50/50, 0% females <=50": us_cfg({4: 0.5, 5: 0.5}, "us_plasma_first", 0.0),
        "US, plasma-first, 50/50, 30% females <=50": us_cfg({4: 0.5, 5: 0.5}, "us_plasma_first", 0.30),
    }

    rows = []
    matched_store = {}
    for name, cfg in scenarios.items():
        print("running:", name)
        res = L.run_config(cfg, y, win, sigma, MODELS, year=YEAR)
        summ, matched, _ = L.matched_table(res, target_sd, MODELS)
        for _, r in summ.iterrows():
            rec = r.to_dict()
            rec["scenario"] = name
            rec["abo_mode"] = cfg.get("abo_mode", "")
            rec["prot_share"] = cfg.get("rhdneg_female_le50_share", 0.0)
            rec["life"] = ",".join(str(k) for k in sorted(cfg["life_on_arrival"]))
            rows.append(rec)
        matched_store[name] = matched

    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "07_inventory.csv", index=False)
    # Per-seed waste for the headline scenarios
    seed = {}
    for name in ("German rules (current sim)",
                 "US, plasma-first, 50/50 mix",
                 "US, oldest-unit-first, 50/50 mix",
                 "US, plasma-first, all 5-day",
                 "US, plasma-first, all 7-day"):
        for m in MODELS:
            seed[f"{name}::{m}"] = matched_store[name][m]
    pd.DataFrame(seed).to_csv(RESULTS / "07_per_seed_waste.csv", index_label="seed")

    notes = {
        "demand_source": "University Hospital Aachen daily platelet counts 2018 (public, CC BY 4.0).",
        "not_a_us_hospital": True,
        "us_group_share_source": L.US_GROUP_SHARE_SOURCE,
        "us_group_share": L.US_GROUP_SHARE,
        "shipping_assumption": (
            "The 2-day order lead already includes transit. Pathogen-reduced "
            "5-day units are assumed to arrive with 4 usable days (released "
            "day 2). 7-day LVDS units are assumed to arrive with 5 usable days "
            "(released day 3). No extra shipping delay is added."
        ),
        "rhdneg_female_le50_share_assumption": (
            "15% of already RhD-negative demand is tagged as females aged 50 "
            "or under and cannot receive RhD-positive units. No source gives "
            "this share for platelet recipients; 0% and 30% are also run."
        ),
        "window": f"{eval_start.date()} to {eval_end.date()}",
        "target_shortage_days": target_sd,
        "hospital_waste_pct": hospital["waste_pct"],
    }
    (RESULTS / "07_assumptions.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in notes.items()) + "\n")

    # Headline chart: German vs two US policies vs hospital, gradient boosting,
    # 50/50 mix for the US policies (the suggested base mix).
    g = matched_store["German rules (current sim)"]["hgbr"]
    us_p = matched_store["US, plasma-first, 50/50 mix"]["hgbr"]
    us_f = matched_store["US, oldest-unit-first, 50/50 mix"]["hgbr"]
    hosp = np.array([hospital["waste_pct"]])
    mg, mp, mf = map(lambda a: float(np.nanmean(a)), (g, us_p, us_f))
    # Honest title.
    if mp < mg - 0.2 and mf < mg - 0.2:
        title = ("Under US substitution and a 50/50 US shelf-life mix, simulated waste\n"
                 "was lower than under the German rules — on German demand, not a US hospital")
    elif mp > mg + 0.2 and mf > mg + 0.2:
        title = ("Under US substitution and a 50/50 US shelf-life mix, simulated waste\n"
                 "was higher than under the German rules — on German demand, not a US hospital")
    else:
        title = ("US rules applied to this German hospital's demand did not clearly\n"
                 "change waste versus the German rules, at the same number of short days")

    items = [
        ("German rules\n(our usual sim)", g, L.m2.COLORS["hgbr"]),
        ("US rules:\nplasma-compatible first", us_p, "#6a3d9a"),
        ("US rules:\noldest unit first, any type", us_f, "#1b9e77"),
        ("What the hospital\nactually did (2018)", hosp, "#222222"),
    ]
    chart = L.simple_bar_chart(
        CHARTS / "m4_us_rules.png",
        title=title,
        ylabel="Platelets thrown away\n(% of units transfused)",
        items=items,
        footnote=(
            "Aachen demand, 2018, set to the hospital's 31 short days. "
            "Machine-learning forecast in every simulated bar. "
            "US bars use Stanford Blood Center group shares, a 50/50 mix of "
            "4- and 5-usable-day units, and assume 15% of RhD-neg demand is "
            "females 50 or under. This is not a US hospital. "
            "Black lines = 5th to 95th percentile of 30 simulated runs. Educational only."
        ),
        ylim=(0, max(16, hospital["waste_pct"] + 4)),
        value_fmt="{:.1f}% wasted",
    )

    metrics = {"year": YEAR, "target_shortage_days": target_sd,
               "hospital_waste_pct": hospital["waste_pct"]}
    for _, r in out.iterrows():
        key = (r["scenario"].replace(" ", "_").replace(",", "")[:40]
               + "_" + r["model"] + "_waste")
        metrics[key] = float(r["waste_mean"])
    trackio_msg = L.log_trackio("07_us_rules_sim", metrics, {
        "group_share_source": "Stanford Blood Center / AABB TM 18e",
        "not_a_us_hospital": True,
    })

    # Sensitivity printout for the protected share, GB only.
    sens = out[(out["model"] == "hgbr") & (out["scenario"].str.contains("females|plasma-first, 50/50 mix$"))]
    shelf = out[(out["model"] == "hgbr") & (out["scenario"].str.contains("all 5-day|all 7-day|50/50 mix$"))
                & ~out["scenario"].str.contains("females|oldest")]

    lines = [
        "=== Step 4: US rules on Aachen demand (not a US hospital) ===",
        f"Window: {eval_start.date()} to {eval_end.date()}",
        f"Hospital actual: {hospital['waste_pct']:.2f}% wasted, {target_sd} short days.",
        f"US group shares: {L.US_GROUP_SHARE_SOURCE}",
        f"Shipping assumption: {notes['shipping_assumption']}",
        f"Females <=50 assumption: {notes['rhdneg_female_le50_share_assumption']}",
        out.to_string(index=False),
        "",
        "Gradient boosting, German vs US base (50/50, plasma-first):",
        f"  German {mg:.2f}%  US plasma-first {mp:.2f}%  US oldest-first {mf:.2f}%",
        f"  gaps vs German: plasma-first {mp-mg:+.2f} pp, oldest-first {mf-mg:+.2f} pp",
        "",
        "Shelf-life scenarios (GB, US plasma-first):",
        shelf.to_string(index=False),
        "",
        "Sensitivity to the females<=50 share (GB, US plasma-first, 50/50):",
        sens.to_string(index=False),
        f"Chart: {chart}",
        f"Trackio: {trackio_msg}",
    ]
    text = "\n".join(lines) + "\n"
    print(text)
    (RESULTS / "07_run_log.txt").write_text(text)


if __name__ == "__main__":
    main()
