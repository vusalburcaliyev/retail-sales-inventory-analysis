-- Assumptions: 28-day trailing average, 14-day lead time,
-- 7-day review period, 7-day safety stock in demand-days.
-- Reorder point = ceil(daily demand * 28 days). Zero demand is not flagged.
WITH latest AS (SELECT MAX(snapshot_date) AS snapshot_date FROM inventory_snapshots),
recent AS (
    SELECT store_id, product_id, SUM(quantity) AS units_28d
    FROM sales
    WHERE sale_date > date((SELECT snapshot_date FROM latest), '-28 days')
      AND sale_date <= (SELECT snapshot_date FROM latest)
    GROUP BY store_id, product_id
), base AS (
    SELECT i.snapshot_date, st.store_name AS store, p.product_id, p.product_name,
           p.category, i.units_on_hand, COALESCE(r.units_28d, 0) AS units_28d,
           COALESCE(r.units_28d, 0) / 28.0 AS daily_demand
    FROM inventory_snapshots AS i
    JOIN latest ON i.snapshot_date = latest.snapshot_date
    JOIN stores AS st ON st.store_id = i.store_id
    JOIN products AS p ON p.product_id = i.product_id
    LEFT JOIN recent AS r ON r.store_id = i.store_id AND r.product_id = i.product_id
)
SELECT snapshot_date, store, product_id, product_name, category,
       units_on_hand, units_28d, ROUND(daily_demand, 2) AS units_per_day,
       CAST(daily_demand * 28 + 0.999999 AS INTEGER) AS reorder_point,
       CAST(daily_demand * 28 + 0.999999 AS INTEGER) - units_on_hand AS shortfall_units
FROM base
WHERE daily_demand > 0
  AND units_on_hand < CAST(daily_demand * 28 + 0.999999 AS INTEGER)
ORDER BY shortfall_units DESC, store, product_id;
