-- At least 58 source rows have blank region; assert none vanish in fact.
-- This requires blank-to-dimension mapping to be preserved by upstream load.
WITH expected AS (
  SELECT COUNT(*) AS n FROM {{ ref('stg_billing') }}
  WHERE region_id IS NULL OR TRIM(region_id) = ''
), observed AS (
  SELECT COUNT(*) AS n FROM {{ ref('fact_spend') }} f
  LEFT JOIN {{ ref('dim_region') }} d ON f.Region_Key = d.Region_Key
  WHERE d.RegionId IS NULL OR TRIM(d.RegionId) = ''
)
SELECT expected.n AS source_blank_regions, observed.n AS fact_blank_regions
FROM expected CROSS JOIN observed
WHERE expected.n <> 58 OR observed.n <> expected.n
