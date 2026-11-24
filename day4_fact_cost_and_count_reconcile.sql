-- dbt singular test: one row indicates source/output row-count or monetary mismatch.
WITH source_summary AS (
 SELECT COUNT(*) AS row_count,
        COALESCE(SUM(BilledCost),0) AS billed_cost,
        COALESCE(SUM(EffectiveCost),0) AS effective_cost
 FROM {{ source('finops_raw', 'Fact_Spend') }}
), output_summary AS (
 SELECT COUNT(*) AS row_count,
        COALESCE(SUM(BilledCost),0) AS billed_cost,
        COALESCE(SUM(EffectiveCost),0) AS effective_cost
 FROM {{ ref('fact_spend') }}
)
SELECT s.row_count AS source_rows, o.row_count AS output_rows,
       s.billed_cost AS source_billed, o.billed_cost AS output_billed,
       s.effective_cost AS source_effective, o.effective_cost AS output_effective
FROM source_summary s CROSS JOIN output_summary o
WHERE s.row_count <> o.row_count
   OR ABS(s.billed_cost - o.billed_cost) > 0.01
   OR ABS(s.effective_cost - o.effective_cost) > 0.01
