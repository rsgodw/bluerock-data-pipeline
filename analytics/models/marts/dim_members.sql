with members as (
    select * from {{ ref('stg_members') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['member_id']) }} as member_sk,
    member_id,
    first_name,
    last_name,
    email,
    phone_number,
    has_phone_number,
    city,
    state,
    join_date
from members
