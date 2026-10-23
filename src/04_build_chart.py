"""Step 4: build the interactive chart from the final dataset.

Reads   data/final/cbam_downstream_products.csv   (one row per circle on the chart)
        chart/template.html                         (the page: layout, styles, drawing code)
Writes  docs/index.html                             (the finished, self-contained page)

The page needs the data as a compact JavaScript array with short field names.
This script does that translation and pastes the array into the template
where it says __DATA__. Nothing is computed here: every number on the chart
comes straight from the CSV.

Run from the repository root:  python src/04_build_chart.py
"""
import csv
import json

from config import ROOT

FINAL = ROOT / "data" / "final" / "cbam_downstream_products.csv"
TEMPLATE = ROOT / "chart" / "template.html"
OUTPUT = ROOT / "docs" / "index.html"

# Short codes the page's JavaScript expects for the position that first lists a product.
POSITION_CODE = {"Commission": "com", "Council": "cnl", "Parliament": "ep"}


def number(text):
    """CSV text to a float, or None (null on the page) when the cell is empty."""
    return None if text == "" else float(text)


def to_page_record(row):
    """One CSV row to one chart record. Key order matters: it fixes the output byte for byte."""
    return {
        "c": row["hs6"],                                   # HS6 code
        "n": row["product"],                               # product description
        "g": row["product_group"],                         # display group
        "k": POSITION_CODE[row["first_listed_by"]],        # colour of the circle
        "m": float(row["imports_eur_m"]),                  # circle size: extra-EU imports, EUR m
        "s": number(row["main_supplier_share"]),           # filled circle if > 50%
        "p": row["main_supplier"],
        "ch": number(row["cbam_charge"]),                  # y-axis: CBAM charge, share of price
        "cn": number(row["china_share"]),
        "ip": number(row["import_share_consumption"]),
        "tc": number(row["main_supplier_share_consumption"]),
        "su": number(row["import_share_eu_market"]),       # x-axis: imports' share of EU market
        "ts": number(row["main_supplier_share_market"]),
        "xp": number(row["exports_over_production"]),
        "pos": [int(row["on_commission"]), int(row["on_council"]), int(row["on_parliament"])],
        "l": int(row["cn8_lines"]),                        # number of 8-digit tariff lines
    }


def main():
    with open(FINAL, newline="", encoding="utf-8") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: int(r["map_order"]))
    records = [to_page_record(r) for r in rows]

    data_js = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    page = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", data_js)

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(records)} products")


if __name__ == "__main__":
    main()
