-- Billing costs must agree between normalized staging and fact (2dp USD).
WITH s AS (
  SELECT COUNT(*) AS n,
    ROUND(COALESCE(SUM(list_cost),0),2) AS list_c,
    ROUND(COALESCE(SUM(contracted_cost),0),2) AS contracted_c,
    ROUND(COALESCE(SUM(billed_cost),0),2) AS billed_c,
    ROUND(COALESCE(SUM(effective_cost),0),2) AS effective_c
  FROM {{ ref('stg_billing') }}
), f AS (
  SELECT COUNT(*) AS n,
    ROUND(COALESCE(SUM(ListCost),0),2) AS list_c,
    ROUND(COALESCE(SUM(ContractedCost),0),2) AS contracted_c,
    ROUND(COALESCE(SUM(BilledCost),0),2) AS billed_c,
    ROUND(COALESCE(SUM(EffectiveCost),0),2) AS effective_c
  FROM {{ ref('fact_spend') }}
)
SELECT s.n AS stage_n, f.n AS fact_n,
       s.billed_c AS stage_billed, f.billed_c AS fact_billed,
       s.effective_c AS stage_effective, f.effective_c AS fact_effective
FROM s CROSS JOIN f
WHERE s.n <> f.n OR s.list_c <> f.list_c OR s.contracted_c <> f.contracted_c
   OR s.billed_c <> f.billed_c OR s.effective_c <> f.effective_c
