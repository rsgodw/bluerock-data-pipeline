with source as (
    select * from {{ source('raw', 'members') }}
),

renamed as (
    select
        member_id,
        first_name,
        last_name,
        email,
        phone_number,
        has_phone_number,
        join_date
    from source
)

select * from renamed
