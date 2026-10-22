-- 1. Overall conversion / net revenue by assigned variant.
-- SQLite syntax. Purchase refunds remove the entire order value.
SELECT
    variant,
    COUNT(*) AS assigned_users,
    SUM(converted) AS purchases,
    ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_pct,
    ROUND(1.0 * SUM(order_value_rub * (1 - refunded)) / COUNT(*), 2) AS net_revenue_per_user_rub,
    ROUND(1.0 * SUM(refunded) / NULLIF(SUM(converted), 0) * 100, 2) AS refunds_per_purchase_pct
FROM experiment_users
GROUP BY variant
ORDER BY variant;

-- 2. Exploratory device breakdown; no unadjusted significance tests.
SELECT
    variant,
    device,
    COUNT(*) AS users,
    SUM(converted) AS purchases,
    ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_pct
FROM experiment_users
GROUP BY variant, device
ORDER BY device, variant;

-- 3. Explore daily assignment counts to catch unexpected drops.
SELECT
    assigned_at,
    variant,
    COUNT(*) AS assigned_users
FROM experiment_users
GROUP BY assigned_at, variant
ORDER BY assigned_at, variant;
