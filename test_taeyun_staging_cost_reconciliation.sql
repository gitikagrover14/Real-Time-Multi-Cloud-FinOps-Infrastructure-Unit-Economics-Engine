-- dbt singular test: preserve exact DECIMAL cost totals across raw -> staging.
WITH raw_totals AS (
    SELECT
        SUM(CAST(NULLIF(TRIM(ListCost), '') AS DECIMAL(18,6))) AS list_cost,
        SUM(CAST(NULLIF(TRIM(ContractedCost), '') AS DECIMAL(18,6))) AS contracted_cost,
        SUM(CAST(NULLIF(TRIM(BilledCost), '') AS DECIMAL(18,6))) AS billed_cost,
        SUM(CAST(NULLIF(TRIM(EffectiveCost), '') AS DECIMAL(18,6))) AS effective_cost
    FROM {{ source('finops_raw', 'stg_focus_billing') }}
),
stage_totals AS (
    SELECT SUM(list_cost) AS list_cost,
           SUM(contracted_cost) AS contracted_cost,
           SUM(billed_cost) AS billed_cost,
           SUM(effective_cost) AS effective_cost
    FROM {{ ref('stg_billing') }}
)
SELECT 'cost_reconciliation_failed' AS test_failure,
       r.billed_cost AS raw_billed_cost, s.billed_cost AS staging_billed_cost,
       r.effective_cost AS raw_effective_cost, s.effective_cost AS staging_effective_cost
FROM raw_totals r CROSS JOIN stage_totals s
WHERE NOT (
    r.list_cost <=> s.list_cost
    AND r.contracted_cost <=> s.contracted_cost
    AND r.billed_cost <=> s.billed_cost
    AND r.effective_cost <=> s.effective_cost
);
