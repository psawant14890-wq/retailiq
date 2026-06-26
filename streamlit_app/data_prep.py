"""
RetailIQ Streamlit App — Data Preparation
Pre-aggregates the Postgres data into small CSVs the deployed app can bundle
and load instantly, instead of shipping raw 100K-row tables to a live app
that only ever displays aggregates anyway.
"""
import pandas as pd
import numpy as np
import psycopg2
import json

conn = psycopg2.connect(host="localhost", dbname="retailiq", user="postgres", password="postgres")
OUT = "/home/claude/retailiq/streamlit_app/data"

# 1. KPI summary
kpi = pd.read_sql("""
SELECT
    (SELECT ROUND(SUM(price + freight_value), 2) FROM order_items) AS total_revenue,
    (SELECT ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 1)
     FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL) AS late_delivery_rate_pct,
    (SELECT ROUND(AVG(review_score), 2) FROM order_reviews) AS avg_review_score
""", conn)
late7 = pd.read_sql("""
SELECT ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue_at_risk
FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_delivered_customer_date - o.order_estimated_delivery_date > INTERVAL '7 days'
""", conn)
kpi["revenue_at_risk"] = late7["revenue_at_risk"]
kpi.to_csv(f"{OUT}/kpi_summary.csv", index=False)
print("Saved kpi_summary.csv:", kpi.to_dict("records"))

# 2. Monthly revenue trend (clean date range, matches forecast model)
monthly = pd.read_sql("""
SELECT TO_CHAR(DATE_TRUNC('month', o.order_purchase_timestamp), 'YYYY-MM') AS year_month,
       ROUND(SUM(oi.price + oi.freight_value), 2) AS revenue
FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
  AND o.order_purchase_timestamp BETWEEN '2017-01-01' AND '2018-08-19'
GROUP BY 1 ORDER BY 1
""", conn)
monthly.to_csv(f"{OUT}/monthly_revenue.csv", index=False)
print(f"Saved monthly_revenue.csv: {len(monthly)} rows")

# 3. Top 10 categories by revenue
categories = pd.read_sql("""
SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
       ROUND(SUM(oi.price), 2) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_translation t ON p.product_category_name = t.product_category_name
GROUP BY 1 ORDER BY revenue DESC LIMIT 10
""", conn)
categories.to_csv(f"{OUT}/top_categories.csv", index=False)
print(f"Saved top_categories.csv: {len(categories)} rows")

# 4. Late delivery rate by state (top 10 worst)
states = pd.read_sql("""
SELECT c.customer_state,
    ROUND(100.0 * SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS late_pct,
    COUNT(*) AS total_orders
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state HAVING COUNT(*) > 100
ORDER BY late_pct DESC LIMIT 10
""", conn)
states.to_csv(f"{OUT}/state_late_delivery.csv", index=False)
print(f"Saved state_late_delivery.csv: {len(states)} rows")

# 5. Review score by delivery bucket
delivery_satisfaction = pd.read_sql("""
SELECT
    CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On Time / Early'
        WHEN o.order_delivered_customer_date - o.order_estimated_delivery_date <= INTERVAL '7 days' THEN 'Late 1-7 Days'
        ELSE 'Late 7+ Days'
    END AS delivery_bucket,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    COUNT(*) AS num_orders
FROM orders o JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY 1
""", conn)
order_map = {"On Time / Early": 0, "Late 1-7 Days": 1, "Late 7+ Days": 2}
delivery_satisfaction["sort_key"] = delivery_satisfaction["delivery_bucket"].map(order_map)
delivery_satisfaction = delivery_satisfaction.sort_values("sort_key").drop(columns="sort_key")
delivery_satisfaction.to_csv(f"{OUT}/delivery_satisfaction.csv", index=False)
print(f"Saved delivery_satisfaction.csv: {len(delivery_satisfaction)} rows")

# 6. RFM segmentation — full customer-level, then segment summary + top 20
rfm_raw = pd.read_sql("""
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
""", conn)
conn.close()

max_date = rfm_raw["last_order_date"].max()
rfm_raw["recency_days"] = (max_date - rfm_raw["last_order_date"]).dt.days

# Use rank-based scoring on ROW position (not dense rank) to avoid the same
# compression bug we hit in the Power BI DAX version — pandas qcut with
# duplicates='drop' handles the heavy ties in frequency cleanly here.
rfm_raw["recency_score"] = pd.qcut(rfm_raw["recency_days"].rank(method="first", ascending=False), 5, labels=[1,2,3,4,5]).astype(int)
rfm_raw["frequency_score"] = pd.qcut(rfm_raw["frequency"].rank(method="first", ascending=True), 5, labels=[1,2,3,4,5]).astype(int)
rfm_raw["monetary_score"] = pd.qcut(rfm_raw["monetary"].rank(method="first", ascending=True), 5, labels=[1,2,3,4,5]).astype(int)
rfm_raw["rfm_total"] = rfm_raw["recency_score"] + rfm_raw["frequency_score"] + rfm_raw["monetary_score"]

def segment(total):
    if total >= 13: return "Champions"
    elif total >= 10: return "Loyal Customers"
    elif total >= 7: return "Potential Loyalists"
    elif total >= 4: return "At Risk"
    else: return "Lost"

rfm_raw["segment"] = rfm_raw["rfm_total"].apply(segment)

print(f"\nRFM_Total distribution:\n{rfm_raw['rfm_total'].value_counts().sort_index()}")
print(f"\nSegment counts:\n{rfm_raw['segment'].value_counts()}")

segment_counts = rfm_raw["segment"].value_counts().reset_index()
segment_counts.columns = ["segment", "count"]
segment_order = ["Champions", "Loyal Customers", "Potential Loyalists", "At Risk", "Lost"]
segment_counts["sort_key"] = segment_counts["segment"].map({s: i for i, s in enumerate(segment_order)})
segment_counts = segment_counts.sort_values("sort_key").drop(columns="sort_key")
segment_counts.to_csv(f"{OUT}/segment_counts.csv", index=False)
print(f"\nSaved segment_counts.csv")

top20 = rfm_raw.sort_values("rfm_total", ascending=False).head(20)[
    ["customer_unique_id", "monetary", "frequency", "recency_days", "rfm_total", "segment"]
].round(2)
top20.to_csv(f"{OUT}/top20_customers.csv", index=False)
print(f"Saved top20_customers.csv")

print("\nAll data prep files saved successfully.")
