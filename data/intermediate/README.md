# Intermediate data

Written by `src/01_legal_scope.py` and `src/02_trade_and_production.py`. One row per
8-digit CN tariff line that at least one position covers (661 lines), except the
supplier file.

## 01_cn8_legal_coverage.csv

| Column | Meaning |
|---|---|
| cn8, hs6 | Tariff line and its six-digit HS code |
| product_group | Display group (`src/config.py`) |
| commission, council, parliament | 2 = fully covered, 1 = partly ("ex" entry, or only narrower lines listed), 0 = not covered |
| commission_basis, council_basis, parliament_basis | Why: "Listed", "Via 8413", "Listed (ex: partial)", "Excluded", ... |
| first_listed_by | Commission, else Council, else Parliament |

## 02_cn8_trade_production.csv

| Column | Meaning |
|---|---|
| imports_eur_m, imports_kt | Extra-EU imports, € million and thousand tonnes a year, 2022–24 (Comext) |
| exports_eur_m | Extra-EU exports, € million a year (Comext) |
| prodcom_code, prodcom_source | Prodcom code(s) matched to the line, and how they were matched |
| production_eur_m, pc_exports_eur_m, pc_imports_eur_m | EU production, exports and imports of those Prodcom codes, € million a year (Prodcom; Comext where Prodcom has no trade) |
| import_share_eu_market | pc_imports ÷ (pc_imports + production) |
| import_share_consumption | pc_imports ÷ (production − pc_exports + pc_imports), capped at 1 |
| exports_over_production | pc_exports ÷ production |

A Prodcom code often spans several tariff lines, and each line then carries the
code's full figures: sum the trade columns, but not the production columns.

## 02_cn8_imports_by_partner.csv

| Column | Meaning |
|---|---|
| cn8, partner | Tariff line and supplier country (ISO code; Comext uses XS for Serbia) |
| imports_eur_m | Imports from that country, € million a year, 2022–24 |
