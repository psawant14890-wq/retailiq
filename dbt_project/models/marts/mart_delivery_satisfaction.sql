-- Mart: order-level delivery performance joined to revenue and review score
-- This is the business-ready table the dashboard reads from.

with orders as (
    select * from {{ ref('stg_orders') }}
),

order_revenue as (
    select
        order_id,
        sum(line_total) as order_value
    from {{ ref('stg_order_items') }}
    group by order_id
),

reviews as (
    -- Some orders have multiple review submissions in the raw data (a real data
    -- quality issue this dbt test suite caught: see _schema.yml unique test).
    -- Deduplicated to the most recent review per order.
    select
        order_id,
        review_score,
        row_number() over (
            partition by order_id
            order by review_creation_date desc
        ) as rn
    from {{ source('raw', 'order_reviews') }}
)

select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.is_late_delivery,
    case
        when o.order_delivered_customer_date <= o.order_estimated_delivery_date then 'on_time'
        when o.order_delivered_customer_date - o.order_estimated_delivery_date <= interval '7 days' then 'late_1_7_days'
        else 'late_7plus_days'
    end as delivery_bucket,
    r.review_score,
    coalesce(rev.order_value, 0) as order_value
from orders o
left join order_revenue rev on o.order_id = rev.order_id
left join reviews r on o.order_id = r.order_id and r.rn = 1
where o.order_status = 'delivered'
  and o.order_delivered_customer_date is not null
