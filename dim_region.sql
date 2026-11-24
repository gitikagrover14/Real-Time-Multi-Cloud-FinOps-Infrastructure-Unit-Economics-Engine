-- {{ config(materialized='view') }}
{{ config(materialized='view', alias='dbt_dim_region') }}

SELECT
    Region_Key,
    RegionId
FROM {{ source('finops_raw', 'Dim_Region') }}