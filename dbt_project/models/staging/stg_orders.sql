-- Staging model: cleaned orders, one row per order
select
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    case
        when order_delivered_customer_date is not null
             and order_delivered_customer_date > order_estimated_delivery_date
        then true
        else false
    end as is_late_delivery
from {{ source('raw', 'orders') }}
where order_id is not null
