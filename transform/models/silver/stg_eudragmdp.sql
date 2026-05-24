{{ config(materialized='view') }}

with source as (
    select * from {{ source('bronze', 'raw_eudragmdp') }}
),

renamed_and_casted as (
    select
        -- Identificadores (limpieza de espacios)
        -- Las columnas ya se han normalizado a snake_case mediante el script de ingesta (load_bronze.py)
        trim(cast(document_reference_number as varchar)) as document_reference_number,
        trim(cast(certificate_number as varchar)) as certificate_number,
        trim(cast(oms_organisation_id as varchar)) as oms_organisation_id,
        trim(cast(oms_location_id as varchar)) as oms_location_id,
        trim(cast(duns_number as varchar)) as duns_number,
        
        -- Datos del sitio
        trim(cast(site_name as varchar)) as site_name,
        trim(cast(postcode as varchar)) as postcode,
        trim(cast(document_type as varchar)) as document_type,
        
        -- Parseo de fechas (Asumiendo que pandas las importó como texto o timestamp)
        cast(inspection_end_date as date) as inspection_end_date,
        cast(issue_date as date) as issue_date,
        
        -- Metadatos de la ingesta
        _ingested_at,
        _source_file
    from source
),

deduplicated_updates as (
    select
        *,
        -- Si un mismo documento se actualiza en diferentes archivos XLS con el tiempo,
        -- hacemos un 'Upsert lógico' quedándonos solo con el más reciente
        row_number() over (
            partition by coalesce(document_reference_number, certificate_number)
            order by _ingested_at desc
        ) as rn
    from renamed_and_casted
)

select
    document_reference_number,
    certificate_number,
    oms_organisation_id,
    oms_location_id,
    duns_number,
    site_name,
    postcode,
    document_type,
    inspection_end_date,
    issue_date,
    _ingested_at,
    _source_file
from deduplicated_updates
where rn = 1