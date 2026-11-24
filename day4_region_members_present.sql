-- dbt singular test: all distinct non-null source region names must be in the dimension.
-- Legitimately empty source RegionId values are handled by separate fact-FK tests.
SELECT DISTINCT src.RegionId AS missing_region
FROM {{ source('finops_raw', 'stg_focus_billing') }} src
LEFT JOIN {{ ref('dim_region') }} d ON TRIM(src.RegionId) = TRIM(d.RegionId)
WHERE src.RegionId IS NOT NULL AND TRIM(src.RegionId) <> ''
  AND d.Region_Key IS NULL
