"""
RetailIQ — Sales Forecasting Model
Forecasts daily revenue using SARIMA, evaluated on a true held-out test period.
"""
import pandas as pd
import numpy as np
import psycopg2
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
import json
import warnings
warnings.filterwarnings("ignore")

conn = psycopg2.connect(host="localhost", dbname="retailiq", user="postgres", password="postgres")

query = """
SELECT
    DATE(o.order_purchase_timestamp) AS order_date,
    SUM(oi.price) AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
GROUP BY 1
ORDER BY 1
"""
df = pd.read_sql(query, conn)
conn.close()

df["order_date"] = pd.to_datetime(df["order_date"])
df = df.set_index("order_date").asfreq("D")
df["revenue"] = df["revenue"].fillna(0)

# Drop the known data collection ramp-up (Sept-Dec 2016) AND the right-censored
# tail (order volume drops from ~2,000/week to 130 then near-zero after Aug 20,
# 2018 — this is a documented data-collection cutoff artifact in this dataset,
# not a real demand collapse. Verified via weekly order counts before trimming.)
print(f"Full date range: {df.index.min()} to {df.index.max()}, {len(df)} days")
df_clean = df.loc["2017-01-01":"2018-08-19"]
print(f"Using clean range: {df_clean.index.min()} to {df_clean.index.max()}, {len(df_clean)} days")

# Weekly aggregation reduces day-to-day noise for a clearer trend/seasonality signal
weekly = df_clean["revenue"].resample("W").sum()
print(f"\nWeekly series: {len(weekly)} weeks")

# Real train/test split — last 8 weeks held out, never seen by the model
train = weekly[:-8]
test = weekly[-8:]
print(f"Train: {len(train)} weeks, Test (held out): {len(test)} weeks")

# SARIMA model — (1,1,1) order, weekly seasonality not strong enough at this length
# for full seasonal SARIMA, so we use SARIMA(1,1,1) with trend term
model = SARIMAX(train, order=(2, 1, 2), trend="c", enforce_stationarity=False, enforce_invertibility=False)
fit = model.fit(disp=False)

forecast = fit.forecast(steps=len(test))
forecast.index = test.index

# Real evaluation metrics on held-out data
rmse = np.sqrt(mean_squared_error(test, forecast))
mape = mean_absolute_percentage_error(test, forecast) * 100
mean_weekly_revenue = test.mean()

print(f"\n--- FORECAST EVALUATION (held-out 8 weeks, never seen during training) ---")
print(f"RMSE: R$ {rmse:,.2f}")
print(f"MAPE: {mape:.1f}%")
print(f"Mean actual weekly revenue (test period): R$ {mean_weekly_revenue:,.2f}")
print(f"RMSE as % of mean revenue: {100*rmse/mean_weekly_revenue:.1f}%")

print("\nActual vs Forecast (held-out weeks):")
comparison = pd.DataFrame({"actual": test, "forecast": forecast.round(2)})
comparison["abs_error"] = (comparison["actual"] - comparison["forecast"]).abs().round(2)
print(comparison)

# Save results
results = {
    "train_weeks": len(train),
    "test_weeks": len(test),
    "rmse": round(float(rmse), 2),
    "mape_pct": round(float(mape), 2),
    "mean_test_revenue": round(float(mean_weekly_revenue), 2),
    "rmse_pct_of_mean": round(float(100*rmse/mean_weekly_revenue), 1),
    "model": "SARIMAX(2,1,2) with trend",
}
with open("/home/claude/retailiq/forecast_results.json", "w") as f:
    json.dump(results, f, indent=2)

# Save the full weekly series + forecast for dashboard/visualization
comparison.to_csv("/home/claude/retailiq/forecast_comparison.csv")
weekly.to_csv("/home/claude/retailiq/weekly_revenue_full.csv")

print("\nSaved forecast_results.json, forecast_comparison.csv, weekly_revenue_full.csv")
