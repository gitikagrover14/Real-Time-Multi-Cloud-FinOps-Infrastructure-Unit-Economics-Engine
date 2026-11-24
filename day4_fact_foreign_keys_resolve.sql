-- dbt singular test: unmatched or NULL fact foreign keys.
-- A documented unknown member is acceptable ONLY when it has a real matching key.
SELECT f.Spend_ID, f.Service_ID, f.Tenant_ID, f.Region_Key
FROM {{ ref('fact_spend') }} f
LEFT JOIN {{ ref('dim_service') }} ds ON f.Service_ID = ds.Service_ID
LEFT JOIN {{ ref('dim_tenant') }} dt ON f.Tenant_ID = dt.Tenant_ID
LEFT JOIN {{ ref('dim_region') }} dr ON f.Region_Key = dr.Region_Key
WHERE ds.Service_ID IS NULL OR dt.Tenant_ID IS NULL OR dr.Region_Key IS NULL
