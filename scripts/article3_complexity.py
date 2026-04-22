#!/usr/bin/env python3
"""
article3_complexity.py

Article 3, Task 6: Complexity-proximity correlation analysis.

Matches AFIDA Chinese-linked holdings to known ownership chains
and compares traceable vs. opaque entities by distance to nearest
CFIUS Appendix A installation.

Inputs:
  - cfius_jurisdiction_analysis.csv (from Task 2)
  - afida_chinese_2024.csv (from Task 2 intermediate)

Outputs:
  - complexity_proximity_analysis.csv
  - Console: descriptive comparison, parent group analysis

Author: Robert J. Green | robert@rjgreenresearch.org
"""

import csv
import sys

import numpy as np
from scipy import stats


# ===================================================================
# KNOWN OWNERSHIP CHAINS
# ===================================================================

ENTITY_PROFILES = {
    "Murphy Brown LLC (Smithfield Foods)": {
        "parent": "Smithfield Foods / WH Group",
        "sec_traceable": True,
        "ownership": "WH Group (HK) -> Smithfield Foods (VA) -> Murphy Brown",
        "chain_depth": 4,
        "jurisdictions": ["Hong Kong", "Cayman Islands", "Virginia"],
        "state_actor": True,
    },
    "Murphy Brown of Missouri LLC (Smithfield Foods)": {
        "parent": "Smithfield Foods / WH Group",
        "sec_traceable": True,
        "ownership": "WH Group (HK) -> Smithfield Foods (VA) -> Murphy Brown of Missouri",
        "chain_depth": 4,
        "jurisdictions": ["Hong Kong", "Cayman Islands", "Virginia", "Missouri"],
        "state_actor": True,
    },
    "Smithfield Fresh Meats Corp.": {
        "parent": "Smithfield Foods / WH Group",
        "sec_traceable": True,
        "ownership": "WH Group (HK) -> Smithfield Foods (VA) -> Smithfield Fresh Meats",
        "chain_depth": 4,
        "jurisdictions": ["Hong Kong", "Cayman Islands", "Virginia"],
        "state_actor": True,
    },
    "Kansas City Sausage Company, LLC": {
        "parent": "Smithfield Foods / WH Group",
        "sec_traceable": True,
        "ownership": "WH Group (HK) -> Smithfield Foods (VA) -> Kansas City Sausage",
        "chain_depth": 4,
        "jurisdictions": ["Hong Kong", "Cayman Islands", "Virginia", "Missouri"],
        "state_actor": True,
    },
    "SYNGENTA CROP PROTECTION, INC.": {
        "parent": "Syngenta / ChemChina / Sinochem",
        "sec_traceable": True,
        "ownership": "Sinochem (SASAC) -> ChemChina -> Syngenta AG -> Syngenta CP",
        "chain_depth": 6,
        "jurisdictions": ["China", "Switzerland", "Cayman Islands", "Delaware"],
        "state_actor": True,
    },
    "Syngenta Flowers, LLC": {
        "parent": "Syngenta / ChemChina / Sinochem",
        "sec_traceable": True,
        "ownership": "Sinochem (SASAC) -> ChemChina -> Syngenta AG -> Syngenta Flowers",
        "chain_depth": 6,
        "jurisdictions": ["China", "Switzerland", "Cayman Islands"],
        "state_actor": True,
    },
    "Syngenta Seeds, LLC": {
        "parent": "Syngenta / ChemChina / Sinochem",
        "sec_traceable": True,
        "ownership": "Sinochem (SASAC) -> ChemChina -> Syngenta AG -> Syngenta Seeds",
        "chain_depth": 6,
        "jurisdictions": ["China", "Switzerland", "Cayman Islands"],
        "state_actor": True,
    },
    "BRAZOS HIGHLAND PROPERTIES, LP": {
        "parent": "Guanghui Group / Sun Guangxin",
        "sec_traceable": False,
        "ownership": "Sun Guangxin (Xinjiang) -> Guanghui Group -> Brazos Highland LP",
        "chain_depth": 3,
        "jurisdictions": ["China (Xinjiang)", "Texas"],
        "state_actor": False,
    },
    "HARVEST TEXAS, LLC": {
        "parent": "Guanghui Group / Sun Guangxin",
        "sec_traceable": False,
        "ownership": "Sun Guangxin (Xinjiang) -> Guanghui Group -> Harvest Texas LLC",
        "chain_depth": 3,
        "jurisdictions": ["China (Xinjiang)", "Texas"],
        "state_actor": False,
    },
    "CSCEC-US, INC.": {
        "parent": "China State Construction Engineering Corp",
        "sec_traceable": False,
        "ownership": "SASAC -> CSCEC -> CSCEC-US Inc",
        "chain_depth": 3,
        "jurisdictions": ["China", "Delaware"],
        "state_actor": True,
    },
}


def main():
    jurisdiction_csv = "data/outputs/cfius_jurisdiction_analysis.csv"
    afida_csv = "data/outputs/afida_chinese_2024.csv"
    output_csv = "data/outputs/complexity_proximity_analysis.csv"

    # Load jurisdiction analysis
    counties = []
    with open(jurisdiction_csv) as f:
        for row in csv.DictReader(f):
            counties.append(row)

    # Load entity names per county
    county_entities = {}
    with open(afida_csv) as f:
        for row in csv.DictReader(f):
            fips = row["fips"]
            county_entities.setdefault(fips, []).append(row["owner"])

    # Match
    matched = []
    unmatched = []

    for cr in counties:
        fips = cr["fips"]
        dist = float(cr["r4_nearest_dist"]) if cr["r4_nearest_dist"] != "N/A" else None
        ents = county_entities.get(fips, [])

        profile = None
        for ename in ents:
            if ename in ENTITY_PROFILES:
                p = ENTITY_PROFILES[ename]
                if profile is None or p["chain_depth"] > profile["chain_depth"]:
                    profile = p

        if profile and dist:
            matched.append({
                "fips": fips,
                "county": cr["county"],
                "state": cr["state"],
                "acres": float(cr["total_acres"]),
                "distance": dist,
                "covered": cr["r4_covered"],
                "parent_group": profile["parent"],
                "sec_traceable": profile["sec_traceable"],
                "chain_depth": profile["chain_depth"],
                "jurisdiction_count": len(profile["jurisdictions"]),
                "state_actor": profile["state_actor"],
                "ownership_path": profile["ownership"],
            })
        else:
            unmatched.append({
                "fips": fips, "county": cr["county"], "state": cr["state"],
                "acres": float(cr["total_acres"]),
                "distance": dist, "entities": ents,
            })

    print(f"Matched: {len(matched)} ({len(matched)/len(counties)*100:.1f}%)")
    print(f"Unmatched: {len(unmatched)} ({len(unmatched)/len(counties)*100:.1f}%)")

    # Descriptive comparison
    m_dists = [m["distance"] for m in matched]
    u_dists = [u["distance"] for u in unmatched if u["distance"]]
    m_acres = sum(m["acres"] for m in matched)
    u_acres = sum(u["acres"] for u in unmatched)
    total_acres = m_acres + u_acres

    print(f"\nTraceable: mean dist {np.mean(m_dists):.1f} mi, "
          f"{m_acres:,.0f} acres ({m_acres/total_acres*100:.1f}%)")
    print(f"Opaque:    mean dist {np.mean(u_dists):.1f} mi, "
          f"{u_acres:,.0f} acres ({u_acres/total_acres*100:.1f}%)")

    t_stat, p_val = stats.ttest_ind(m_dists, u_dists)
    print(f"t-test: t={t_stat:.2f}, p={p_val:.4f}")

    # By parent group
    print(f"\nBy parent group:")
    by_parent = {}
    for m in matched:
        p = m["parent_group"]
        by_parent.setdefault(p, {"n": 0, "acres": 0, "dists": [], "depth": m["chain_depth"]})
        by_parent[p]["n"] += 1
        by_parent[p]["acres"] += m["acres"]
        by_parent[p]["dists"].append(m["distance"])

    for parent, d in sorted(by_parent.items(), key=lambda x: -x[1]["acres"]):
        print(f"  {parent}: {d['n']} counties, {d['acres']:,.0f} acres, "
              f"depth {d['depth']}, mean dist {np.mean(d['dists']):.0f} mi")

    # Save
    with open(output_csv, "w", newline="") as f:
        if matched:
            w = csv.DictWriter(f, fieldnames=matched[0].keys())
            w.writeheader()
            w.writerows(matched)
    print(f"\nSaved: {output_csv}")


if __name__ == "__main__":
    main()
