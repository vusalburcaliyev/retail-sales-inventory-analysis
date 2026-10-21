# Raw data and preparation rules

`data/raw/` contains the four original generated CSVs. The generator uses fixed seed `20251021` and adds deliberate errors. `prepare` reads but does not edit them, creates a new SQLite database, and writes counts to `outputs/quality_report.csv`.

| Deliberate issue | Rule | Rows affected in supplied raw files |
|---|---|---:|
| Category capitalization / whitespace | Trim and normalize to the five known category labels | 2 corrected |
| Duplicate sale ID | Keep first row, exclude later duplicate | 1 excluded |
| Negative quantity, blank price, invalid date | Exclude invalid sales values; do not impute | 3 excluded |
| Sale referencing unknown product | Exclude and report | 1 excluded |
| Duplicate inventory snapshot key | Keep first row, exclude later duplicate | 1 excluded |
| Negative stock balance | Exclude and report | 1 excluded |

Thus 12,664 raw sale lines yield 12,659 accepted lines; 9,362 raw inventory rows yield 9,360 accepted snapshots. The cleaned tables enforce primary keys, foreign keys, and nonnegative / positive numerical constraints. Real projects would also investigate source systems and business owners before deciding whether to exclude or repair records.
