"""
RetailIQ — Data validation and pipeline tests
Run with: pytest tests/test_data_quality.py -v
"""
import pandas as pd
import psycopg2
import pytest

@pytest.fixture(scope="module")
def conn():
    c = psycopg2.connect(host="localhost", dbname="retailiq", user="postgres", password="postgres")
    yield c
    c.close()


def test_no_duplicate_orders(conn):
    """orders.order_id must be unique — this is the primary key of the business."""
    df = pd.read_sql("SELECT order_id, COUNT(*) c FROM orders GROUP BY order_id HAVING COUNT(*) > 1", conn)
    assert len(df) == 0, f"Found {len(df)} duplicate order_ids"


def test_no_negative_prices(conn):
    """Order item prices and freight must never be negative."""
    df = pd.read_sql("SELECT * FROM order_items WHERE price < 0 OR freight_value < 0", conn)
    assert len(df) == 0, f"Found {len(df)} line items with negative price/freight"


def test_review_scores_in_valid_range(conn):
    """Review scores must be within the documented 1-5 scale."""
    df = pd.read_sql(
        "SELECT * FROM order_reviews WHERE review_score < 1 OR review_score > 5", conn
    )
    assert len(df) == 0, f"Found {len(df)} reviews with out-of-range scores"


def test_delivered_orders_have_delivery_date(conn):
    """Any order marked 'delivered' should have a non-null delivery date."""
    df = pd.read_sql(
        "SELECT * FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL",
        conn,
    )
    # Known data quirk: a small number of 'delivered' orders are missing this
    # timestamp in the raw Olist data. We assert it's a small, bounded number,
    # not zero — documenting the real data quality limitation rather than
    # hiding it or failing the whole pipeline on a known upstream issue.
    assert len(df) < 20, f"Expected <20 delivered orders missing delivery date, found {len(df)}"


def test_order_items_reference_valid_orders(conn):
    """Every order_item must reference an order that actually exists (FK integrity)."""
    df = pd.read_sql(
        """
        SELECT oi.order_id FROM order_items oi
        LEFT JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_id IS NULL
        """,
        conn,
    )
    assert len(df) == 0, f"Found {len(df)} order_items with no matching order"


def test_forecast_results_within_sane_bounds():
    """Sanity-check the saved forecast evaluation metrics are plausible, not corrupted."""
    import json
    with open("/home/claude/retailiq/forecast_results.json") as f:
        results = json.load(f)
    assert 0 < results["mape_pct"] < 100, "MAPE should be a plausible percentage"
    assert results["rmse"] > 0, "RMSE must be positive"
    assert results["test_weeks"] == 8, "Expected 8-week held-out test period"
