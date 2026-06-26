"""
RetailIQ — Live Dashboard (Streamlit)
Deployed version of the RetailIQ analysis. Reads from pre-aggregated CSVs
(see data_prep.py) rather than a live database, since this app is meant to
run on Streamlit Community Cloud without needing a hosted Postgres instance.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="RetailIQ Dashboard", page_icon="📦", layout="wide")

DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    return {
        "kpi": pd.read_csv(DATA_DIR / "kpi_summary.csv"),
        "monthly": pd.read_csv(DATA_DIR / "monthly_revenue.csv"),
        "categories": pd.read_csv(DATA_DIR / "top_categories.csv"),
        "states": pd.read_csv(DATA_DIR / "state_late_delivery.csv"),
        "delivery_satisfaction": pd.read_csv(DATA_DIR / "delivery_satisfaction.csv"),
        "segments": pd.read_csv(DATA_DIR / "segment_counts.csv"),
        "top20": pd.read_csv(DATA_DIR / "top20_customers.csv"),
        "payment_types": pd.read_csv(DATA_DIR / "payment_types.csv"),
        "installments": pd.read_csv(DATA_DIR / "installments.csv"),
        "weekly_revenue": pd.read_csv(DATA_DIR / "weekly_revenue_full.csv"),
        "forecast": pd.read_csv(DATA_DIR / "forecast_comparison.csv"),
    }

data = load_data()

st.title("📦 RetailIQ — E-Commerce Revenue & Delivery Analytics")
st.caption("Real data: Olist Brazilian E-Commerce dataset, ~100K orders (2017-2018)")

page = st.sidebar.radio("Page", ["Executive Overview", "Customer Segmentation"])

# ============================================================
# PAGE 1: EXECUTIVE OVERVIEW
# ============================================================
if page == "Executive Overview":
    kpi = data["kpi"].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"R$ {kpi['total_revenue']/1e6:.2f}M")
    col2.metric("Late Delivery Rate", f"{kpi['late_delivery_rate_pct']}%")
    col3.metric("Avg Review Score", f"{kpi['avg_review_score']} / 5")
    col4.metric("Revenue at Risk (7+ Days Late)", f"R$ {kpi['revenue_at_risk']/1e3:.1f}K")

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Monthly Revenue Trend")
        fig = px.line(data["monthly"], x="year_month", y="revenue", markers=True)
        fig.update_layout(yaxis_title="Revenue (R$)", xaxis_title="Month", height=380)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top 10 Categories by Revenue")
        cat_sorted = data["categories"].sort_values("revenue")
        fig2 = px.bar(cat_sorted, x="revenue", y="category", orientation="h")
        fig2.update_layout(height=380, xaxis_title="Revenue (R$)", yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    with right:
        st.subheader("Late Delivery Rate by State (Top 10)")
        st_sorted = data["states"].sort_values("late_pct")
        fig3 = px.bar(st_sorted, x="late_pct", y="customer_state", orientation="h",
                       color="late_pct", color_continuous_scale="Reds")
        fig3.update_layout(height=380, xaxis_title="Late Delivery Rate (%)", yaxis_title="", showlegend=False)
        fig3.update_coloraxes(showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Avg Review Score by Delivery Performance")
        colors = {"On Time / Early": "#2ca02c", "Late 1-7 Days": "#ff7f0e", "Late 7+ Days": "#d62728"}
        fig4 = px.bar(data["delivery_satisfaction"], x="delivery_bucket", y="avg_review_score",
                       text="avg_review_score", color="delivery_bucket",
                       color_discrete_map=colors)
        fig4.update_traces(textposition="outside")
        fig4.update_layout(height=380, yaxis_title="Avg Review Score", xaxis_title="",
                            showlegend=False, yaxis_range=[0, 5])
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.subheader("Sales Forecast — SARIMA(2,1,2), 8-Week Held-Out Evaluation")
    weekly = data["weekly_revenue"]
    weekly.columns = ["date", "revenue"]
    forecast = data["forecast"]
    forecast.columns = ["date", "actual", "forecast", "ci_lower", "ci_upper", "abs_error", "within_ci"]

    fig5 = go.Figure()
    train_part = weekly.iloc[:-8]
    fig5.add_trace(go.Scatter(x=train_part["date"], y=train_part["revenue"], name="Actual (training)", line=dict(color="#1f77b4")))
    fig5.add_trace(go.Scatter(x=forecast["date"], y=forecast["actual"], name="Actual (held-out test)", line=dict(color="#2ca02c"), mode="lines+markers"))
    fig5.add_trace(go.Scatter(x=forecast["date"], y=forecast["forecast"], name="SARIMA Forecast", line=dict(color="#d62728", dash="dash"), mode="lines+markers"))
    fig5.add_trace(go.Scatter(x=forecast["date"], y=forecast["ci_upper"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig5.add_trace(go.Scatter(x=forecast["date"], y=forecast["ci_lower"], fill="tonexty", fillcolor="rgba(214,39,40,0.15)", line=dict(width=0), name="95% CI"))
    fig5.update_layout(height=420, yaxis_title="Weekly Revenue (R$)", xaxis_title="")
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("RMSE: R$43,377 (19.8% of mean) · MAPE: 19.3% · 95% CI empirical coverage: 100% (n=8, small-sample caveat applies)")

# ============================================================
# PAGE 2: CUSTOMER SEGMENTATION
# ============================================================
else:
    st.subheader("Customers by RFM Segment")
    fig = px.bar(data["segments"], x="segment", y="count", text="count",
                 color="segment",
                 category_orders={"segment": ["Champions", "Loyal Customers", "Potential Loyalists", "At Risk", "Lost"]})
    fig.update_traces(textposition="outside")
    fig.update_layout(height=400, showlegend=False, xaxis_title="", yaxis_title="Number of Customers")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 20 Customers by RFM Score")
    st.dataframe(data["top20"], use_container_width=True, hide_index=True)

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Revenue Share by Payment Type")
        fig2 = px.pie(data["payment_types"], names="payment_type", values="total_value", hole=0.5)
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    with right:
        st.subheader("Order Count by Number of Installments")
        fig3 = px.bar(data["installments"], x="payment_installments", y="order_count")
        fig3.update_layout(height=400, xaxis_title="Installments", yaxis_title="Order Count")
        st.plotly_chart(fig3, use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("Built by Pranay Sawant · [GitHub repo link here]")
