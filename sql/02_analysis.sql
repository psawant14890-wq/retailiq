-- RetailIQ SQL Analysis
-- Demonstrates: CTEs, window functions, joins across 6 tables, RFM segmentation

-- ============================================================
-- Q1: Monthly revenue trend with month-over-month growth (window function: LAG)
-- ============================================================
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
        SUM(oi.price + oi.freight_value) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY 1
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY month), 2) AS prev_month_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month), 1) AS mom_growth_pct
FROM monthly_revenue
ORDER BY month;

-- ============================================================
-- Q2: Top product categories by revenue, with rank (window function: RANK)
-- ============================================================
WITH category_revenue AS (
    SELECT
        COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
        SUM(oi.price) AS revenue,
        COUNT(DISTINCT oi.order_id) AS num_orders
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN product_category_translation t ON p.product_category_name = t.product_category_name
    GROUP BY 1
)
SELECT
    category,
    ROUND(revenue, 2) AS revenue,
    num_orders,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM category_revenue
ORDER BY revenue_rank
LIMIT 15;

-- ============================================================
-- Q3: RFM Customer Segmentation (Recency, Frequency, Monetary)
-- Uses CTEs + NTILE window function for scoring
-- ============================================================
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp) AS last_order_date,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.price + oi.freight_value) AS monetary
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
rfm_scores AS (
    SELECT
        customer_unique_id,
        last_order_date,
        frequency,
        monetary,
        (SELECT MAX(order_purchase_timestamp) FROM orders) - last_order_date AS recency_interval,
        NTILE(5) OVER (ORDER BY (SELECT MAX(order_purchase_timestamp) FROM orders) - last_order_date DESC) AS recency_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS monetary_score
    FROM customer_orders
)
SELECT
    customer_unique_id,
    EXTRACT(DAY FROM recency_interval) AS days_since_last_order,
    frequency,
    ROUND(monetary, 2) AS monetary_value,
    recency_score, frequency_score, monetary_score,
    (recency_score + frequency_score + monetary_score) AS rfm_total,
    CASE
        WHEN (recency_score + frequency_score + monetary_score) >= 13 THEN 'Champions'
        WHEN (recency_score + frequency_score + monetary_score) >= 10 THEN 'Loyal Customers'
        WHEN (recency_score + frequency_score + monetary_score) >= 7 THEN 'Potential Loyalists'
        WHEN (recency_score + frequency_score + monetary_score) >= 4 THEN 'At Risk'
        ELSE 'Lost'
    END AS segment
FROM rfm_scores
ORDER BY rfm_total DESC
LIMIT 20;

-- ============================================================
-- Q4: Delivery performance — % delivered late vs estimated date, by state
-- ============================================================
SELECT
    c.customer_state,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS late_orders,
    ROUND(100.0 * SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS late_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
HAVING COUNT(*) > 100
ORDER BY late_pct DESC;

-- ============================================================
-- Q5: Review score vs delivery delay (does late delivery hurt satisfaction?)
-- ============================================================
SELECT
    CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On time / early'
        WHEN o.order_delivered_customer_date - o.order_estimated_delivery_date <= INTERVAL '7 days' THEN 'Late by 1-7 days'
        ELSE 'Late by 7+ days'
    END AS delivery_bucket,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    COUNT(*) AS num_orders
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY 1
ORDER BY avg_review_score DESC;

-- ============================================================
-- Q6: Running cumulative revenue per year (window function: SUM OVER)
-- ============================================================
WITH daily_rev AS (
    SELECT
        DATE(o.order_purchase_timestamp) AS order_date,
        SUM(oi.price) AS daily_revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY 1
)
SELECT
    order_date,
    daily_revenue,
    SUM(daily_revenue) OVER (PARTITION BY DATE_TRUNC('year', order_date) ORDER BY order_date) AS ytd_cumulative_revenue
FROM daily_rev
ORDER BY order_date;
