"""Step 2: trade and EU production for each covered tariff line.

Reads   data/intermediate/01_cn8_legal_coverage.csv
        data/raw/comext/*.csv.gz     Eurostat Comext DS-045409: EU27 trade by CN8, 2022-24
        data/raw/prodcom/*           Eurostat Prodcom (EU production) and the Prodcom-CN correspondences
Writes  data/intermediate/02_cn8_imports_by_partner.csv   extra-EU imports by supplier country, EUR m a year
        data/intermediate/02_cn8_trade_production.csv     one row per CN8 line: trade, EU production, ratios

All Comext values are annual averages over 2022-24 (sum of the three years / 3).

EU production comes from Prodcom, which uses its own product codes. Each CN8 line is matched to Prodcom codes:
  1. the 2025 Prodcom-CN correspondence (Statistics Netherlands, CBS), for codes with 2019-24 data;
  2. if that gives nothing, the 2014 CN8-Prodcom concordance of Magerman (ULB);
  3. if there is still no production, the 2025 Prodcom release (new NACE Rev. 2.1 codes), single year.
Where Prodcom gives production but not trade, trade is taken from Comext for the same Prodcom code.
A Prodcom code often spans several CN8 lines; each line then carries that code's figures, which is why the
ratios below (not the levels) are what later steps use.

Run from the repository root:  python src/02_trade_and_production.py
"""
import pandas as pd

from config import INTERMEDIATE, RAW, YEARS

N_YEARS = len(YEARS)
cov = pd.read_csv(INTERMEDIATE / "01_cn8_legal_coverage.csv", dtype={"cn8": str, "hs6": str})
lines = list(cov.cn8)

# ---- 1. Comext ---------------------------------------------------------------------------------------------
frames = []
for path in sorted((RAW / "comext").glob("*.csv.gz")):
    t = pd.read_csv(path, dtype=str)
    t = t[t["product"].isin(lines) & t.TIME_PERIOD.astype(int).isin(YEARS)]
    frames.append(t)
trade = pd.concat(frames)
trade["value"] = pd.to_numeric(trade.OBS_VALUE, errors="coerce")
is_qty = trade.indicators == "QUANTITY_IN_100KG"
trade.loc[is_qty, "value"] = trade.loc[is_qty, "value"] * 100          # quantities: 100 kg units -> kg
trade = trade.rename(columns={"product": "cn8"})


def three_year_average(rows, indicator):
    """Average over the window, by CN8, in the indicator's own unit."""
    return rows[rows.indicators == indicator].groupby("cn8").value.sum() / N_YEARS


extra = trade[trade.partner == "EXT_EU27_2020"]           # EU27 trade with the rest of the world
imports = extra[extra.flow == "1"]
exports = extra[extra.flow == "2"]

out = pd.DataFrame(index=pd.Index(lines, name="cn8"))
out["imports_eur_m"] = (three_year_average(imports, "VALUE_IN_EUROS") / 1e6).reindex(out.index).fillna(0)
out["imports_kt"] = (three_year_average(imports, "QUANTITY_IN_100KG") / 1e6).reindex(out.index).fillna(0)  # kg -> kt
out["exports_eur_m"] = (three_year_average(exports, "VALUE_IN_EUROS") / 1e6).reindex(out.index).fillna(0)

# Imports by supplier country. Codes starting with Q (secret, unspecified, ship stores) are left out.
by_partner = trade[(trade.partner.str.len() == 2) & ~trade.partner.str.startswith("Q")
                   & (trade.flow == "1") & (trade.indicators == "VALUE_IN_EUROS")]
by_partner = (by_partner.groupby(["cn8", "partner"]).value.sum() / N_YEARS / 1e6).rename("imports_eur_m").reset_index()

# ---- 2. Prodcom --------------------------------------------------------------------------------------------


def prodcom_averages(path):
    """EU27 production, exports and imports by Prodcom code, EUR m, averaged over the years in the file."""
    p = pd.read_csv(path, dtype=str)
    p = p[p.reporter == "EU27_2020"]
    p = p.pivot_table(index=["product", "TIME_PERIOD"], columns="indicators", values="OBS_VALUE",
                      aggfunc="first").reset_index()
    for k in ("PRODVAL", "EXPVAL", "IMPVAL"):
        p[k] = pd.to_numeric(p[k], errors="coerce") if k in p else float("nan")
    a = p.groupby("product")[["PRODVAL", "EXPVAL", "IMPVAL"]].mean() / 1e6
    return a.rename(columns={"PRODVAL": "production_eur_m", "EXPVAL": "pc_exports_eur_m", "IMPVAL": "pc_imports_eur_m"})


def match_to_cn8(codes, use_magerman):
    """Sum each CN8 line's Prodcom codes. Only Prodcom codes with production data are used."""
    have = set(codes.index[codes.production_eur_m.notna()])
    corr = pd.read_excel(RAW / "prodcom" / "prodcom_cn_correspondence_2025.xlsx", dtype=str)
    corr = pd.DataFrame({"prodcom_code": corr["Prodcom code"].str.replace(r"\D", "", regex=True),
                         "cn8": corr["Commodity code"].str.replace(r"\D", "", regex=True),
                         "source": "Prodcom-CN 2025 (CBS)"})
    corr = corr[corr.cn8.str.len() == 8]
    if use_magerman:
        matched = set(corr.loc[corr.prodcom_code.isin(have), "cn8"])
        mag = pd.read_csv(RAW / "prodcom" / "cn8_prodcom_concordance_magerman.tsv.gz", sep="\t", dtype=str)
        mag = mag[mag.year == "2014"]
        mag = pd.DataFrame({"prodcom_code": mag.pc8.str.zfill(8), "cn8": mag.cn8.str.zfill(8),
                            "source": "CN-PC8 2014 (Magerman) fallback"})
        mag = mag[~mag.cn8.isin(matched) & mag.prodcom_code.isin(have)]
        corr = pd.concat([corr[corr.prodcom_code.isin(have)], mag], ignore_index=True)
    j = corr.merge(codes, left_on="prodcom_code", right_index=True, how="inner")
    total = lambda x: x.sum(min_count=1)
    return j.groupby("cn8").agg(prodcom_code=("prodcom_code", lambda s: ";".join(sorted(set(s)))),
                                prodcom_source=("source", "first"),
                                production_eur_m=("production_eur_m", total),
                                pc_exports_eur_m=("pc_exports_eur_m", total),
                                pc_imports_eur_m=("pc_imports_eur_m", total))


PC = ["prodcom_code", "prodcom_source", "production_eur_m", "pc_exports_eur_m", "pc_imports_eur_m"]
out = out.join(match_to_cn8(prodcom_averages(RAW / "prodcom" / "prodcom_2019_2024.csv.gz"), use_magerman=True))

# Lines with no 2019-24 production: use the 2025 release (single year) where it has production.
p25 = match_to_cn8(prodcom_averages(RAW / "prodcom" / "prodcom_2025.csv.gz"), use_magerman=False)
p25 = p25.reindex(out.index)
gap = ~(out.production_eur_m > 0) & (p25.production_eur_m > 0)
for k in ("prodcom_code", "production_eur_m", "pc_exports_eur_m", "pc_imports_eur_m"):
    out.loc[gap, k] = p25.loc[gap, k]
out.loc[gap, "prodcom_source"] = "Prodcom 2025 (NACE Rev. 2.1), single year"

# Production but no trade in Prodcom: take extra-EU trade from Comext, summed over lines sharing the Prodcom code.
missing = (out.production_eur_m > 0) & (out.pc_imports_eur_m.isna() | out.pc_exports_eur_m.isna())
same_code = out.groupby("prodcom_code")[["imports_eur_m", "exports_eur_m"]].transform("sum")
out.loc[missing, "pc_imports_eur_m"] = same_code.loc[missing, "imports_eur_m"]
out.loc[missing, "pc_exports_eur_m"] = same_code.loc[missing, "exports_eur_m"]
out.loc[missing, "prodcom_source"] = out.loc[missing, "prodcom_source"].fillna("") + " + trade from Comext"

# ---- 3. Ratios (only where EU production is positive) -------------------------------------------------------
P, X, M = out.production_eur_m, out.pc_exports_eur_m, out.pc_imports_eur_m
ok = P > 0
out["import_share_eu_market"] = (M / (M + P)).where(ok)                 # imports / (production + imports)
out["import_share_consumption"] = (M / (P - X + M)).where(ok & (P - X + M > 0)).clip(upper=1.0)
out["exports_over_production"] = (X / P).where(ok)

out.reset_index().to_csv(INTERMEDIATE / "02_cn8_trade_production.csv", index=False)
by_partner.to_csv(INTERMEDIATE / "02_cn8_imports_by_partner.csv", index=False)

print(f"Lines: {len(out)}; extra-EU imports EUR {out.imports_eur_m.sum() / 1000:.1f}bn a year")
print(f"Lines with EU production data: {int(ok.sum())}; by source: {out.prodcom_source.value_counts().to_dict()}")
print(f"Supplier rows: {len(by_partner):,} ({by_partner.partner.nunique()} countries)")
