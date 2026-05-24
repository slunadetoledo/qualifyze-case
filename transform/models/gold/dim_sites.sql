{{ config(materialized='table') }}

with staging as (
    select * from {{ ref('stg_eudragmdp') }}
),

deduplicated_sites as (
    select
        -- Generamos una clave maestra unificada basada en la disponibilidad de IDs
        coalesce(oms_location_id, duns_number, 'UNKNOWN') as site_master_id,
        oms_location_id,
        duns_number,
        oms_organisation_id,
        site_name,
        postcode,
        -- En caso de duplicados, tomamos el registro más reciente según la fecha de inspección
        row_number() over (
            partition by coalesce(oms_location_id, duns_number, 'UNKNOWN') 
            order by issue_date desc
        ) as rn
    from staging
    where oms_location_id is not null or duns_number is not null
)

select
    site_master_id,
    oms_location_id,
    duns_number,
    oms_organisation_id,
    site_name,
    postcode
from deduplicated_sites 
where rn = 1