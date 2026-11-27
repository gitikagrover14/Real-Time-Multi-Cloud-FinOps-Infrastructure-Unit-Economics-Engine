-- Should return zero rows; combined with row parity detects dropped fact rows.
SELECT f.Spend_ID, f.Service_ID, f.Tenant_ID, f.Region_Key
FROM {{ ref('fact_spend') }} f
LEFT JOIN {{ ref('dim_service') }} s ON f.Service_ID = s.Service_ID
LEFT JOIN {{ ref('dim_tenant') }} t ON f.Tenant_ID = t.Tenant_ID
LEFT JOIN {{ ref('dim_region') }} r ON f.Region_Key = r.Region_Key
WHERE f.Service_ID IS NULL OR f.Tenant_ID IS NULL OR f.Region_Key IS NULL
   OR s.Service_ID IS NULL OR t.Tenant_ID IS NULL OR r.Region_Key IS NULL
