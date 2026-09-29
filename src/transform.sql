-- Category Benchmark View: Computes category-level statistics and pricing spreads
CREATE OR REPLACE VIEW v_category_pricing_intelligence AS
WITH category_aggregates AS (
    SELECT
        category,
        COUNT(id) AS total_skus,
        ROUND(AVG(price), 2) AS category_avg_msrp,
        ROUND(AVG(effective_price), 2) AS category_avg_selling_price,
        ROUND(AVG(discountPercentage), 2) AS category_avg_discount_pct,
        SUM(inventory_value) AS category_total_stock_value
    FROM raw_products
    GROUP BY category
),
ranked_skus AS (
    SELECT
        p.id,
        p.title,
        p.category,
        p.brand,
        p.price AS msrp,
        p.discountPercentage AS discount_pct,
        p.effective_price,
        p.stock,
        p.rating,
        p.inventory_value,
        c.category_avg_selling_price,
        c.category_avg_discount_pct,
        ROUND(p.effective_price - c.category_avg_selling_price, 2) AS price_delta_vs_category_mean,
        DENSE_RANK() OVER (
            PARTITION BY p.category 
            ORDER BY p.discountPercentage DESC
        ) AS category_discount_rank,
        -- Commercial Risk Flags
        CASE 
            WHEN p.stock < 10 THEN 'Critical Stockout Risk'
            WHEN p.discountPercentage > 20 AND p.rating < 3.5 THEN 'Margin Drain (Low Quality / High Markdown)'
            WHEN p.stock > 100 AND p.discountPercentage < 5 THEN 'Overstocked / Stagnant'
            ELSE 'Healthy'
        END AS inventory_health_status
    FROM raw_products p
    JOIN category_aggregates c ON p.category = c.category
)
SELECT * FROM ranked_skus;