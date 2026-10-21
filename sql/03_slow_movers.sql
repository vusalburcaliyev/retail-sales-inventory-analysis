-- Latest available snapshot (2025-12-28); recent demand covers 28 days inclusive.
-- Slow means under 0.5 unit/day and at least 50 units on hand.
WITH latest AS (SELECT MAX(snapshot_date) AS snapshot_date FROM inventory_snapshots),
recent AS (
    SELECT store_id, product_id, SUM(quantity) AS units_28d
    FROM sales
    WHERE sale_date > date((SELECT snapshot_date FROM latest), '-28 days')
      AND sale_date <= (SELECT snapshot_date FROM latest)
    GROUP BY store_id, product_id
)
SELECT i.snapshot_date, st.store_name AS store, p.product_id, p.product_name,
       p.category, i.units_on_hand, COALESCE(r.units_28d, 0) AS units_28d,
       ROUND(COALESCE(r.units_28d, 0) / 28.0, 2) AS units_per_day,
       CASE WHEN COALESCE(r.units_28d, 0) = 0 THEN NULL
            ELSE ROUND(28.0 * i.units_on_hand / r.units_28d, 1) END AS days_of_supply
FROM inventory_snapshots AS i
JOIN latest ON i.snapshot_date = latest.snapshot_date
JOIN stores AS st ON st.store_id = i.store_id
JOIN products AS p ON p.product_id = i.product_id
LEFT JOIN recent AS r ON r.store_id = i.store_id AND r.product_id = i.product_id
WHERE COALESCE(r.units_28d, 0) / 28.0 < 0.5 AND i.units_on_hand >= 50
ORDER BY i.units_on_hand DESC, units_28d ASC;
