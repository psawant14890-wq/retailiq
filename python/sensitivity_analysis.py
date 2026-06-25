"""
RetailIQ — Sensitivity Analysis
"If the late-delivery rate in our 4 target states changes by X, how much
revenue moves out of the high-risk (1.73 avg review score) bucket?"

This is the MBB-style "what if assumption X changes" scenario analysis —
real numbers, not hand-waving.
"""
import pandas as pd
import psycopg2
import json

conn = psycopg2.connect(host="localhost", dbname="retailiq", user="postgres", password="postgres")

query = """
SELECT
    c.customer_state,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS late_orders,
    SUM(oi.price + oi.freight_value) AS total_revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
  AND c.customer_state IN ('AL','MA','PI','CE')
GROUP BY c.customer_state
"""
df = pd.read_sql(query, conn)
conn.close()

df["current_late_pct"] = df["late_orders"] / df["total_orders"] * 100
df["avg_order_value"] = df["total_revenue"] / df["total_orders"]

NATIONAL_AVG_LATE_PCT = 8.11
BEST_STATE_LATE_PCT = 2.9  # Roraima (RO), the best-performing state nationally

print("Current state (baseline):")
print(df[["customer_state", "total_orders", "late_orders", "current_late_pct", "total_revenue"]].round(2))

total_orders = df["total_orders"].sum()
total_current_late = df["late_orders"].sum()
total_revenue = df["total_revenue"].sum()
avg_order_value = total_revenue / total_orders
baseline_late_pct = total_current_late / total_orders * 100

print(f"\nBaseline: {total_current_late} late orders out of {total_orders} ({baseline_late_pct:.2f}%), R$ {total_revenue:,.2f} total revenue")
print(f"Average order value across these 4 states: R$ {avg_order_value:.2f}")

scenarios = {}

def compute_scenario(name, target_late_pct):
    df["scenario_late_orders"] = df["total_orders"] * (target_late_pct / 100)
    reduction = (df["late_orders"] - df["scenario_late_orders"]).clip(lower=0).sum()
    revenue_protected = reduction * avg_order_value
    return {
        "target_late_pct": target_late_pct,
        "orders_shifted_to_on_time": round(float(reduction)),
        "revenue_protected_BRL": round(float(revenue_protected), 2),
    }

df["conservative_target"] = (df["current_late_pct"] - 5).clip(lower=0)
reduction_cons = (df["late_orders"] - df["total_orders"] * df["conservative_target"] / 100).clip(lower=0).sum()
scenarios["conservative_minus_5pp"] = {
    "description": "Each state's late rate drops by 5 percentage points",
    "orders_shifted_to_on_time": round(float(reduction_cons)),
    "revenue_protected_BRL": round(float(reduction_cons * avg_order_value), 2),
}

scenarios["moderate_to_national_avg"] = compute_scenario("Moderate: to national average", NATIONAL_AVG_LATE_PCT)
scenarios["moderate_to_national_avg"]["description"] = f"All 4 states improve to the national average late rate ({NATIONAL_AVG_LATE_PCT}%)"

scenarios["optimistic_to_best_state"] = compute_scenario("Optimistic: to best-performing state level", BEST_STATE_LATE_PCT)
scenarios["optimistic_to_best_state"]["description"] = f"All 4 states improve to match Roraima, the best-performing state ({BEST_STATE_LATE_PCT}%)"

print("\n--- SENSITIVITY SCENARIOS ---")
for name, s in scenarios.items():
    print(f"\n{name}: {s['description']}")
    print(f"  Orders shifted from late to on-time: {s['orders_shifted_to_on_time']}")
    print(f"  Revenue protected: R$ {s['revenue_protected_BRL']:,.2f}")

with open("/home/claude/retailiq/sensitivity_analysis.json", "w") as f:
    json.dump({
        "baseline": {
            "total_orders": int(total_orders),
            "total_late_orders": int(total_current_late),
            "baseline_late_pct": round(float(baseline_late_pct), 2),
            "avg_order_value_BRL": round(float(avg_order_value), 2),
        },
        "scenarios": scenarios,
    }, f, indent=2)

print("\nSaved sensitivity_analysis.json")
