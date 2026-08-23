with accounts as (
    select * from {{ ref('stg_accounts') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['account_id']) }} as account_sk,
    account_id,
    member_id,
    account_type,
    balance
from accounts
