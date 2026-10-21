"""Generate, prepare, analyze and chart a clearly synthetic retail dataset."""
from __future__ import annotations

import argparse
import csv
import random
import sqlite3
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "retail.sqlite"
OUT = ROOT / "outputs"
START = date(2025, 1, 1)
END = date(2025, 12, 31)


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def generate():
    if any(RAW.glob("*.csv")):
        raise SystemExit("Raw CSVs already exist. Move them aside explicitly before regenerating.")
    rng = random.Random(20251021)
    stores = [
        {"store_id": "S01", "store_name": "Harbor", "region": "North"},
        {"store_id": "S02", "store_name": "Market", "region": "Central"},
        {"store_id": "S03", "store_name": "Park", "region": "South"},
    ]
    categories = ["Grocery", "Household", "Beauty", "Electronics", "Apparel"]
    products = []
    for c, category in enumerate(categories):
        for n in range(1, 13):
            pid = f"P{c * 12 + n:03d}"
            cost = round((3 + c * 6 + (n % 6) * 2) * (1 + rng.random() * .2), 2)
            products.append({"product_id": pid, "product_name": f"{category} item {n:02d}",
                             "category": category, "list_cost": f"{cost:.2f}"})
    sales = []
    tx = 1
    day = START
    while day <= END:
        for store in stores:
            for _ in range(rng.randint(8, 15)):
                product = rng.choice(products)
                cost = float(product["list_cost"])
                # Every eleventh item has intentionally tight pricing.
                multiplier = 1.09 if int(product["product_id"][1:]) % 11 == 0 else rng.uniform(1.25, 1.85)
                qty = rng.choices([1, 2, 3, 4], [65, 25, 8, 2])[0]
                sales.append({"sale_id": f"T{tx:06d}", "sale_date": day.isoformat(),
                              "store_id": store["store_id"], "product_id": product["product_id"],
                              "quantity": str(qty), "unit_price": f"{cost * multiplier:.2f}",
                              "unit_cost": f"{cost:.2f}"})
                tx += 1
        day += timedelta(days=1)
    # Deliberate issues; keep raw files unchanged after generation.
    sales += [dict(sales[40]),
              dict(sales[80], sale_id="T_BAD_QTY", quantity="-2"),
              dict(sales[120], sale_id="T_BAD_PRICE", unit_price=""),
              dict(sales[160], sale_id="T_BAD_PRODUCT", product_id="P999"),
              dict(sales[200], sale_id="T_BAD_DATE", sale_date="2025-13-01")]
    products[4]["category"] = " grocery "
    products[18]["category"] = "household"
    snapshots = []
    snap = START + timedelta(days=(6 - START.weekday()) % 7)
    while snap <= END:
        for store in stores:
            for product in products:
                pid = int(product["product_id"][1:])
                base = 12 + (pid * 7 + int(store["store_id"][1:]) * 9) % 55
                if pid % 13 == 0:
                    base += 95  # deliberate slow-moving stock scenario
                if pid % 17 == 0 and snap.month == 12:
                    base = 2  # deliberate replenishment scenario
                snapshots.append({"snapshot_date": snap.isoformat(), "store_id": store["store_id"],
                                  "product_id": product["product_id"], "units_on_hand": str(base)})
        snap += timedelta(days=7)
    snapshots += [dict(snapshots[12]),
                  dict(snapshots[22], snapshot_date="2025-12-30", units_on_hand="-3")]
    write_csv(RAW / "stores.csv", stores[0].keys(), stores)
    write_csv(RAW / "products.csv", products[0].keys(), products)
    write_csv(RAW / "sales.csv", sales[0].keys(), sales)
    write_csv(RAW / "inventory_snapshots.csv", snapshots[0].keys(), snapshots)
    print(f"Generated synthetic raw data: {len(sales)} sales rows, {len(snapshots)} inventory rows.")


def prepare():
    if not all((RAW / f).exists() for f in ("stores.csv", "products.csv", "sales.csv", "inventory_snapshots.csv")):
        raise SystemExit("Raw CSVs missing. Run: python src/project.py generate")
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
    issues = Counter()
    stores = read_csv(RAW / "stores.csv")
    products = read_csv(RAW / "products.csv")
    categories = {x.casefold(): x for x in ("Grocery", "Household", "Beauty", "Electronics", "Apparel")}
    for row in stores:
        con.execute("INSERT INTO stores VALUES (?, ?, ?)", tuple(row[k].strip() for k in ("store_id", "store_name", "region")))
    for row in products:
        raw_category = row["category"]
        category = categories.get(raw_category.strip().casefold())
        if category is None:
            raise ValueError(f"Unknown category: {raw_category}")
        if raw_category != category:
            issues["category_normalized"] += 1
        con.execute("INSERT INTO products VALUES (?, ?, ?, ?)",
                    (row["product_id"], row["product_name"], category, float(row["list_cost"])))
    valid_stores = {r[0] for r in con.execute("SELECT store_id FROM stores")}
    valid_products = {r[0] for r in con.execute("SELECT product_id FROM products")}
    seen_sales = set()
    for row in read_csv(RAW / "sales.csv"):
        if row["sale_id"] in seen_sales:
            issues["duplicate_sale_id_excluded"] += 1
            continue
        seen_sales.add(row["sale_id"])
        try:
            sale_date = date.fromisoformat(row["sale_date"])
            qty = int(row["quantity"])
            price = float(row["unit_price"])
            cost = float(row["unit_cost"])
        except ValueError:
            issues["invalid_sales_value_excluded"] += 1
            continue
        if not START <= sale_date <= END or qty <= 0 or price <= 0 or cost < 0:
            issues["invalid_sales_value_excluded"] += 1
            continue
        if row["store_id"] not in valid_stores or row["product_id"] not in valid_products:
            issues["unknown_sales_key_excluded"] += 1
            continue
        con.execute("INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row["sale_id"], row["sale_date"], row["store_id"], row["product_id"], qty, price, cost))
    seen_snapshots = set()
    for row in read_csv(RAW / "inventory_snapshots.csv"):
        key = (row["snapshot_date"], row["store_id"], row["product_id"])
        if key in seen_snapshots:
            issues["duplicate_snapshot_excluded"] += 1
            continue
        seen_snapshots.add(key)
        try:
            snap_date = date.fromisoformat(row["snapshot_date"])
            units = int(row["units_on_hand"])
        except ValueError:
            issues["invalid_snapshot_excluded"] += 1
            continue
        if not START <= snap_date <= END or units < 0 or key[1] not in valid_stores or key[2] not in valid_products:
            issues["invalid_snapshot_excluded"] += 1
            continue
        con.execute("INSERT INTO inventory_snapshots VALUES (?, ?, ?, ?)", (*key, units))
    con.commit()
    OUT.mkdir(exist_ok=True)
    with (OUT / "quality_report.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["issue", "count"])
        writer.writerows(sorted(issues.items()))
    print("Prepared SQLite database. Data quality actions:", dict(sorted(issues.items())))
    con.close()


def query(con, filename):
    return con.execute((ROOT / "sql" / filename).read_text(encoding="utf-8")).fetchall()


def export_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(rows[0].keys())
        writer.writerows(tuple(row) for row in rows)


def bar_chart(path, title, labels, values, unit):
    width, height = 960, 480
    left, right, top, bottom = 90, 30, 75, 100
    max_value = max(values) * 1.12 if values else 1
    plot_w, plot_h = width - left - right, height - top - bottom
    step = plot_w / max(len(values), 1)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             f'<text x="{left}" y="38" font-size="23" font-family="Arial" fill="#1a2a44">{escape(title)}</text>',
             f'<text x="{left}" y="61" font-size="13" font-family="Arial" fill="#526277">Synthetic retail data · {escape(unit)}</text>',
             f'<line x1="{left}" y1="{top+plot_h}" x2="{width-right}" y2="{top+plot_h}" stroke="#9aa8b7"/>']
    for i, (label, value) in enumerate(zip(labels, values)):
        x = left + i * step + step * .15
        bar_w = step * .7
        bar_h = max(0, value / max_value * plot_h)
        y = top + plot_h - bar_h
        parts += [f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="#287c9f"/>',
                  f'<text x="{x + bar_w/2:.1f}" y="{y-7:.1f}" text-anchor="middle" font-size="11" font-family="Arial">{value:,.0f}</text>',
                  f'<text x="{x + bar_w/2:.1f}" y="{top+plot_h+21}" text-anchor="middle" font-size="11" font-family="Arial">{escape(str(label))}</text>']
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def analyze():
    if not DB.exists():
        raise SystemExit("Database missing. Run: python src/project.py prepare")
    OUT.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    results = {}
    for name in ("01_monthly_store_category.sql", "02_high_sales_low_margin.sql",
                 "03_slow_movers.sql", "04_replenishment.sql"):
        rows = query(con, name)
        export_csv(OUT / name.replace(".sql", ".csv"), rows)
        results[name] = rows
    monthly = results["01_monthly_store_category.sql"]
    by_month = {}
    for row in monthly:
        item = by_month.setdefault(row["month"], [0, 0])
        item[0] += row["revenue"]
        item[1] += row["gross_profit"]
    bar_chart(OUT / "monthly_revenue.svg", "Monthly revenue", list(by_month),
              [v[0] for v in by_month.values()], "currency units")
    by_category = {}
    for row in monthly:
        by_category[row["category"]] = by_category.get(row["category"], 0) + row["gross_profit"]
    bar_chart(OUT / "category_gross_profit.svg", "Gross profit by category", list(by_category),
              list(by_category.values()), "currency units")
    print("Analysis exported to outputs/.")
    print("Total revenue:", round(sum(v[0] for v in by_month.values()), 2))
    print("Total gross profit:", round(sum(v[1] for v in by_month.values()), 2))
    print("Low-margin high-sales rows:", len(results["02_high_sales_low_margin.sql"]))
    print("Slow-moving rows:", len(results["03_slow_movers.sql"]))
    print("Replenishment rows:", len(results["04_replenishment.sql"]))
    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "prepare", "analyze", "all"))
    args = parser.parse_args()
    if args.command in ("generate", "all"):
        generate()
    if args.command in ("prepare", "all"):
        prepare()
    if args.command in ("analyze", "all"):
        analyze()
