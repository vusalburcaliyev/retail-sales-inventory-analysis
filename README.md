# Retail Sales & Inventory Analysis

**Portfolio project using synthetic data.** This local, reproducible example uses Python to generate and prepare data, SQLite SQL to answer business questions, and Python to produce SVG charts. Its figures do not describe a real retailer. The dataset has three stores, 60 products, five categories, daily 2025 sales, and weekly inventory snapshots.

## Business problem and dataset source

A retail analyst needs to understand where sales and gross profit come from, spot products with weak margins or slow movement, and prioritize stock checks. This project demonstrates that workflow with **original synthetic data generated locally by `src/project.py`**. The data was not downloaded from a retailer or public website, and no customer, employee, or employer records are included. The generator uses a fixed random seed and deliberately adds documented quality issues to the preserved raw CSVs.

## Questions and outputs

1. How do revenue and gross profit vary by month, store, and category? See `sql/01_monthly_store_category.sql` and the two SVG charts.
2. Which products have high sales but low margins? See `sql/02_high_sales_low_margin.sql`.
3. Which products sell slowly relative to inventory? See `sql/03_slow_movers.sql`.
4. Which products may need replenishment under stated assumptions? See `sql/04_replenishment.sql`.

The [findings report](reports/findings.md) separates observations, assumptions, and possible actions. The [data dictionary](docs/data_dictionary.md) defines all fields and metrics. [Data quality notes](docs/data_quality.md) explain each deliberate raw-data issue and cleaning rule.

## Windows setup and reproduction

Install Python 3.10 or newer and Git on Windows. Open this folder in VS Code or PyCharm, open a **PowerShell** terminal in the project folder, and run:

```powershell
python --version
python src/project.py prepare
python src/project.py analyze
python -m unittest discover -s tests -v
```

The four original synthetic CSVs are included in `data/raw/`, so `generate` is **not needed** for normal use. The `prepare` command rebuilds `data/retail.sqlite` from those files. `analyze` writes query results, the quality report, and two SVG charts to `outputs/`. SQLite is bundled with Python; no separate SQLite installation is needed. The requirements file records that there are no third-party packages.

To inspect a query without a separate SQLite app, use Python in the same terminal:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/retail.sqlite'); print(c.execute('select count(*) from sales').fetchone())"
```

To generate a fresh copy of the exact synthetic raw data, move the existing `data/raw/*.csv` files to a backup folder yourself, then run `python src/project.py generate`. The generator refuses to overwrite raw files. Its fixed seed makes the output reproducible.

## Workflow

`data/raw/*.csv` → `src/project.py prepare` → `data/retail.sqlite` → `sql/*.sql` → `src/project.py analyze` → `outputs/*` → `reports/findings.md`.

The raw files and a reviewed copy of the query and chart outputs are intended to be tracked so the report renders on GitHub. The database is generated locally and ignored by Git. Running the analysis requires no account access.

## Interview practice

1. **Data preparation:** Find a rejected sales row in `data/raw/sales.csv`. Explain why the rule in `src/project.py` excludes it rather than guessing a replacement value.
2. **SQL metrics:** Change the monthly query to report only one store. Explain why gross margin is calculated from summed revenue and profit, rather than averaging line margins.
3. **Inventory:** Change the replenishment lead time from 14 to 21 days, update the cover period in SQL, and explain why more items may be flagged.
4. **Validation:** Reconcile the SQL monthly revenue total to a direct sum over `sales`, then describe the small rounding tolerance in `tests/test_analysis.py`.

## Limitations

Synthetic prices, demand, and snapshots are generated examples. Snapshots are not derived from a full purchasing and stock movement ledger, so the project cannot explain stock changes or establish actual availability at the time of each sale. There are no returns, taxes, discounts, supplier minimums, or real lead-time variation. Replenishment flags are illustrative and should not be treated as purchase orders.
