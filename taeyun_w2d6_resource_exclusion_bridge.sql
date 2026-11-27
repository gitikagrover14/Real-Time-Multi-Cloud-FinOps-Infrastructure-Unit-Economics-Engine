-- Unattributed resource bridge must reconcile with whole-fact cost.
WITH f AS (
 SELECT ROUND(COALESCE(SUM(EffectiveCost),0),2) cost FROM {{ ref('fact_spend') }}
), r AS (
 SELECT ROUND(COALESCE(SUM(total_effective_cost),0),2) cost FROM {{ ref('resource_unit_economics') }}
), gap AS (
 SELECT COUNT(*) n, ROUND(COALESCE(SUM(EffectiveCost),0),2) cost
 FROM {{ ref('fact_spend') }} WHERE ResourceId IS NULL OR TRIM(ResourceId) = ''
)
SELECT f.cost AS whole, r.cost AS resource, gap.cost AS unattributed, gap.n
FROM f CROSS JOIN r CROSS JOIN gap
WHERE gap.n <> 333 OR ABS(gap.cost - 38597.49) > 0.01 OR f.cost <> r.cost + gap.cost
