-- Illustration: top quartile by 2025 units and margin under 15%.
-- The quartile cutoff is calculated from product unit totals, not hard-coded.
WITH product_sales AS (
    SELECT p.product_id, p.product_name, p.category,
           SUM(s.quantity) AS units_sold,
           SUM(s.quantity * s.unit_price) AS revenue,
           SUM(s.quantity * (s.unit_price - s.unit_cost)) AS gross_profit
    FROM products AS p JOIN sales AS s ON s.product_id = p.product_id
    GROUP BY p.product_id
), ranked AS (
    SELECT *, NTILE(4) OVER (ORDER BY units_sold DESC) AS sales_quartile
    FROM product_sales
)
SELECT product_id, product_name, category, units_sold,
       ROUND(revenue, 2) AS revenue,
       ROUND(gross_profit, 2) AS gross_profit,
       ROUND(100.0 * gross_profit / NULLIF(revenue, 0), 2) AS gross_margin_pct
FROM ranked
WHERE sales_quartile = 1 AND gross_profit / NULLIF(revenue, 0) < 0.15
ORDER BY units_sold DESC;
