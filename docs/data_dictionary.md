# Data dictionary

All values are synthetic. Grain means what one row represents.

| Table / CSV | Grain | Fields |
|---|---|---|
| `stores` | One store | `store_id` (primary key), `store_name`, `region` |
| `products` | One product | `product_id` (primary key), `product_name`, `category`, `list_cost` (synthetic reference cost) |
| `sales` | One sale line | `sale_id` (primary key), `sale_date` (ISO date), `store_id`, `product_id`, `quantity` (units), `unit_price` (per unit), `unit_cost` (historical cost per unit) |
| `inventory_snapshots` | One store-product-date balance | `snapshot_date` (ISO date), `store_id`, `product_id`, `units_on_hand` (nonnegative units) |

`store_id` and `product_id` in fact tables reference the corresponding dimension tables. The sales `unit_cost` is kept on each line so historical gross profit does not change if a product reference cost changes later.

## Metric definitions

| Metric | Definition |
|---|---|
| Revenue | `SUM(quantity * unit_price)` over accepted sales. Currency units are generic. |
| Cost of goods sold | `SUM(quantity * unit_cost)` over accepted sales. |
| Gross profit | Revenue minus cost of goods sold; excludes operating expenses. |
| Gross margin % | `100 * gross_profit / revenue`, calculated after aggregation. |
| 28-day demand | Units sold after snapshot date minus 28 days through the snapshot date, inclusive of the snapshot date. |
| Daily demand | 28-day demand divided by 28. |
| Days of supply | `units_on_hand / daily_demand`; blank when recent demand is zero. |
| Reorder point | Ceiling of daily demand times 28 assumed cover days. |
| Shortfall | Reorder point minus units on hand for flagged rows. |

The latest weekly snapshot is 2025-12-28. Inventory is a **stock** measured at a point in time; do not sum weekly snapshots as if they were sales flows.
