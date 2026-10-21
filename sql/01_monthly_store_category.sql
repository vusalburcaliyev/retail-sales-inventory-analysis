-- Valid sales only. Gross profit excludes all operating expenses.
SELECT strftime('%Y-%m', s.sale_date) AS month,
       st.store_name AS store,
       p.category,
       SUM(s.quantity) AS units_sold,
       ROUND(SUM(s.quantity * s.unit_price), 2) AS revenue,
       ROUND(SUM(s.quantity * (s.unit_price - s.unit_cost)), 2) AS gross_profit,
       ROUND(100.0 * SUM(s.quantity * (s.unit_price - s.unit_cost))
             / NULLIF(SUM(s.quantity * s.unit_price), 0), 2) AS gross_margin_pct
FROM sales AS s
JOIN stores AS st ON st.store_id = s.store_id
JOIN products AS p ON p.product_id = s.product_id
GROUP BY month, st.store_id, p.category
ORDER BY month, st.store_id, p.category;
