with source as (
    select * from {{ source('raw', 'transactions') }}
),

renamed as (
    select
        transaction_id,
        account_id,
        transaction_date,
        amount,
        transaction_type
    from source
)

select * from renamed
