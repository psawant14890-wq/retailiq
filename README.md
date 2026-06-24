# RetailIQ — E-Commerce Revenue & Delivery Performance Analytics

A full-stack data analytics project on real Brazilian e-commerce data (Olist marketplace, ~100K orders, 2017–2018), built to the top-tier standard: relational SQL, dbt-modeled warehouse layer, evaluated forecasting, and a quantified business recommendation.

## Situation → Complication → Recommendation

**Situation:** Olist is a multi-seller e-commerce marketplace connecting ~3,000 small sellers to customers across Brazil. Revenue grew from R$280 in Sept 2016 to a peak of over R$1.17M/month by Nov 2017, with a visible Black Friday seasonal spike.

**Complication:** Delivery delays are strongly associated with customer dissatisfaction. Orders delivered on time average a **4.28/5** review score; orders delivered **7+ days late** average just **1.73/5**. **R$607,588** in revenue is tied to orders in this severe-delay bucket — concentrated disproportionately in specific states (Alagoas: 23.9% late-delivery rate vs. São Paulo: 5.9%).

**Recommendation:** Prioritize logistics intervention in the worst-performing states (AL, MA, PI, CE — all >15% late-delivery rate) rather than a blanket logistics overhaul. This targets the R$600K+ in at-risk revenue at its geographic source rather than spreading limited operational budget evenly across all 24 states.

## Key Findings (real numbers, from real data)

| Finding | Number |
|---|---|
| Total analyzed revenue (2017–2018, clean period) | R$ 14.07M (on-time) + R$ 1.35M (late) |
| Revenue tied to severely late (7+ day) deliveries | **R$ 607,588** |
| Review score: on-time vs. 7+ days late | **4.28 vs. 1.73** |
| Worst-performing state by late-delivery rate | Alagoas (AL) — **23.9%** |
| Best-performing state | Roraima (RO) — **2.9%** |
| Top revenue category | Health & Beauty — R$1.26M |
| 8-week sales forecast accuracy (held-out test) | **MAPE 19.3%**, RMSE R$43,377 (19.8% of mean weekly revenue) |

**Note on repeat purchase behavior:** I initially hypothesized that low satisfaction → lower repeat-purchase rate → quantifiable revenue loss. The real data didn't support a clean version of this story — repeat purchase rate is low across all satisfaction tiers (2.7–5.3%), consistent with Olist's nature as a largely one-time-purchase marketplace, and low-satisfaction customers actually had a slightly *higher* average lifetime spend. I'm reporting this honestly rather than forcing a narrative the data doesn't support — the late-delivery revenue exposure figure above is the dollar translation that the data does cleanly back.

## Methodology

1. **Data**: Real Olist Brazilian E-Commerce dataset — 99,441 orders, 112,650 line items, 100,000 reviews, across 7 relational tables, loaded into PostgreSQL with proper foreign keys.
2. **SQL analysis**: CTEs and window functions (`LAG`, `RANK`, `NTILE`, `SUM() OVER`) for monthly trend analysis, category ranking, RFM customer segmentation, and delivery performance by state.
3. **dbt modeling layer**: Staging models (`stg_orders`, `stg_order_items`) and a business-ready mart (`mart_delivery_satisfaction`) with 9 automated data tests.
4. **Forecasting**: SARIMA(2,1,2) on weekly revenue, evaluated on a genuine 8-week held-out test period never seen during training.
5. **Data validation**: 6 pytest tests + 9 dbt tests covering uniqueness, referential integrity, valid ranges, and pipeline sanity checks.

## A Real Bug Found and Fixed

The dbt test suite caught a genuine data quality issue: joining `order_reviews` directly onto `orders` created **533 duplicate `order_id` rows** in the mart table, because a small number of orders have multiple review submissions in the raw data. Fixed by deduplicating to the most recent review per order using `ROW_NUMBER()`. This is documented in `mart_delivery_satisfaction.sql` — the kind of issue dbt's testing layer exists specifically to catch.

## Assumptions & Limitations

- **Date range trimmed to 2017-01-01 through 2018-08-19.** The raw dataset's tail (after Aug 20, 2018) shows order volume collapsing from ~2,000/week to under 10/week — a documented data-collection cutoff artifact, not a real demand crash. Including it would have corrupted the forecast evaluation (verified: MAPE dropped from 41.3% to 19.3% after this fix).
- **Forecast model is univariate** (revenue history only) — no exogenous regressors (marketing spend, holidays, promotions). A production version would likely add a holiday/Black-Friday dummy variable, given the visible seasonal spike in Nov 2017.
- **Repeat-purchase-based dollar translation was tested and abandoned** when the data didn't support it cleanly (see note above) — the late-delivery revenue exposure figure is used instead as the primary dollar metric.
- **Geolocation data** was unavailable from this data source at build time, so state-level (not city-level) granularity is used for delivery performance.

## Tech Stack
PostgreSQL · SQL (CTEs, window functions) · Python (pandas, statsmodels, scikit-learn) · dbt-core + dbt-postgres · pytest · matplotlib/seaborn

## Repo Structure
```
retailiq/
├── data/raw/                          # Original Olist CSVs (7 tables)
├── sql/
│   ├── 01_schema.sql                  # Relational schema with FKs and indexes
│   └── 02_analysis.sql                # CTEs, window functions, RFM segmentation
├── dbt_project/
│   ├── models/staging/                # stg_orders, stg_order_items
│   ├── models/marts/                  # mart_delivery_satisfaction + schema tests
│   └── dbt_project.yml
├── python/
│   ├── forecast_model.py              # SARIMA forecast with held-out evaluation
│   └── visualize.py                   # Dashboard chart generation
├── tests/
│   └── test_data_quality.py           # 6 pytest data validation tests
├── requirements.txt
└── README.md
```

## How to Reproduce
```bash
# 1. Load data into PostgreSQL
createdb retailiq
psql -d retailiq -f sql/01_schema.sql
psql -d retailiq -c "\copy customers FROM 'data/raw/olist_customers_dataset.csv' WITH (FORMAT csv, HEADER true)"
# (repeat \copy for each table — see sql/01_schema.sql for table order)

# 2. Run SQL analysis
psql -d retailiq -f sql/02_analysis.sql

# 3. Run dbt models and tests
cd dbt_project && dbt run && dbt test

# 4. Run forecasting model
python3 python/forecast_model.py

# 5. Generate dashboard visuals
python3 python/visualize.py

# 6. Run data quality tests
pytest tests/test_data_quality.py -v
```

## Next Steps
- Migrate dbt models to BigQuery/Snowflake (adapter swap — models require no rewrite)
- Build live Power BI dashboard with state-level map visual once geolocation data is available
- Add marketing-spend and holiday-calendar exogenous regressors to the forecast model
