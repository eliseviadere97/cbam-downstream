"""Step 5: the headline figures quoted in the Insight, from the final dataset.

Reads   data/final/cbam_downstream_products.csv
Writes  docs/headline_figures.csv   (and prints the same tables)

The cut-offs come from src/config.py, so changing one there changes every figure.

Run from the repository root:  python src/05_headline_figures.py
"""
import pandas as pd

from config import CARBON_PRICE, IMPORT_SHARE_CUT, LEAKAGE_CUT, ROOT, SUPPLIER_CUT

FINAL = ROOT / "data" / "final" / "cbam_downstream_products.csv"
OUTPUT = ROOT / "docs" / "headline_figures.csv"
LOW_CHARGE = 0.01          # "charged under 1%"

df = pd.read_csv(FINAL, dtype={"hs6": str})

# Derived columns, one line each.
df["cbam_cost_eur_m"] = df["imports_eur_m"] * df["cbam_charge"]           # what importers would pay
df["co2_mt"] = df["cbam_cost_eur_m"] / CARBON_PRICE                         # EUR m / (EUR per t) = Mt
df["china_imports_eur_m"] = df["imports_eur_m"] * df["china_share"]
df["placed"] = df["import_share_eu_market"].notna()
df["leakage"] = df["cbam_charge"] >= LEAKAGE_CUT
df["security"] = (df["placed"]
                  & (df["import_share_eu_market"] > IMPORT_SHARE_CUT)
                  & (df["main_supplier_share"] > SUPPLIER_CUT))
df["quadrant"] = "Neither"
df.loc[df["leakage"], "quadrant"] = "Carbon leakage"
df.loc[df["security"], "quadrant"] = "Supply security"
df.loc[df["leakage"] & df["security"], "quadrant"] = "Both"
df.loc[~df["placed"], "quadrant"] = "Not placed"


def summarise(rows):
    imports = rows["imports_eur_m"].sum()
    return pd.Series({
        "map_rows": len(rows),
        "cn8_lines": rows["cn8_lines"].sum(),
        "imports_eur_bn": imports / 1000,
        "co2_mt": rows["co2_mt"].sum(),
        "co2_mt_per_eur_bn": rows["co2_mt"].sum() / (imports / 1000),
        "avg_cbam_charge": rows["cbam_cost_eur_m"].sum() / imports,
        "share_imports_under_1pct": rows.loc[rows["cbam_charge"] < LOW_CHARGE, "imports_eur_m"].sum() / imports,
        "share_imports_above_leakage_cut": rows.loc[rows["leakage"], "imports_eur_m"].sum() / imports,
        "china_share_imports": rows["china_imports_eur_m"].sum() / imports,
        "china_share_co2": (rows["co2_mt"] * rows["china_share"]).sum() / rows["co2_mt"].sum(),
        "cbam_cost_full_eur_bn": rows["cbam_cost_eur_m"].sum() / 1000,
    })


# Table 1: each position's whole list.
lists = pd.DataFrame({
    "Commission list": summarise(df[df["on_commission"] == 1]),
    "Council list": summarise(df[df["on_council"] == 1]),
    "Parliament list": summarise(df[df["on_parliament"] == 1]),
}).T

# Table 2: what each position adds (each row credited to the first position that lists it).
adds = df.groupby("first_listed_by").apply(summarise, include_groups=False)
adds.index = [f"First listed by {p}" for p in adds.index]

# Table 3: imports by worry quadrant, EUR bn.
quadrants = (df.pivot_table(index="first_listed_by", columns="quadrant", values="imports_eur_m",
                            aggfunc="sum", fill_value=0) / 1000)
quadrants = quadrants[["Carbon leakage", "Both", "Supply security", "Neither", "Not placed"]]

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 10)
print("Whole lists\n", lists.round(3).T, "\n")
print("What each position adds\n", adds.round(3).T, "\n")
print("Imports by quadrant, EUR bn\n", quadrants.round(1), "\n")
both = quadrants["Both"].sum()
print(f"Overlap ('Both'): EUR {both:.1f}bn, {both / quadrants.to_numpy().sum():.0%} of all imports")
print(f"Parliament list vs Commission list: {lists.loc['Parliament list', 'imports_eur_bn'] / lists.loc['Commission list', 'imports_eur_bn']:.1f}x imports, "
      f"{lists.loc['Parliament list', 'co2_mt'] / lists.loc['Commission list', 'co2_mt']:.1f}x CO2")

OUTPUT.parent.mkdir(exist_ok=True)
pd.concat([lists, adds]).round(4).to_csv(OUTPUT)
print(f"\nWrote {OUTPUT.relative_to(ROOT)}")
