with source as (
    select * from {{ source('raw', 'accounts') }}
),

renamed as (
    select
        account_id,
        member_id,
        account_type,
        balance
    from source
)

select * from renamed
