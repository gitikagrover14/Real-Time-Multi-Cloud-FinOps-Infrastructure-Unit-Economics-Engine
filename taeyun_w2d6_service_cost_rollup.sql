-- Whole-fact sum must equal service-level rollup. Excludes nothing.
WITH f AS (
 SELECT COUNT(*) n, ROUND(COALESCE(SUM(BilledCost),0),2) billed,
    ROUND(COALESCE(SUM(EffectiveCost),0),2) effective
 FROM {{ ref('fact_spend') }}
), s AS (
 SELECT ROUND(COALESCE(SUM(total_billed_cost),0),2) billed,
   ROUND(COALESCE(SUM(total_effective_cost),0),2) effective
 FROM {{ ref('service_unit_economics') }}
)
SELECT f.n, f.billed AS fact_billed, s.billed AS service_billed,
       f.effective AS fact_effective, s.effective AS service_effective
FROM f CROSS JOIN s
WHERE f.n <> 4433 OR f.billed <> s.billed OR f.effective <> s.effective
