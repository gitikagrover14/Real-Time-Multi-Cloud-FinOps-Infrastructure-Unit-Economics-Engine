-- {{ config(materialized='view') }}
{{ config(materialized='view', alias='dbt_dim_service') }}

SELECT
    Service_ID,
    ProviderName,
    InvoiceIssuerName,
    ServiceCategory,
    ServiceName
FROM {{ source('finops_raw', 'Dim_Service') }}