#!/usr/bin/env python3
"""
article3_did.py

Article 3, Task 5: State-level difference-in-differences analysis.

Tests whether state foreign land ownership restrictions reduce
Chinese-linked AFIDA holdings, using staggered adoption (2022-2025)
as a natural experiment.

Inputs:
  - AFIDA annual files (2018-2024): AFIDACurrentHoldingsYR20XX.xlsx
  - state_restrictions.csv (from Task 3)

Outputs:
  - afida_state_year_panel.csv
  - Console: DiD estimates, event study, displacement test, TWFE

Author: Robert J. Green | robert@rjgreenresearch.org
"""

import csv
import os
import sys
from collections import defaultdict

import numpy as np

try:
    import openpyxl
except ImportError:
    print("Required: pip install openpyxl")
    sys.exit(1)


# ===================================================================
# CONFIGURATION -- adjust paths to your environment
# ===================================================================

AFIDA_FILES = {
    2018: "data/inputs/afida_current_holdings_yr2018.xlsx",
    2019: "data/inputs/afida_current_holdings_yr2019.xlsx",
    2020: "data/inputs/afida_current_holdings_yr2020.xlsx",
    2021: "data/inputs/afida_current_holdings_yr2021.xlsx",
    2022: "data/inputs/AFIDA YR2022 Holdings Data.xlsx",
    2023: "data/inputs/AFIDA YR2023 Holdings Data.xlsx",
    2024: "data/inputs/AFIDACurrentHoldingsYR2024.xlsx",
}

# Try alternate filenames (spaces vs underscores)
for year in list(AFIDA_FILES.keys()):
    path = AFIDA_FILES[year]
    if not os.path.exists(path):
        alt = path.replace(" ", "_")
        if os.path.exists(alt):
            AFIDA_FILES[year] = alt
        else:
            alt2 = path.replace("_", " ")
            if os.path.exists(alt2):
                AFIDA_FILES[year] = alt2

STATE_RESTRICTIONS = "data/outputs/state_restrictions.csv"
OUTPUT_PANEL = "data/outputs/afida_state_year_panel.csv"


def parse_afida_year(filepath: str):
    """Parse state-level holding counts from AFIDA Excel file."""
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active

    state_data = defaultdict(lambda: {
        "total_holdings": 0, "total_acres": 0.0,
        "chinese_holdings": 0, "chinese_acres": 0.0,
    })

    for row in ws.iter_rows(min_row=4, values_only=True):
        cells = [str(c).strip() if c else "" for c in row]
        if len(cells) < 11:
            continue
        state = cells[0]
        if not state or state.lower() in ("state", ""):
            continue
        country = cells[6] if len(cells) > 6 else ""
        try:
            acres = float(cells[10])
        except (ValueError, IndexError):
            continue
        if acres <= 0:
            continue

        state_data[state]["total_holdings"] += 1
        state_data[state]["total_acres"] += acres
        if "CHINA" in country.upper() or "CHINESE" in country.upper():
            state_data[state]["chinese_holdings"] += 1
            state_data[state]["chinese_acres"] += acres

    wb.close()
    return dict(state_data)


def load_restrictions(csv_path: str):
    """Load state restriction data."""
    restrictions = {}
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            restrictions[row["state"]] = row
    return restrictions


def build_panel(afida_data, restrictions, years):
    """Build state-year panel with treatment indicators."""
    all_states = set()
    for y in years:
        all_states.update(afida_data.get(y, {}).keys())

    panel = []
    for year in sorted(years):
        for state in sorted(all_states):
            d = afida_data.get(year, {}).get(state, {
                "total_holdings": 0, "total_acres": 0,
                "chinese_holdings": 0, "chinese_acres": 0,
            })

            rest = restrictions.get(state, {})
            first_year = rest.get("first_enacted_year", "")

            if first_year == "pre-existing":
                treated = 1
                treatment_year = 2000
            elif first_year and first_year.isdigit():
                treatment_year = int(first_year)
                treated = 1 if year >= treatment_year else 0
            else:
                treated = 0
                treatment_year = 0

            panel.append({
                "state": state,
                "year": year,
                "total_holdings": d["total_holdings"],
                "total_acres": round(d["total_acres"], 1),
                "chinese_holdings": d["chinese_holdings"],
                "chinese_acres": round(d.get("chinese_acres", 0), 1),
                "has_restriction": treated,
                "treatment_year": treatment_year if treatment_year > 0 else "",
                "provision_type": rest.get("provision_type", ""),
                "target_scope": rest.get("target_scope", ""),
            })

    return panel


def avg_metric(panel, states, years, metric):
    """Compute average metric across states and years."""
    vals = [r[metric] for r in panel
            if r["state"] in states and r["year"] in years]
    return np.mean(vals) if vals else 0


def run_did(panel, wave_states, control_states, pre_years, post_years):
    """Run simple 2x2 DiD and event study."""
    results = {}

    for metric, label in [("chinese_holdings", "Chinese Holdings"),
                          ("chinese_acres", "Chinese Acreage"),
                          ("total_holdings", "Total Holdings")]:
        t_pre = avg_metric(panel, wave_states, pre_years, metric)
        t_post = avg_metric(panel, wave_states, post_years, metric)
        c_pre = avg_metric(panel, control_states, pre_years, metric)
        c_post = avg_metric(panel, control_states, post_years, metric)
        did = (t_post - t_pre) - (c_post - c_pre)
        results[metric] = {
            "treat_pre": t_pre, "treat_post": t_post,
            "ctrl_pre": c_pre, "ctrl_post": c_post, "did": did,
        }
        print(f"\n  {label}:")
        print(f"    Treated: Pre={t_pre:.2f}, Post={t_post:.2f}, ?={t_post-t_pre:+.2f}")
        print(f"    Control: Pre={c_pre:.2f}, Post={c_post:.2f}, ?={c_post-c_pre:+.2f}")
        print(f"    DiD: {did:+.2f}")

    return results


def run_event_study(panel, wave_states, control_states, years, metric):
    """Year-by-year treatment-control differences."""
    base_diff = None
    print(f"\n  {'Year':<6} {'Treated':>10} {'Control':>10} {'Diff':>10} {'Rel 2021':>10}")
    for y in years:
        t = avg_metric(panel, wave_states, [y], metric)
        c = avg_metric(panel, control_states, [y], metric)
        diff = t - c
        if y == 2021:
            base_diff = diff
        rel = diff - base_diff if base_diff is not None else 0
        marker = " ?" if y == 2023 else ""
        print(f"  {y:<6} {t:>10.2f} {c:>10.2f} {diff:>+10.2f} {rel:>+10.2f}{marker}")


def main():
    # Check inputs
    for path in AFIDA_FILES.values():
        if not os.path.exists(path):
            print(f"WARNING: {path} not found -- skipping")

    restrictions = load_restrictions(STATE_RESTRICTIONS)

    # Parse all years
    afida_data = {}
    years = []
    for year, path in sorted(AFIDA_FILES.items()):
        if os.path.exists(path):
            print(f"Parsing {year}...", end=" ")
            try:
                data = parse_afida_year(path)
                afida_data[year] = data
                years.append(year)
                ch = sum(d["chinese_holdings"] for d in data.values())
                print(f"{sum(d['total_holdings'] for d in data.values())} total, {ch} Chinese")
            except Exception as e:
                print(f"SKIPPED ({type(e).__name__}: {e})")
        else:
            print(f"Skipping {year}: {path} not found")

    if len(years) < 3:
        print(f"\nWARNING: Only {len(years)} years loaded ({years}). "
              f"DiD requires at least 3 years for pre/post comparison.")
        print("Check that AFIDA Excel files are valid .xlsx format.")
        if len(years) == 0:
            sys.exit(1)

    # Build panel
    panel_list = build_panel(afida_data, restrictions, years)

    # Save panel
    with open(OUTPUT_PANEL, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=panel_list[0].keys())
        w.writeheader()
        w.writerows(panel_list)
    print(f"\nPanel: {len(panel_list)} observations")
    print(f"Saved: {OUTPUT_PANEL}")

    # Classify states
    wave_2023 = set()
    never_treated = set()
    always_treated = set()
    seen = set()
    for r in panel_list:
        s = r["state"]
        if s in seen:
            continue
        seen.add(s)
        ty = r["treatment_year"]
        if ty == "":
            never_treated.add(s)
        elif ty == 2000:
            always_treated.add(s)
        elif ty == 2023:
            wave_2023.add(s)

    control = never_treated - wave_2023

    # DiD
    print(f"\n{'='*60}")
    print(f"2023 WAVE DiD ({len(wave_2023)} treated, {len(control)} control)")
    print(f"{'='*60}")
    run_did(panel_list, wave_2023, control, [2020, 2021], [2023, 2024])

    # Event study
    print(f"\n{'='*60}")
    print("EVENT STUDY: Chinese Holdings")
    print(f"{'='*60}")
    run_event_study(panel_list, wave_2023, control, years, "chinese_holdings")


if __name__ == "__main__":
    main()
