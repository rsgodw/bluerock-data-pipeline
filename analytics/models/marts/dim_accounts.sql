with accounts as (
    select * from {{ ref('stg_accounts') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['account_id']) }} as account_sk,
    account_id,
    {{ dbt_utils.generate_surrogate_key(['member_id']) }} as member_sk,
    account_type,
    balance
from accounts
