select account_id, balance, account_type
from {{ ref('dim_accounts') }}
where account_type = 'Savings' and balance < 0
