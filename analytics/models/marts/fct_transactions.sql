{{ config(materialized='table') }}

with transactions as (
    select * from {{ ref('stg_transactions') }}
),

accounts as (
    select * from {{ ref('stg_accounts') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['t.transaction_id']) }} as transaction_sk,
    t.transaction_id,
    {{ dbt_utils.generate_surrogate_key(['t.account_id']) }} as account_sk,
    t.account_id,
    {{ dbt_utils.generate_surrogate_key(['a.member_id']) }} as member_sk,
    a.member_id,
    to_varchar(t.transaction_date::DATE, 'YYYYMMDD')::NUMBER(8,0) as transaction_date_sk,
    cast(t.transaction_date as date) as transaction_date,
    t.transaction_date as transaction_timestamp,
    t.amount,
    t.transaction_type
from transactions t
left join accounts a on t.account_id = a.account_id
