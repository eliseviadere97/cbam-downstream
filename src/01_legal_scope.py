"""Step 1: which tariff lines does each position cover?

Reads   data/raw/legal/*.csv        the three positions' product lists, transcribed from the legal texts
        data/raw/comext/*.csv.gz    only to get the list of 8-digit CN codes the EU actually traded in 2022-24
Writes  data/intermediate/01_cn8_legal_coverage.csv   one row per downstream CN8 line covered by at least one position

How a list "covers" a CN8 line (function `cover` below):
  - the line is printed in the list                      -> 2 (fully), or 1 if printed with "ex" (only part of it)
  - a broader code containing it is printed (e.g. 8413)  -> 2, or 1 if that broader code carries "ex"
  - only narrower codes inside it are printed            -> 1 (partly)
  - otherwise, or the line is expressly excluded         -> 0
Lines already covered by today's CBAM (Regulation 2023/956), and all of chapter 72 (basic iron and steel),
are dropped: only downstream goods are kept.

Run from the repository root:  python src/01_legal_scope.py
"""
import pandas as pd

from config import INTERMEDIATE, RAW, YEARS, group_of

LEGAL = RAW / "legal"

# ---- 1. The three lists, as (code, ex) pairs ----------------------------------------------------------------
commission_table = pd.read_csv(LEGAL / "commission_annex_i.csv", dtype=str)
commission = [(c, ex == "1") for c, ex in zip(commission_table.code, commission_table.ex)]

# Council: the Commission's table, minus the three lines deleted by NOTE 2, plus the 200 lines added by NOTE 1.
deleted = set(pd.read_csv(LEGAL / "council_note2_deletions.csv", dtype=str).code)
added = pd.read_csv(LEGAL / "council_note1_additions.csv", dtype=str).code
council = [(c, ex) for c, ex in commission if c not in deleted] + [(c, False) for c in added]

# Parliament: the Commission's table (working assumption: Parliament's amendments add to it rather than
# replace it), plus the 276 lines listed one by one in Amendment 83, plus the broad entries of Amendments 110
# and 135 (all of chapter 73 and whole headings such as 8413 or 8504).
am83 = pd.read_csv(LEGAL / "parliament_amendment_83.csv", dtype=str).code
broad = pd.read_csv(LEGAL / "parliament_broad_entries.csv", dtype=str).read_as
parliament = commission + [(c, False) for c in am83] + [(c, False) for c in broad]

# Lines carved out of the lists.
excl = pd.read_csv(LEGAL / "exclusions.csv", dtype=str)
exclusions = {
    "Commission": list(excl.code[excl.applies_to_commission == "1"]),
    "Council": list(excl.code[excl.applies_to_council == "1"]),
    "Parliament": list(excl.code[excl.applies_to_parliament == "1"]),
}
lists = {"Commission": commission, "Council": council, "Parliament": parliament}

# Today's CBAM scope, to separate new downstream goods from goods already covered.
base = pd.read_csv(LEGAL / "baseline_regulation_2023_956.csv", dtype=str)
baseline_in = list(base.code[base.status == "In scope"])
baseline_exceptions = list(base.code[base.status.str.startswith("Exception")])


def cover(code, entries, excluded):
    """Return (flag, basis): 2 = fully covered, 1 = partly covered, 0 = not covered."""
    if any(code.startswith(e) for e in excluded):
        return 0, "Excluded"
    exact = [ex for c, ex in entries if c == code]
    if exact:
        return (1, "Listed (ex: partial)") if any(exact) else (2, "Listed")
    # Broader entries: a full entry beats an "ex" entry; then the most specific one.
    broader = sorted([(c, ex) for c, ex in entries if len(c) < len(code) and code.startswith(c)],
                     key=lambda t: (t[1], -len(t[0])))
    if broader:
        c, ex = broader[0]
        return (1, f"Via {c} (ex: partial)") if ex else (2, f"Via {c}")
    narrower = [c for c, _ in entries if len(c) > len(code) and c.startswith(code)]
    if narrower:
        return 1, f"Partly: {len(narrower)} narrower line(s)"
    return 0, "Not listed"


def in_todays_cbam(code):
    if code.startswith("72"):
        return not any(code.startswith(e) for e in baseline_exceptions)
    return any(code.startswith(b) for b in baseline_in)


# ---- 2. The CN8 lines the EU traded in 2022-24 -------------------------------------------------------------
codes = set()
for path in sorted((RAW / "comext").glob("*.csv.gz")):
    t = pd.read_csv(path, dtype=str, usecols=["partner", "product", "flow", "TIME_PERIOD"])
    t = t[t["product"].str.fullmatch(r"\d{8}") & t.TIME_PERIOD.astype(int).isin(YEARS) & t.flow.isin(["1", "2"])
          & (t.partner.isin(["EXT_EU27_2020", "INT_EU27_2020"]) | (t.partner.str.len() == 2))]
    codes |= set(t["product"])

# ---- 3. Coverage of each line ------------------------------------------------------------------------------
rows = []
for code in sorted(codes):
    result = {p: cover(code, lists[p], exclusions[p]) for p in lists}
    if all(flag == 0 for flag, _ in result.values()):
        continue
    if in_todays_cbam(code) or code.startswith("72"):
        continue  # not a new downstream good
    rows.append({
        "cn8": code, "hs6": code[:6], "product_group": group_of(code),
        "commission": result["Commission"][0], "council": result["Council"][0], "parliament": result["Parliament"][0],
        "commission_basis": result["Commission"][1], "council_basis": result["Council"][1],
        "parliament_basis": result["Parliament"][1],
    })
cov = pd.DataFrame(rows)

# The chart colour: the first position that lists the line.
cov["first_listed_by"] = "Parliament"
cov.loc[cov.council > 0, "first_listed_by"] = "Council"
cov.loc[cov.commission > 0, "first_listed_by"] = "Commission"

INTERMEDIATE.mkdir(parents=True, exist_ok=True)
cov.to_csv(INTERMEDIATE / "01_cn8_legal_coverage.csv", index=False)

print(f"Traded CN8 codes: {len(codes):,}; downstream lines covered by at least one position: {len(cov)}")
print("Lines on each list:", {p: int((cov[p.lower()] > 0).sum()) for p in lists})
print("Lines by first position:", cov.first_listed_by.value_counts().to_dict())
