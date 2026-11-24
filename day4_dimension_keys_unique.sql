-- dbt singular test: each dimension surrogate ID must be NOT NULL and unique.
SELECT 'Dim_Service' AS dimension_name, CAST(Service_ID AS CHAR) AS dimension_key,
       COUNT(*) AS records
FROM {{ ref('dim_service') }}
GROUP BY Service_ID
HAVING Service_ID IS NULL OR COUNT(*) <> 1
UNION ALL
SELECT 'Dim_Tenant', CAST(Tenant_ID AS CHAR), COUNT(*)
FROM {{ ref('dim_tenant') }}
GROUP BY Tenant_ID
HAVING Tenant_ID IS NULL OR COUNT(*) <> 1
UNION ALL
SELECT 'Dim_Region', CAST(Region_Key AS CHAR), COUNT(*)
FROM {{ ref('dim_region') }}
GROUP BY Region_Key
HAVING Region_Key IS NULL OR COUNT(*) <> 1
