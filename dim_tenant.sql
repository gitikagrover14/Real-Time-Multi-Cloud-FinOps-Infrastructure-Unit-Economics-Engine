-- {{ config(materialized='view') }}
{{ config(materialized='view', alias='dbt_dim_tenant') }}

SELECT
    Tenant_ID,
    BillingAccountId,
    SubAccountId
FROM {{ source('finops_raw', 'Dim_Tenant') }}