import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
import json

sns.set_style("whitegrid")
conn = psycopg2.connect(host="localhost", dbname="retailiq", user="postgres", password="postgres")

fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# 1. Monthly revenue trend
q1 = """
SELECT DATE_TRUNC('month', o.order_purchase_timestamp) AS month, SUM(oi.price + oi.freight_value) AS revenue
FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
  AND o.order_purchase_timestamp BETWEEN '2017-01-01' AND '2018-08-19'
GROUP BY 1 ORDER BY 1
"""
df1 = pd.read_sql(q1, conn)
axes[0,0].plot(df1["month"], df1["revenue"]/1000, marker="o", color="#4C72B0", linewidth=2)
axes[0,0].set_title("Monthly Revenue Trend (R$ thousands)")
axes[0,0].set_ylabel("Revenue (R$k)")
axes[0,0].tick_params(axis='x', rotation=45)

# 2. Top 10 categories by revenue
q2 = """
SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category, SUM(oi.price) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_translation t ON p.product_category_name = t.product_category_name
GROUP BY 1 ORDER BY revenue DESC LIMIT 10
"""
df2 = pd.read_sql(q2, conn).sort_values("revenue")
axes[0,1].barh(df2["category"], df2["revenue"]/1000, color="#55A868")
axes[0,1].set_title("Top 10 Categories by Revenue (R$ thousands)")
axes[0,1].set_xlabel("Revenue (R$k)")

# 3. Delivery performance by state (top 10 worst)
q3 = """
SELECT c.customer_state,
    ROUND(100.0 * SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS late_pct
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state HAVING COUNT(*) > 100
ORDER BY late_pct DESC LIMIT 10
"""
df3 = pd.read_sql(q3, conn).sort_values("late_pct")
axes[1,0].barh(df3["customer_state"], df3["late_pct"], color="#C44E52")
axes[1,0].set_title("Top 10 States by Late Delivery Rate")
axes[1,0].set_xlabel("Late Delivery Rate (%)")

# 4. Review score by delivery bucket
q4 = """
SELECT
    CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On time /\nearly'
        WHEN o.order_delivered_customer_date - o.order_estimated_delivery_date <= INTERVAL '7 days' THEN 'Late\n1-7 days'
        ELSE 'Late\n7+ days'
    END AS delivery_bucket,
    AVG(r.review_score) AS avg_review_score
FROM orders o JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
GROUP BY 1
"""
df4 = pd.read_sql(q4, conn)
order_map = {"On time /\nearly": 0, "Late\n1-7 days": 1, "Late\n7+ days": 2}
df4["sort_key"] = df4["delivery_bucket"].map(order_map)
df4 = df4.sort_values("sort_key")
colors = ["#55A868", "#DD8452", "#C44E52"]
axes[1,1].bar(df4["delivery_bucket"], df4["avg_review_score"], color=colors)
axes[1,1].set_title("Avg Review Score by Delivery Performance")
axes[1,1].set_ylabel("Avg Review Score (1-5)")
axes[1,1].set_ylim(0, 5)
for i, v in enumerate(df4["avg_review_score"]):
    axes[1,1].text(i, v + 0.1, f"{v:.2f}", ha="center", fontweight="bold")

plt.tight_layout()
plt.savefig("/home/claude/retailiq/retailiq_dashboard_preview.png", dpi=150)
print("Saved retailiq_dashboard_preview.png")
conn.close()
