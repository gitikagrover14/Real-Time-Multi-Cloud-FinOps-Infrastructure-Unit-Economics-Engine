-- dbt singular test: converting optional empty strings to NULL must not drop rows
-- or silently change the count of missing values.
WITH raw_counts AS (
 SELECT
   SUM(CASE WHEN SubAccountId IS NULL OR TRIM(SubAccountId) = '' THEN 1 ELSE 0 END) AS n_sub,
   SUM(CASE WHEN RegionId IS NULL OR TRIM(RegionId) = '' THEN 1 ELSE 0 END) AS n_region,
   SUM(CASE WHEN ResourceId IS NULL OR TRIM(ResourceId) = '' THEN 1 ELSE 0 END) AS n_resource,
   SUM(CASE WHEN Tags IS NULL OR TRIM(Tags) = '' THEN 1 ELSE 0 END) AS n_tags
 FROM {{ source('finops_raw', 'stg_focus_billing') }}
), stage_counts AS (
 SELECT
   SUM(CASE WHEN sub_account_id IS NULL THEN 1 ELSE 0 END) AS n_sub,
   SUM(CASE WHEN region_id IS NULL THEN 1 ELSE 0 END) AS n_region,
   SUM(CASE WHEN resource_id IS NULL THEN 1 ELSE 0 END) AS n_resource,
   SUM(CASE WHEN tags IS NULL THEN 1 ELSE 0 END) AS n_tags
 FROM {{ ref('stg_billing') }}
)
SELECT 'optional_null_conversion_mismatch' AS test_failure
FROM raw_counts r CROSS JOIN stage_counts s
WHERE NOT (r.n_sub <=> s.n_sub
 AND r.n_region <=> s.n_region
 AND r.n_resource <=> s.n_resource
 AND r.n_tags <=> s.n_tags);
