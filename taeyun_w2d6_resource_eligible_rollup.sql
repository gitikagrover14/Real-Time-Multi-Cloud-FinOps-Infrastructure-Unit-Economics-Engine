-- Compare the resource rollup to the eligible fact population, not whole fact.
WITH f AS (
 SELECT COUNT(*) n, ROUND(COALESCE(SUM(BilledCost),0),2) billed,
   ROUND(COALESCE(SUM(EffectiveCost),0),2) effective
 FROM {{ ref('fact_spend') }}
 WHERE ResourceId IS NOT NULL AND TRIM(ResourceId) <> ''
), r AS (
 SELECT ROUND(COALESCE(SUM(total_billed_cost),0),2) billed,
   ROUND(COALESCE(SUM(total_effective_cost),0),2) effective
 FROM {{ ref('resource_unit_economics') }}
)
SELECT f.n, f.billed AS fact_billed, r.billed AS resource_billed,
       f.effective AS fact_effective, r.effective AS resource_effective
FROM f CROSS JOIN r
WHERE f.n <> 4100 OR f.billed <> r.billed OR f.effective <> r.effective
