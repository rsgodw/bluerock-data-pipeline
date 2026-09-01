{{ config(materialized='table') }}

with date_spine as (
    select
        dateadd(day, seq4(), '2020-01-01'::date) as date_day
    from table(generator(rowcount => 3650))
)
select
    to_varchar(date_day, 'YYYYMMDD')::NUMBER(8,0) as date_sk,
    date_day as full_date,
    year(date_day) as year,
    month(date_day) as month,
    to_varchar(date_day, 'YYYY-MM')::VARCHAR(7) as year_month,
    dayname(date_day) as day_of_week
from date_spine
