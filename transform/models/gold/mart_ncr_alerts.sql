{{ config(materialized='table') }}

with staging as (
    select * from {{ ref('stg_eudragmdp') }}
),

ncr_reports as (
    select
        document_reference_number,
        document_type,
        oms_location_id,
        duns_number,
        site_name,
        issue_date,
        _ingested_at
    from staging
    -- Filtrar solo los reportes de no cumplimiento (NCR)
    where document_type = 'Non-Compliance Report'
      and document_reference_number is not null
)

select * from ncr_reports