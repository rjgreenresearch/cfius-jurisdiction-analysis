#!/usr/bin/env python3
"""
build_cfius_appendix_a.py

Builds the CFIUS Appendix A site database with regime tagging and geocoding.
Sources:
  - 85 FR 3166 (Jan 17, 2020) -- Original Part 802 Appendix A (Regime 2)
  - 88 FR 57348 (Aug 23, 2023) -- Added 8 installations (Regime 3)
  - 89 FR 88128 (Nov 7, 2024) -- Added 59, moved 8, removed 3 (Regime 4)
  - eCFR current text (retrieved Apr 4, 2026) -- Authoritative current list

Output: cfius_appendix_a_all_regimes.csv

Author: Robert J. Green | robert@rjgreenresearch.org
"""

import csv
import json
import os

# ===================================================================
# 2024 ADDITIONS (from 89 FR 88128, effective Dec 9, 2024)
# ===================================================================

# 40 new Part 1 installations added in 2024
REGIME4_PART1_NEW = {
    "Anniston Army Depot", "Barter Island Regional Radar Site",
    "Blue Grass Army Depot", "Camp Blaz", "Camp Navajo", "Camp Roberts",
    "Cold Bay Regional Radar Site", "Detroit Arsenal",
    "Hawthorne Army Depot", "Indian Mountain Regional Radar Site",
    "Iowa Army Ammunition Plant", "Joint Base Myer-Henderson Hall",
    "Joint Systems Manufacturing Center--Lima", "Kenai Regional Radar Site",
    "Kotzebue Regional Radar Site", "Lake City Army Ammunition Plant",
    "Letterkenny Army Depot", "Lisburne Regional Radar Site",
    "Marine Corps Logistics Base Albany", "Marine Corps Logistics Base Barstow",
    "Marine Corps Support Facility Blount Island",
    "McAlester Army Ammunition Plant", "Military Ocean Terminal Concord",
    "Military Ocean Terminal Sunny Point", "Naval Air Station Corpus Christi",
    "Naval Logistics Support Activity Ketchikan",
    "Naval Logistics Support Activity LaMoure",
    "Naval Logistics Support Annex Orlando",
    "Naval Logistics Support Facility Aguada",
    "Naval Logistics Support Facility Cutler", "Naval Suffolk Facility",
    "Pine Bluff Arsenal", "Pueblo Chemical Depot", "Red River Army Depot",
    "Romanzof Regional Radar Site", "Scott Air Force Base",
    "Scranton Army Ammunition Plant", "Sparrevohn Regional Radar Site",
    "Tatalina Regional Radar Site", "Tooele Army Depot",
}

# 19 new Part 2 installations added in 2024
REGIME4_PART2_NEW = {
    "Altus Air Force Base", "Barksdale Air Force Base", "Camp Dodge",
    "Camp Grayling", "Camp Williams", "Cannon Air Force Base",
    "Chocolate Mountain Aerial Gunnery Range", "Columbus Air Force Base",
    "Dover Air Force Base", "Fort Novosel", "Goodfellow Air Force Base",
    "Joint Base Cape Cod", "Joint Base Charleston",
    "Little Rock Air Force Base", "Maxwell-Gunter Air Force Base",
    "Muscatatuck Urban Training Center", "Townsend Bombing Range",
    "Vance Air Force Base", "Whiteman Air Force Base",
}

# 8 moved from Part 1 to Part 2 in 2024
REGIME4_MOVED_P1_TO_P2 = {
    "Arnold Air Force Base", "Joint Base San Antonio",
    "Malmstrom Air Force Base", "Moody Air Force Base",
    "Redstone Arsenal", "Schriever Space Force Base",
    "Tinker Air Force Base", "Wright-Patterson Air Force Base",
}

# 3 removed in 2024 (replaced by new entries)
REGIME4_REMOVED = {
    "Cape Cod Air Force Station",  # replaced by Joint Base Cape Cod
    "Iowa National Guard Joint Force Headquarters",  # replaced by Camp Dodge
    "Lackland Air Force Base",  # merged into Joint Base San Antonio
}

# ===================================================================
# 2023 ADDITIONS (from 88 FR 57348, effective Sep 22, 2023)
# 8 installations added to Part 2, in AZ, CA, IA, ND, SD, TX
# ===================================================================

REGIME3_PART2_NEW = {
    "Dyess Air Force Base",  # Abilene, TX -- B-21 Raider
    "Edwards Air Force Base",  # Edwards, CA -- B-21 testing
    "Ellsworth Air Force Base",  # Box Elder, SD -- B-21
    "Fort Huachuca",  # Sierra Vista, AZ -- intelligence
    "Grand Forks Air Force Base",  # Grand Forks, ND -- Fufeng response
    "Iowa National Guard Joint Force Headquarters",  # Des Moines, IA
    "Laughlin Air Force Base",  # Del Rio, TX
    "Luke Air Force Base",  # Glendale, AZ
}

# ===================================================================
# FULL CURRENT LIST with regime tagging
# ===================================================================

# All Part 1 sites (current)
PART1 = [
    ("Adelphi Laboratory Center", "Adelphi, MD"),
    ("Air Force Maui Optical and Supercomputing Site", "Maui, HI"),
    ("Air Force Office of Scientific Research", "Arlington, VA"),
    ("Andersen Air Force Base", "Yigo, Guam"),
    ("Anniston Army Depot", "Anniston, AL"),
    ("Army Futures Command", "Austin, TX"),
    ("Army Research Lab--Orlando Simulations and Training Technology Center", "Orlando, FL"),
    ("Army Research Office", "Durham, NC"),
    ("Barter Island Regional Radar Site", "Barter Island, AK"),
    ("Beale Air Force Base", "Yuba City, CA"),
    ("Biometric Technology Center (Defense Forensics and Biometrics Agency)", "Clarksburg, WV"),
    ("Blue Grass Army Depot", "Richmond, KY"),
    ("Buckley Space Force Base", "Aurora, CO"),
    ("Camp Blaz", "Dededo, Guam"),
    ("Camp Mackall", "Southern Pines, NC"),
    ("Camp Navajo", "Bellemont, AZ"),
    ("Camp Roberts", "San Miguel, CA"),
    ("Cape Newenham Long Range Radar Site", "Cape Newenham, AK"),
    ("Cavalier Space Force Station", "Cavalier, ND"),
    ("Cheyenne Mountain Space Force Station", "Colorado Springs, CO"),
    ("Clear Space Force Station", "Anderson, AK"),
    ("Cold Bay Regional Radar Site", "Cold Bay, AK"),
    ("Combat Capabilities Development Command Soldier Center", "Natick, MA"),
    ("Creech Air Force Base", "Indian Springs, NV"),
    ("Davis-Monthan Air Force Base", "Tucson, AZ"),
    ("Defense Advanced Research Projects Agency", "Arlington, VA"),
    ("Detroit Arsenal", "Warren, MI"),
    ("Eareckson Air Station", "Shemya, AK"),
    ("Eielson Air Force Base", "Fairbanks, AK"),
    ("Ellington Field Joint Reserve Base", "Houston, TX"),
    ("Fairchild Air Force Base", "Spokane, WA"),
    ("Fort Belvoir", "Fairfax County, VA"),
    ("Fort Bliss", "El Paso, TX"),
    ("Fort Campbell", "Hopkinsville, KY and Clarksville, TN"),
    ("Fort Carson", "Colorado Springs, CO"),
    ("Fort Cavazos", "Killeen, TX"),
    ("Fort Detrick", "Frederick, MD"),
    ("Fort Drum", "Watertown, NY"),
    ("Fort Eisenhower", "Augusta, GA"),
    ("Fort Gregg-Adams", "Petersburg, VA"),
    ("Fort Knox", "Elizabethtown, KY"),
    ("Fort Leavenworth", "Leavenworth County, KS"),
    ("Fort Leonard Wood", "Pulaski County, MO"),
    ("Fort Meade", "Anne Arundel County, MD"),
    ("Fort Moore", "Columbus, GA"),
    ("Fort Riley", "Junction City, KS"),
    ("Fort Shafter", "Honolulu, HI"),
    ("Fort Sill", "Lawton, OK"),
    ("Fort Stewart", "Hinesville, GA"),
    ("Fort Yukon Long Range Radar Site", "Fort Yukon, AK"),
    ("Francis E. Warren Air Force Base", "Cheyenne, WY"),
    ("Guam Tracking Station", "Inarajan, Guam"),
    ("Hanscom Air Force Base", "Lexington, MA"),
    ("Hawthorne Army Depot", "Hawthorne, NV"),
    ("Holloman Air Force Base", "Alamogordo, NM"),
    ("Holston Army Ammunition Plant", "Kingsport, TN"),
    ("Indian Mountain Regional Radar Site", "Indian Mountain, AK"),
    ("Iowa Army Ammunition Plant", "Middletown, IA"),
    ("Joint Base Anacostia-Bolling", "Washington, DC"),
    ("Joint Base Andrews", "Camp Springs, MD"),
    ("Joint Base Elmendorf-Richardson", "Anchorage, AK"),
    ("Joint Base Langley-Eustis", "Hampton, VA and Newport News, VA"),
    ("Joint Base Lewis-McChord", "Tacoma, WA"),
    ("Joint Base McGuire-Dix-Lakehurst", "Lakehurst, NJ"),
    ("Joint Base Myer-Henderson Hall", "Arlington, VA"),
    ("Joint Base Pearl Harbor-Hickam", "Honolulu, HI"),
    ("Joint Expeditionary Base Little Creek-Fort Story", "Virginia Beach, VA"),
    ("Joint Systems Manufacturing Center--Lima", "Lima, OH"),
    ("Kaena Point Satellite Tracking Station", "Waianae, HI"),
    ("Kenai Regional Radar Site", "Kenai, AK"),
    ("King Salmon Air Force Station", "King Salmon, AK"),
    ("Kirtland Air Force Base", "Albuquerque, NM"),
    ("Kodiak Tracking Station", "Kodiak Island, AK"),
    ("Kotzebue Regional Radar Site", "Kotzebue, AK"),
    ("Lake City Army Ammunition Plant", "Independence, MO"),
    ("Letterkenny Army Depot", "Chambersburg, PA"),
    ("Lisburne Regional Radar Site", "Cape Lisburne, AK"),
    ("Los Angeles Air Force Base", "El Segundo, CA"),
    ("MacDill Air Force Base", "Tampa, FL"),
    ("Marine Corps Air Ground Combat Center Twentynine Palms", "Twentynine Palms, CA"),
    ("Marine Corps Air Station Beaufort", "Beaufort, SC"),
    ("Marine Corps Air Station Cherry Point", "Cherry Point, NC"),
    ("Marine Corps Air Station Miramar", "San Diego, CA"),
    ("Marine Corps Air Station New River", "Jacksonville, NC"),
    ("Marine Corps Air Station Yuma", "Yuma, AZ"),
    ("Marine Corps Base Camp Lejeune", "Jacksonville, NC"),
    ("Marine Corps Base Camp Pendleton", "Oceanside, CA"),
    ("Marine Corps Base Hawaii", "Kaneohe Bay, HI"),
    ("Marine Corps Base Hawaii, Camp H.M. Smith", "Halawa, HI"),
    ("Marine Corps Base Quantico", "Quantico, VA"),
    ("Marine Corps Logistics Base Albany", "Albany, GA"),
    ("Marine Corps Logistics Base Barstow", "Barstow, CA"),
    ("Marine Corps Support Facility Blount Island", "Jacksonville, FL"),
    ("Mark Center", "Alexandria, VA"),
    ("McAlester Army Ammunition Plant", "McAlester, OK"),
    ("Military Ocean Terminal Concord", "Concord, CA"),
    ("Military Ocean Terminal Sunny Point", "Brunswick County, NC"),
    ("Minot Air Force Base", "Minot, ND"),
    ("Naval Air Station Corpus Christi", "Corpus Christi, TX"),
    ("Naval Air Station Joint Reserve Base New Orleans", "Belle Chasse, LA"),
    ("Naval Air Station Oceana", "Virginia Beach, VA"),
    ("Naval Air Station Oceana Dam Neck Annex", "Virginia Beach, VA"),
    ("Naval Air Station Whidbey Island", "Oak Harbor, WA"),
    ("Naval Base Guam", "Apra Harbor, Guam"),
    ("Naval Base Kitsap Bangor", "Silverdale, WA"),
    ("Naval Base Point Loma", "San Diego, CA"),
    ("Naval Base San Diego", "San Diego, CA"),
    ("Naval Base Ventura County--Port Hueneme Operating Facility", "Port Hueneme, CA"),
    ("Naval Logistics Support Activity Ketchikan", "Ketchikan, AK"),
    ("Naval Logistics Support Activity LaMoure", "LaMoure, ND"),
    ("Naval Logistics Support Annex Orlando", "Okahumpka, FL"),
    ("Naval Logistics Support Facility Aguada", "Aguada, Puerto Rico"),
    ("Naval Logistics Support Facility Cutler", "Cutler, ME"),
    ("Naval Research Laboratory", "Washington, DC"),
    ("Naval Research Laboratory--Blossom Point", "Welcome, MD"),
    ("Naval Research Laboratory--Stennis Space Center", "Hancock County, MS"),
    ("Naval Research Laboratory--Tilghman", "Tilghman, MD"),
    ("Naval Station Newport", "Newport, RI"),
    ("Naval Station Norfolk", "Norfolk, VA"),
    ("Naval Submarine Base Kings Bay", "Kings Bay, GA"),
    ("Naval Submarine Base New London", "Groton, CT"),
    ("Naval Suffolk Facility", "Suffolk, VA"),
    ("Naval Support Activity Crane", "Crane, IN"),
    ("Naval Support Activity Orlando", "Orlando, FL"),
    ("Naval Support Activity Panama City", "Panama City, FL"),
    ("Naval Support Activity Philadelphia", "Philadelphia, PA"),
    ("Naval Support Facility Carderock", "Bethesda, MD"),
    ("Naval Support Facility Dahlgren", "Dahlgren, VA"),
    ("Naval Support Facility Indian Head", "Indian Head, MD"),
    ("Naval Surface Warfare Center Carderock Division--Acoustic Research Detachment", "Bayview, ID"),
    ("Naval Weapons Station Seal Beach Detachment Norco", "Norco, CA"),
    ("New Boston Air Station", "New Boston, NH"),
    ("Offutt Air Force Base", "Bellevue, NE"),
    ("Oliktok Long Range Radar Site", "Oliktok, AK"),
    ("Orchard Combat Training Center", "Boise, ID"),
    ("Peason Ridge Training Area", "Leesville, LA"),
    ("Pentagon", "Arlington, VA"),
    ("Peterson Space Force Base", "Colorado Springs, CO"),
    ("Picatinny Arsenal", "Morris County, NJ"),
    ("Pine Bluff Arsenal", "White Hall, AR"),
    ("Pinon Canyon Maneuver Site", "Tyrone, CO"),
    ("Pohakuloa Training Area", "Hilo, HI"),
    ("Point Barrow Long Range Radar Site", "Point Barrow, AK"),
    ("Portsmouth Naval Shipyard", "Kittery, ME"),
    ("Pueblo Chemical Depot", "Pueblo, CO"),
    ("Radford Army Ammunition Plant", "Radford, VA"),
    ("Red River Army Depot", "Texarkana, TX"),
    ("Rock Island Arsenal", "Rock Island, IL"),
    ("Romanzof Regional Radar Site", "Romanzof, AK"),
    ("Rome Research Laboratory", "Rome, NY"),
    ("Scott Air Force Base", "St. Clair County, IL"),
    ("Scranton Army Ammunition Plant", "Scranton, PA"),
    ("Seymour Johnson Air Force Base", "Goldsboro, NC"),
    ("Shaw Air Force Base", "Sumter, SC"),
    ("Southeast Alaska Acoustic Measurement Facility", "Ketchikan, AK"),
    ("Sparrevohn Regional Radar Site", "Sparrevohn, AK"),
    ("Tatalina Regional Radar Site", "Tatalina, AK"),
    ("Tin City Long Range Radar Site", "Tin City, AK"),
    ("Tooele Army Depot", "Tooele, UT"),
    ("Travis Air Force Base", "Fairfield, CA"),
    ("Tyndall Air Force Base", "Bay County, FL"),
    ("Watervliet Arsenal", "Watervliet, NY"),
]

# All Part 2 sites (current)
PART2 = [
    ("Aberdeen Proving Ground", "Aberdeen, MD"),
    ("Air Force Plant 42", "Palmdale, CA"),
    ("Altus Air Force Base", "Altus, OK"),
    ("Arnold Air Force Base", "Coffee County and Franklin County, TN"),
    ("Barksdale Air Force Base", "Bossier City, LA"),
    ("Camp Dodge", "Johnston, IA"),
    ("Camp Grayling", "Grayling, MI"),
    ("Camp Shelby", "Hattiesburg, MS"),
    ("Camp Williams", "Bluffdale, UT"),
    ("Cannon Air Force Base", "Clovis, NM"),
    ("Cape Canaveral Space Force Station", "Cape Canaveral, FL"),
    ("Chocolate Mountain Aerial Gunnery Range", "Niland, CA"),
    ("Columbus Air Force Base", "Columbus, MS"),
    ("Dare County Range", "Manns Harbor, NC"),
    ("Dover Air Force Base", "Delmarva, DE"),
    ("Dyess Air Force Base", "Abilene, TX"),
    ("Edwards Air Force Base", "Edwards, CA"),
    ("Eglin Air Force Base", "Valparaiso, FL"),
    ("Ellsworth Air Force Base", "Box Elder, SD"),
    ("Fallon Range Complex", "Fallon, NV"),
    ("Fort Greely", "Delta Junction, AK"),
    ("Fort Huachuca", "Sierra Vista, AZ"),
    ("Fort Irwin", "San Bernardino County, CA"),
    ("Fort Johnson", "Vernon Parish, LA"),
    ("Fort Liberty", "Fayetteville, NC"),
    ("Fort Novosel", "Dale County, AL"),
    ("Fort Wainwright", "Fairbanks, AK"),
    ("Goodfellow Air Force Base", "San Angelo, TX"),
    ("Grand Forks Air Force Base", "Grand Forks, ND"),
    ("Hardwood Range", "Necedah, WI"),
    ("Hill Air Force Base", "Ogden, UT"),
    ("Joint Base Cape Cod", "Sandwich, MA"),
    ("Joint Base Charleston", "North Charleston, SC"),
    ("Joint Base San Antonio", "San Antonio, TX"),
    ("Laughlin Air Force Base", "Del Rio, TX"),
    ("Little Rock Air Force Base", "Little Rock, AR"),
    ("Luke Air Force Base", "Glendale, AZ"),
    ("Malmstrom Air Force Base", "Great Falls, MT"),
    ("Maxwell-Gunter Air Force Base", "Montgomery, AL"),
    ("Moody Air Force Base", "Valdosta, GA"),
    ("Mountain Home Air Force Base", "Mountain Home, ID"),
    ("Muscatatuck Urban Training Center", "Butlerville, IN"),
    ("Naval Air Station Meridian", "Meridian, MS"),
    ("Naval Air Station Patuxent River", "Lexington Park, MD"),
    ("Naval Air Weapons Station China Lake", "Ridgecrest, CA"),
    ("Naval Base Kitsap--Keyport", "Keyport, WA"),
    ("Naval Base Ventura County--Point Mugu Operating Facility", "Point Mugu, CA"),
    ("Naval Weapons Systems Training Facility Boardman", "Boardman, OR"),
    ("Nellis Air Force Base", "Las Vegas, NV"),
    ("Nevada Test and Training Range", "Tonopah, NV"),
    ("Pacific Missile Range Facility", "Kekaha, HI"),
    ("Patrick Space Force Base", "Cocoa Beach, FL"),
    ("Redstone Arsenal", "Huntsville, AL"),
    ("Schriever Space Force Base", "Colorado Springs, CO"),
    ("Tinker Air Force Base", "Midwest City, OK"),
    ("Townsend Bombing Range", "McIntosh County, GA"),
    ("Tropic Regions Test Center", "Wahiawa, HI"),
    ("Utah Test and Training Range", "Barro, UT"),
    ("Vance Air Force Base", "Enid, OK"),
    ("Vandenberg Space Force Base", "Lompoc, CA"),
    ("West Desert Test Center", "Dugway, UT"),
    ("White Sands Missile Range", "White Sands Missile Range, NM"),
    ("Whiteman Air Force Base", "Knob Noster, MO"),
    ("Wright-Patterson Air Force Base", "Dayton, OH"),
    ("Yuma Proving Ground", "Yuma, AZ"),
]


def determine_regime(name, part):
    """Determine which regime added this site."""
    if name in REGIME4_PART1_NEW:
        return "2024"
    if name in REGIME4_PART2_NEW:
        return "2024"
    if name in REGIME4_MOVED_P1_TO_P2:
        return "2020_moved_2024"  # Original 2020 Part 1, moved to Part 2 in 2024
    if name in REGIME3_PART2_NEW:
        return "2023"
    return "2020"


def main():
    rows = []

    for name, loc in PART1:
        regime = determine_regime(name, 1)
        rows.append({
            "site_name": name,
            "location": loc,
            "current_part": 1,
            "threshold_miles": 1,
            "regime_added": regime,
            "latitude": "",
            "longitude": "",
            "conus": "N" if any(x in loc for x in ["AK", "HI", "Guam", "Puerto Rico"]) else "Y",
        })

    for name, loc in PART2:
        regime = determine_regime(name, 2)
        rows.append({
            "site_name": name,
            "location": loc,
            "current_part": 2,
            "threshold_miles": 100,
            "regime_added": regime,
            "latitude": "",
            "longitude": "",
            "conus": "N" if any(x in loc for x in ["AK", "HI", "Guam", "Puerto Rico"]) else "Y",
        })

    # Write CSV
    outpath = "data/outputs/cfius_appendix_a_all_regimes.csv"
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "site_name", "location", "current_part", "threshold_miles",
            "regime_added", "latitude", "longitude", "conus",
        ])
        w.writeheader()
        w.writerows(rows)

    # Summary
    regime_counts = {}
    for r in rows:
        key = r["regime_added"]
        regime_counts[key] = regime_counts.get(key, 0) + 1

    conus_count = sum(1 for r in rows if r["conus"] == "Y")

    print(f"Saved: {outpath}")
    print(f"Total sites: {len(rows)}")
    print(f"CONUS sites: {conus_count}")
    print(f"\nRegime distribution:")
    for regime, count in sorted(regime_counts.items()):
        print(f"  {regime}: {count}")
    print(f"\nPart distribution:")
    p1 = sum(1 for r in rows if r["current_part"] == 1)
    p2 = sum(1 for r in rows if r["current_part"] == 2)
    print(f"  Part 1 (1-mile): {p1}")
    print(f"  Part 2 (100-mile): {p2}")

    # Verify counts against Federal Register
    print(f"\n=== VERIFICATION ===")
    print(f"2024 Part 1 new: {sum(1 for r in rows if r['regime_added']=='2024' and r['current_part']==1)} (expected 40)")
    print(f"2024 Part 2 new: {sum(1 for r in rows if r['regime_added']=='2024' and r['current_part']==2)} (expected 19)")
    print(f"2024 moved P1->P2: {sum(1 for r in rows if r['regime_added']=='2020_moved_2024')} (expected 8)")
    print(f"2023 Part 2 new: {sum(1 for r in rows if r['regime_added']=='2023')} (expected 8)")
    print(f"2020 original: {sum(1 for r in rows if r['regime_added']=='2020')} (expected ~152)")


if __name__ == "__main__":
    main()
