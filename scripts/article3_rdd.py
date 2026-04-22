#!/usr/bin/env python3
"""
article3_rdd.py

Article 3, Task 4: Multi-threshold boundary discontinuity analysis.

Tests for density discontinuities at 25, 50, 75, 100, and 125 miles
from nearest CFIUS Appendix A installation.

Inputs:
  - cfius_jurisdiction_analysis.csv (from article3_cfius_analysis.py)

Outputs:
  - cfius_distance_distribution.csv
  - Console: density tests, cumulative coverage, near-threshold analysis

Author: Robert J. Green | robert@rjgreenresearch.org
"""

import csv
import math
import sys

import numpy as np


def load_distances(jurisdiction_csv: str):
    """Extract Regime 4 nearest distances from jurisdiction analysis."""
    distances = []
    with open(jurisdiction_csv) as f:
        for row in csv.DictReader(f):
            d = row.get("r4_nearest_dist", "")
            if d and d != "N/A":
                distances.append({
                    "fips": row["fips"],
                    "county": row["county"],
                    "state": row["state"],
                    "acres": float(row["total_acres"]),
                    "dist": float(d),
                    "covered": row["r4_covered"],
                })
    return distances


def density_test(dists: np.ndarray, threshold: float, window: int = 15):
    """Test density ratio at a given threshold with specified window."""
    below = np.sum((dists >= threshold - window) & (dists < threshold))
    above = np.sum((dists >= threshold) & (dists < threshold + window))
    total = below + above

    ratio = above / below if below > 0 else float("inf")
    p_hat = above / total if total > 0 else 0
    se = math.sqrt(0.25 / total) if total > 0 else 0
    z = (p_hat - 0.5) / se if se > 0 else 0

    # Near-boundary (5-mile)
    just_below = int(np.sum((dists >= threshold - 5) & (dists < threshold)))
    just_above = int(np.sum((dists >= threshold) & (dists < threshold + 5)))

    return {
        "threshold": threshold,
        "below": int(below),
        "above": int(above),
        "ratio": ratio,
        "p_hat": p_hat,
        "z": z,
        "significant_5pct": abs(z) > 1.96,
        "significant_10pct": abs(z) > 1.645,
        "near_below": just_below,
        "near_above": just_above,
    }


def cumulative_coverage(dists: np.ndarray, acres: np.ndarray, thresholds):
    """Compute cumulative coverage at each threshold."""
    total_a = acres.sum()
    results = []
    for t in thresholds:
        mask = dists <= t
        n = int(mask.sum())
        a = float(acres[mask].sum())
        results.append({
            "threshold": t,
            "counties": n,
            "total": len(dists),
            "county_rate": n / len(dists),
            "acreage": a,
            "acreage_rate": a / total_a if total_a > 0 else 0,
        })
    return results


def main():
    input_csv = "data/outputs/cfius_jurisdiction_analysis.csv"
    output_csv = "data/outputs/cfius_distance_distribution.csv"

    distances = load_distances(input_csv)
    if not distances:
        print(f"ERROR: No distances loaded from {input_csv}")
        sys.exit(1)

    dists = np.array([d["dist"] for d in distances])
    acres = np.array([d["acres"] for d in distances])

    print(f"Holdings: {len(dists)}")
    print(f"Range: {dists.min():.1f} - {dists.max():.1f} miles")
    print(f"Mean: {dists.mean():.1f}, Median: {np.median(dists):.1f}")

    # Density tests
    print(f"\n{'='*60}")
    print("MULTI-THRESHOLD DENSITY TESTS")
    print(f"{'='*60}")

    for t in [25, 50, 75, 100, 125]:
        r = density_test(dists, t)
        marker = " <- CFIUS THRESHOLD" if t == 100 else ""
        sig = "***" if r["significant_5pct"] else ("*" if r["significant_10pct"] else "")
        print(f"\n  {t} miles{marker}:")
        print(f"    ?15 mi window: {r['below']} below, {r['above']} above (ratio {r['ratio']:.2f})")
        print(f"    ?5 mi near-boundary: {r['near_below']} below, {r['near_above']} above")
        print(f"    z = {r['z']:.2f} {sig}")

    # Cumulative coverage
    print(f"\n{'='*60}")
    print("CUMULATIVE COVERAGE (distance to ANY Appendix A site)")
    print(f"{'='*60}")
    for c in cumulative_coverage(dists, acres, [1, 10, 25, 50, 75, 100, 125, 150]):
        print(f"  <= {c['threshold']:>3} mi: {c['counties']:>3}/{c['total']} "
              f"({c['county_rate']*100:>5.1f}%), {c['acreage']:>10,.0f} acres "
              f"({c['acreage_rate']*100:>5.1f}%)")

    # Part 1/Part 2 classification gap
    within_100 = int(np.sum(dists <= 100))
    actual_covered = sum(1 for d in distances if d["covered"] == "Y")
    gap = within_100 - actual_covered
    print(f"\n  CLASSIFICATION GAP: {gap} counties within 100 mi of Part 1 sites")
    print(f"  but outside jurisdiction (Part 1 = 1-mile threshold)")
    print(f"  Reclassification would increase coverage: "
          f"{actual_covered/len(dists)*100:.1f}% -> {within_100/len(dists)*100:.1f}%")

    # Save distance distribution
    with open(output_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "fips", "county", "state", "acres", "r4_nearest_dist", "r4_covered"])
        w.writeheader()
        for d in distances:
            w.writerow({
                "fips": d["fips"], "county": d["county"], "state": d["state"],
                "acres": d["acres"], "r4_nearest_dist": d["dist"],
                "r4_covered": d["covered"],
            })
    print(f"\nSaved: {output_csv}")


if __name__ == "__main__":
    main()
