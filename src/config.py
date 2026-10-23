"""Every assumption and fixed choice in one place. The numbered scripts import from here."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERMEDIATE = ROOT / "data" / "intermediate"
FINAL = ROOT / "data" / "final"

# Trade window: Comext values are averaged over these years.
YEARS = [2022, 2023, 2024]

# CBAM charge = metal content x emission factor x carbon price / import price per tonne (full phase-in).
CARBON_PRICE = 82.40           # EUR per tonne of CO2, EU ETS price of 5 October 2026
EMISSION_FACTOR_STEEL = 1.9    # tCO2 per tonne of steel (assumption; not the CBAM default values)
EMISSION_FACTOR_ALUMINIUM = 1.7  # tCO2 per tonne of aluminium, used for chapter 76
METAL_CONTENT_73_76 = 1.0      # articles of iron or steel (ch. 73) and of aluminium (ch. 76) are taken as all metal
METAL_CONTENT_OTHER = 0.79     # other goods: average steel/aluminium content of the Commission's list (EPRS)

# Cut-offs used in the chart and the Insight (fixed lines, not medians).
LEAKAGE_CUT = 0.015            # carbon-leakage worry: CBAM charge at or above 1.5% of price
IMPORT_SHARE_CUT = 1 / 3       # supply-security worry: imports above a third of the EU market ...
SUPPLIER_CUT = 0.5             # ... and one country above half of those imports

# Display groups for the chart (CER classification). A code goes to the group with the longest matching prefix.
GROUPS = [
    ("Steel scrap", ["7204"]),
    ("Wire, ropes, netting and fencing", ["7312", "7314"]),
    ("Nails, screws and fasteners", ["7317", "7318", "7415"]),
    ("Springs", ["7320"]),
    ("Stoves, cookers and barbecues", ["7321"]),
    ("Household and sanitary articles", ["7323", "7324", "7615"]),
    ("Other iron and steel articles", ["73"]),
    ("Aluminium articles", ["7616"]),
    ("Mountings, fittings and closures", ["8302", "8309"]),
    ("Saw blades and metal-working tools", ["8202", "8207"]),
    ("Boilers and steam turbines", ["8402", "8403", "8406"]),
    ("Engines, turbines and parts", ["8407", "8408", "8409", "8410", "8411"]),
    ("Pumps and compressors", ["8413", "8414"]),
    ("Refrigeration, air-con and heat pumps", ["8415", "8418"]),
    ("Furnaces and industrial heating", ["8416", "8417", "8419"]),
    ("Lifting and handling equipment", ["8425", "8426", "8427", "8428"]),
    ("Construction and mining machinery", ["8429", "8430", "8431", "8474"]),
    ("Farm machinery", ["8432"]),
    ("Laundry and textile machinery", ["8450", "8451"]),
    ("Other industrial machinery", ["8420", "8421", "8422", "8424", "8454", "8455", "8464", "8479", "8480", "8515"]),
    ("Valves, bearings and gears", ["8481", "8482", "8483"]),
    ("Motors, generators and transformers", ["8501", "8502", "8503", "8504"]),
    ("Domestic electrical appliances", ["8508", "8516"]),
    ("Insulated wire and cables", ["8544"]),
    ("Railway parts", ["8607"]),
    ("Trucks, vehicle parts and trailers", ["8704", "8706", "8707", "8708", "8716"]),
    ("Medical and measuring instruments", ["9018", "9027"]),
    ("Furniture, seats and mattresses", ["9401", "9403", "9404"]),
    ("Prefabricated buildings", ["9406"]),
]

# Country names shown on the chart (Comext uses ISO codes; XS = Serbia in Comext).
COUNTRY_NAMES = {
    "CN": "China", "TR": "Turkey", "IN": "India", "US": "United States", "GB": "Britain", "CH": "Switzerland",
    "KR": "South Korea", "JP": "Japan", "TW": "Taiwan", "VN": "Vietnam", "TH": "Thailand", "MY": "Malaysia",
    "ID": "Indonesia", "UA": "Ukraine", "XS": "Serbia", "BA": "Bosnia", "MK": "North Macedonia", "AL": "Albania",
    "ME": "Montenegro", "MD": "Moldova", "GE": "Georgia", "MA": "Morocco", "TN": "Tunisia", "EG": "Egypt",
    "ZA": "South Africa", "BR": "Brazil", "MX": "Mexico", "CA": "Canada", "RU": "Russia", "BY": "Belarus",
    "NO": "Norway", "IL": "Israel", "SA": "Saudi Arabia", "AE": "UAE", "PK": "Pakistan", "BD": "Bangladesh",
    "PH": "Philippines", "SG": "Singapore", "HK": "Hong Kong", "AU": "Australia", "AR": "Argentina",
    "KZ": "Kazakhstan", "LK": "Sri Lanka", "XK": "Kosovo",
}

# Product names that no source file provides, filled by hand.
NAME_OVERRIDES = {
    ("850300", "Parliament"): "Parts of electric motors, generators and generating sets",  # CN 8503 heading text
}


def group_of(code):
    best, best_len = "Unassigned", 0
    for name, prefixes in GROUPS:
        for p in prefixes:
            if code.startswith(p) and len(p) > best_len:
                best, best_len = name, len(p)
    return best
