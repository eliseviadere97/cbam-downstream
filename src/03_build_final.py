"""Step 3: group tariff lines into the rows of the chart.

Reads   data/intermediate/01_cn8_legal_coverage.csv
        data/intermediate/02_cn8_trade_production.csv
        data/intermediate/02_cn8_imports_by_partner.csv
        data/raw/prodcom/prodcom_cn_correspondence_2025.xlsx and data/raw/legal/*  (product names only)
Writes  data/final/cbam_downstream_products.csv   one row per circle on the chart

A chart row is a six-digit HS code together with the position that first lists its lines, so every euro of
imports is credited to exactly one position (e.g. HS 850440: rectifiers from the Council, static converters
from Parliament, two rows).

For each row:
  imports            sum of its lines' extra-EU imports
  main supplier      largest supplier country; its share of the row's extra-EU imports (same for China)
  CBAM charge        metal content x emission factor x carbon price / (import value per tonne)
  market shares      import-weighted averages of the lines' ratios from step 2
Rows with no imports, or no import quantity (so no price per tonne), are dropped. Values are rounded as shown.

Run from the repository root:  python src/03_build_final.py
"""
import csv
import re

import numpy as np
import pandas as pd

import config as C

LEGAL = C.RAW / "legal"
POSITION_CODE = {"Commission": "com", "Council": "cnl", "Parliament": "ep"}  # short codes, also used by the page

cov = pd.read_csv(C.INTERMEDIATE / "01_cn8_legal_coverage.csv", dtype={"cn8": str, "hs6": str})
tp = pd.read_csv(C.INTERMEDIATE / "02_cn8_trade_production.csv", dtype={"cn8": str, "prodcom_code": str})
partners = pd.read_csv(C.INTERMEDIATE / "02_cn8_imports_by_partner.csv", dtype={"cn8": str})

lines = cov.merge(tp, on="cn8")
lines["row"] = lines.hs6 + "|" + lines.first_listed_by.map(POSITION_CODE)   # e.g. "850440|cnl"

# ---- 1. Totals and supplier shares by row -------------------------------------------------------------------
rows = lines.groupby("row").agg(hs6=("hs6", "first"), first_listed_by=("first_listed_by", "first"),
                                product_group=("product_group", "first"), cn8_lines=("cn8", "size"),
                                imports_eur_m=("imports_eur_m", "sum"), imports_kt=("imports_kt", "sum"))
for p in POSITION_CODE:
    rows["on_" + p.lower()] = (lines.groupby("row")[p.lower()].max() > 0).astype(int)

partners["row"] = partners.cn8.map(lines.set_index("cn8").row)
by_country = partners.groupby(["row", "partner"]).imports_eur_m.sum()
# Shares of the row's extra-EU imports (never below the sum of the countries listed in the download).
denominator = pd.concat([rows.imports_eur_m.where(rows.imports_eur_m > 0), by_country.groupby(level=0).sum()],
                        axis=1).max(axis=1)
shares = by_country / denominator.reindex(by_country.index.get_level_values(0)).values
rows["main_supplier"] = shares.groupby(level=0).idxmax().map(lambda t: t[1])
rows["main_supplier_share"] = shares.groupby(level=0).max()
rows["china_share"] = shares.xs("CN", level=1).reindex(rows.index).fillna(0.0)

# ---- 2. CBAM charge -----------------------------------------------------------------------------------------
chapter = rows.hs6.str[:2]
metal = np.where(chapter.isin(["73", "76"]), C.METAL_CONTENT_73_76, C.METAL_CONTENT_OTHER)
factor = np.where(chapter == "76", C.EMISSION_FACTOR_ALUMINIUM, C.EMISSION_FACTOR_STEEL)
eur_per_tonne = rows.imports_eur_m / rows.imports_kt.replace(0, np.nan) * 1000     # EUR m / kt = EUR per kg
rows["cbam_charge"] = metal * factor * C.CARBON_PRICE / eur_per_tonne

# ---- 3. Market shares: import-weighted averages of the lines' ratios ----------------------------------------
lines["weight"] = lines.imports_eur_m.fillna(0).clip(lower=1e-9)   # lines with no imports count (almost) nothing
for col in ("import_share_consumption", "import_share_eu_market", "exports_over_production"):
    x = lines.dropna(subset=[col])
    rows[col] = (x[col] * x.weight).groupby(x.row).sum() / x.weight.groupby(x.row).sum()
rows["main_supplier_share_consumption"] = rows.main_supplier_share * rows.import_share_consumption
rows["main_supplier_share_market"] = rows.main_supplier_share * rows.import_share_eu_market

# ---- 4. Product names: the description of the row's largest line that has one -------------------------------
corr = pd.read_excel(C.RAW / "prodcom" / "prodcom_cn_correspondence_2025.xlsx", dtype=str)
corr["cn8"] = corr["Commodity code"].str.replace(r"\D", "", regex=True)
names = corr.drop_duplicates("cn8").set_index("cn8")["Commodity Description"].to_dict()
for f in ("parliament_amendment_83.csv", "council_note1_additions.csv"):   # used only where the CBS file has none
    for code, text in pd.read_csv(LEGAL / f, dtype=str)[["code", "description"]].itertuples(index=False):
        names.setdefault(code, text)


def tidy(s):
    """Drop '(excl. ...)' clauses and 'n.e.s.', capitalise, cut to 150 characters."""
    s = re.sub(r'\s*\((excl|excluding|other than)[^()]*(\([^()]*\)[^()]*)*\)', "", s or "").replace('"', "")
    s = re.sub(r"\s+", " ", s).strip(" ,;.")
    s = re.sub(r"\s*,?\s*n\.e\.s\.?$", "", s)
    s = s[:1].upper() + s[1:]
    return s if len(s) <= 150 else s[:147].rsplit(" ", 1)[0] + "…"


rows["product"] = ""
for row, g in lines.sort_values("imports_eur_m", ascending=False).groupby("row", sort=False):
    rows.loc[row, "product"] = next((tidy(names[c]) for c in g.cn8 if c in names), "")
for (hs6, pos), text in C.NAME_OVERRIDES.items():
    rows.loc[f"{hs6}|{POSITION_CODE[pos]}", "product"] = text

# ---- 5. Keep, round and write ------------------------------------------------------------------------------
rows = rows[(rows.imports_eur_m > 0) & rows.cbam_charge.notna()]
rows["main_supplier"] = rows.main_supplier.map(lambda c: C.COUNTRY_NAMES.get(c, c))
DECIMALS = {"imports_eur_m": 1, "main_supplier_share": 3, "china_share": 3, "import_share_eu_market": 3,
            "import_share_consumption": 3, "main_supplier_share_market": 3, "main_supplier_share_consumption": 3,
            "exports_over_production": 2, "cbam_charge": 5}
COLUMNS = ["hs6", "product", "product_group", "cn8_lines", "first_listed_by", "on_commission", "on_council",
           "on_parliament", "imports_eur_m", "main_supplier", "main_supplier_share", "china_share",
           "import_share_eu_market", "import_share_consumption", "main_supplier_share_market",
           "main_supplier_share_consumption", "exports_over_production", "cbam_charge"]

C.FINAL.mkdir(parents=True, exist_ok=True)
with open(C.FINAL / "cbam_downstream_products.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["map_order"] + COLUMNS)
    for i, (_, r) in enumerate(rows.iterrows(), 1):   # rows are in order of HS6 code, then position code
        cells = []
        for col in COLUMNS:
            v = r[col]
            if col in DECIMALS:
                cells.append("" if pd.isna(v) else repr(float(round(v, DECIMALS[col]))))
            else:
                cells.append(v)
        w.writerow([i] + cells)

print(f"Chart rows: {len(rows)} from {len(lines)} lines; extra-EU imports EUR {rows.imports_eur_m.sum() / 1000:.1f}bn")
print("Rows by first position:", rows.first_listed_by.value_counts().to_dict())
