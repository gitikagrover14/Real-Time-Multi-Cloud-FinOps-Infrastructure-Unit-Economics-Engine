-- WEEK 2 DAY 5 (Taeyun) / Read-only MySQL checks for Gitika.
-- Expected model names: service_unit_economics, resource_unit_economics,
-- dbt_fact_spend (alias for {{ ref('fact_spend') }}), dbt_dim_service.
-- Assumes dbt models are accessible in multi_cloud_finops; adjust USE if otherwise.
-- Run after 'dbt run --select +service_unit_economics +resource_unit_economics'.
-- No DDL/DML or dbt configuration changes.

USE multi_cloud_finops;

-- 1) Verify current fact and aggregate counts. Local CSV expected 4433 / 33 / 44.
SELECT 'dbt_fact_spend' AS model_name, COUNT(*) AS record_count FROM dbt_fact_spend
UNION ALL SELECT 'service_unit_economics', COUNT(*) FROM service_unit_economics
UNION ALL SELECT 'resource_unit_economics', COUNT(*) FROM resource_unit_economics;

-- 2) Confirm service totals match entire fact; resource totals match only identified-resource fact.
SELECT 'fact_all' AS scope, COUNT(*) AS rows_considered,
 SUM(ListCost) AS list_cost, SUM(ContractedCost) AS contracted_cost,
 SUM(BilledCost) AS billed_cost, SUM(EffectiveCost) AS effective_cost,
 SUM(PricingQuantity) AS pricing_quantity
FROM dbt_fact_spend
UNION ALL
SELECT 'fact_with_resource',COUNT(*),SUM(ListCost),SUM(ContractedCost),SUM(BilledCost),SUM(EffectiveCost),SUM(PricingQuantity)
FROM dbt_fact_spend WHERE ResourceId IS NOT NULL AND TRIM(ResourceId) <> ''
UNION ALL
SELECT 'fact_without_resource',COUNT(*),SUM(ListCost),SUM(ContractedCost),SUM(BilledCost),SUM(EffectiveCost),SUM(PricingQuantity)
FROM dbt_fact_spend WHERE ResourceId IS NULL OR TRIM(ResourceId) = '';

SELECT 'service_model' AS model_name, SUM(total_list_cost) AS list_cost,
 SUM(total_contracted_cost) AS contracted_cost, SUM(total_billed_cost) AS billed_cost,
 SUM(total_effective_cost) AS effective_cost,
 SUM(total_pricing_quantity) AS pricing_quantity
FROM service_unit_economics
UNION ALL
SELECT 'resource_model',SUM(total_list_cost),SUM(total_contracted_cost),
 SUM(total_billed_cost),SUM(total_effective_cost),SUM(total_pricing_quantity)
FROM resource_unit_economics;

-- 3) Check service model's unit economics within numerical tolerance.
SELECT Service_ID, BillingCurrency, PricingUnit,
 total_effective_cost,total_pricing_quantity,effective_cost_per_unit
FROM service_unit_economics
WHERE (total_pricing_quantity IS NULL OR total_pricing_quantity=0)
        AND effective_cost_per_unit IS NOT NULL
   OR total_pricing_quantity IS NOT NULL AND total_pricing_quantity<>0
        AND (effective_cost_per_unit IS NULL OR
             ABS(effective_cost_per_unit - total_effective_cost/total_pricing_quantity)>0.0001);
-- Expected: zero rows.

-- 4) Check resource model's unit economics within numerical tolerance.
SELECT Service_ID, ResourceId, BillingCurrency, PricingUnit,
 total_effective_cost,total_pricing_quantity,effective_cost_per_unit
FROM resource_unit_economics
WHERE (total_pricing_quantity IS NULL OR total_pricing_quantity=0)
        AND effective_cost_per_unit IS NOT NULL
   OR total_pricing_quantity IS NOT NULL AND total_pricing_quantity<>0
        AND (effective_cost_per_unit IS NULL OR
             ABS(effective_cost_per_unit - total_effective_cost/total_pricing_quantity)>0.0001);
-- Expected: zero rows.

-- 5) Count model groups with no valid pricing-unit denominator.
SELECT 'service' AS model_name, COUNT(*) AS unpriced_groups
FROM service_unit_economics WHERE total_pricing_quantity IS NULL OR total_pricing_quantity=0
UNION ALL
SELECT 'resource', COUNT(*) FROM resource_unit_economics
WHERE total_pricing_quantity IS NULL OR total_pricing_quantity=0;
-- Local expectation: service 6, resource 1. Differences should be investigated.

-- 6) Review how NULL/blank ResourceId affects COUNT(DISTINCT ResourceId).
-- If source blanks are stored as empty strings, service-level total_resources
-- may be inflated by 1 in affected service/currency/unit groups.
SELECT f.Service_ID,f.BillingCurrency,f.PricingUnit,
 COUNT(DISTINCT f.ResourceId) AS literal_distinct_count,
 COUNT(DISTINCT NULLIF(TRIM(f.ResourceId), '')) AS nonblank_distinct_count,
 SUM(CASE WHEN f.ResourceId IS NULL OR TRIM(f.ResourceId)='' THEN 1 ELSE 0 END)
   AS missing_resource_rows
FROM dbt_fact_spend f
GROUP BY f.Service_ID, f.BillingCurrency, f.PricingUnit
HAVING missing_resource_rows>0;

-- 7) Duplicate grain checks (should return no rows).
SELECT Service_ID,BillingCurrency,PricingUnit,COUNT(*) AS n
FROM service_unit_economics GROUP BY Service_ID,BillingCurrency,PricingUnit HAVING COUNT(*)>1;
SELECT Service_ID,ResourceId,BillingCurrency,PricingUnit,COUNT(*) AS n
FROM resource_unit_economics GROUP BY Service_ID,ResourceId,BillingCurrency,PricingUnit HAVING COUNT(*)>1;

-- 8) Confirm source and populated models reference same data (no fact-loss).
SELECT (SELECT COUNT(*) FROM stg_focus_billing) AS staging_rows,
       (SELECT COUNT(*) FROM dbt_fact_spend) AS dbt_fact_rows,
       (SELECT COUNT(*) FROM Fact_Spend) AS original_fact_rows;
-- WARNING: original fact may have dupes if the initial import script was rerun.
