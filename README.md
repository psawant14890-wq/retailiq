# RetailIQ — E-Commerce Revenue & Delivery Performance Analytics

A full-stack data analytics project on real Brazilian e-commerce data (Olist marketplace, ~100K orders, 2017–2018), built to the top-tier standard: relational SQL, dbt-modeled warehouse layer, evaluated forecasting, and a quantified business recommendation.

**🔴 Live Dashboard:** [RetailIQ Interactive Analytics](https://retailiq-wq4exudkd9nfhh8aio6yjy.streamlit.app)

**📊 MBB Executive Summary:** See `excel_deck/RetailIQ_Executive_Deck.pptx`

**📈 Sensitivity Model:** See `excel_deck/RetailIQ_Sensitivity_Model.xlsx`

---

## Situation → Complication → Recommendation

**Situation:** Olist is a multi-seller e-commerce marketplace connecting ~3,000 small sellers to customers across Brazil. Revenue grew from R$280 in Sept 2016 to a peak of over R$1.17M/month by Nov 2017, with a visible Black Friday seasonal spike.

**Complication:** Delivery delays are strongly associated with customer dissatisfaction. Orders delivered on time average a **4.28/5** review score; orders delivered **7+ days late** average just **1.73/5**. **R$607,588** in revenue is tied to orders in this severe-delay bucket — concentrated disproportionately in specific states (Alagoas: 23.9% late-delivery rate vs. São Paulo: 5.9%).

**Recommendation:** Prioritize logistics intervention in the worst-performing states (AL, MA, PI, CE — all >15% late-delivery rate) rather than a blanket logistics overhaul. This targets the R$600K+ in at-risk revenue at its geographic source rather than spreading limited operational budget evenly across all 24 states.

## Sensitivity Analysis — "What if the intervention only partially works?"

Real computed scenarios for the 4 target states (AL, MA, PI, CE — 3,176 orders, R$613,591 in revenue, baseline 17.79% late rate vs. 8.11% national average):

| Scenario | Target late rate | Orders shifted to on-time | Revenue protected |
|---|---|---|---|
| **Conservative** — each state improves by 5pp | varies by state | 159 orders | **R$30,680** |
| **Moderate** — all 4 states reach the national average | 8.11% | 307 orders | **R$59,394** |
| **Optimistic** — all 4 states match the best-performing state (Roraima) | 2.9% | 473 orders | **R$91,362** |

This means even a partial, conservative win on the recommendation (5-point improvement, not full parity with the national average) still protects ~R$30,700 in revenue from the high-dissatisfaction bucket — the recommendation holds up under a pessimistic assumption, not just the best case.

## North Star Metric

**On-Time Delivery Rate** (currently 91.89% nationally, 76-85% in the 4 target states) is the proposed North Star metric for this analysis — chosen because it has a direct, measured causal pathway to the only satisfaction signal in this dataset (review score: 4.28 on-time vs. 1.73 when 7+ days late), and is something Operations can directly act on, unlike review score itself which is a lagging, noisier indicator.

## Proposed Experiment Design (A/B Test)

To validate the recommendation before a full rollout: randomly assign half of new orders in AL/MA/PI/CE to an expedited-carrier treatment group, half to the existing logistics process (control).
- **Primary metric:** On-time delivery rate (treatment vs. control)
- **Guardrail metric:** Shipping cost per order (expedited carriers cost more — must not erase the revenue-protection benefit)
- **Minimum detectable effect:** A 5-percentage-point improvement (the conservative scenario above) at 80% power, 95% confidence would require approximately 1,200 orders per arm, achievable within ~4-6 weeks given current order volume in these states (3,176 orders over the ~20-month analysis window).
- **Decision rule:** Roll out fully if treatment shows ≥5pp improvement in on-time rate without guardrail-metric (cost) breach.

## Forecast Confidence Intervals

The SARIMA forecast's point estimates (RMSE R$43,377, MAPE 19.3%) are reported alongside 95% confidence intervals, not as bare point predictions — all 8 held-out actuals fell within their predicted 95% CI band (100% empirical coverage on this test set; note the small n=8 means this should be read directionally, not as a precise long-run coverage guarantee).

## Data Governance Note (controls framing)

The 9 dbt tests and 6 pytest checks function as automated data controls: `unique`/`not_null` tests on `order_id` catch duplication before it reaches the business-facing mart (as the 533-row bug demonstrated), `accepted_values` tests catch unexpected category drift in `order_status`/`delivery_bucket`, and `relationships` tests enforce referential integrity between staging models. This is the same control logic an audit/advisory review would check for in a production data pipeline.

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
│   ├── profiles_bigquery_example.yml  # BigQuery migration template (adapter-agnostic models)
│   └── dbt_project.yml
├── python/
│   ├── forecast_model.py              # SARIMA forecast with held-out evaluation + 95% CI
│   ├── sensitivity_analysis.py        # 3-scenario sensitivity analysis on target states
│   └── visualize.py                   # Dashboard chart generation
├── streamlit_app/
│   ├── app.py                         # Live 2-page interactive dashboard
│   ├── data_prep.py                   # Generates pre-aggregated CSVs from Postgres
│   ├── data/                          # 11 small pre-aggregated CSVs (<10KB total)
│   └── requirements.txt
├── excel_deck/
│   ├── RetailIQ_Sensitivity_Model.xlsx  # Interactive MBB-style model, 139 live formulas
│   └── RetailIQ_Executive_Deck.pptx     # 3-slide Situation-Complication-Recommendation deck
├── tests/
│   └── test_data_quality.py           # 6 pytest data validation tests
├── requirements.txt
└── README.md
```

**Note:** the deployed live app additionally relies on a few Streamlit Cloud-specific config files (`.python-version`, a deploy-scoped `requirements.txt` split) created directly during deployment troubleshooting — see commit history for the full debugging trail.

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
