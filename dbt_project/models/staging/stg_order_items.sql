-- Staging model: order line items with total line value
select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    price,
    freight_value,
    price + freight_value as line_total
from {{ source('raw', 'order_items') }}
where order_id is not null
