-- Este test asegura que no haya documentos duplicados en la capa silver
-- basándose en la clave principal que se utilizó para la deduplicación.

{{ config(severity = 'error') }}

with validation as (
    select
        coalesce(document_reference_number, certificate_number) as document_identifier,
        count(*) as row_count
    from {{ ref('stg_eudragmdp') }}
    group by 1
)

select *
from validation
where row_count > 1