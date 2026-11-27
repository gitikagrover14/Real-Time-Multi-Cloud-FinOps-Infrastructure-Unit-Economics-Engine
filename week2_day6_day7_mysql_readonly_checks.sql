-- Week 2 Days 6-7: read-only MySQL/dbt integration verification for Gitika.
-- Owner: Taeyun (QA support). MySQL 8+, database: multi_cloud_finops.
-- Not executed in Taeyun's local environment; Gitika to execute in live MySQL.
-- WARNING: review actual model schema and aliases first; DO NOT run Data_Integration.sql
-- again just to execute these checks. All statements below are SELECT-only.

USE multi_cloud_finops;

-- 01. Inspect actual relations, including backup source identifiers.
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND table_name IN (
    'stg_focus_billing','Dim_Service','Dim_Tenant','Dim_Region','Fact_Spend',
    'dim_service__dbt_backup','dim_tenant__dbt_backup','dim_region__dbt_backup',
    'dbt_dim_service','dbt_dim_tenant','dbt_dim_region','dbt_fact_spend',
    'stg_billing','service_unit_economics','resource_unit_economics'
  )
ORDER BY table_name;

-- 02. Row count parity (should return 4433 each for source, staging and fact).
SELECT (SELECT COUNT(*) FROM stg_focus_billing) AS raw_staging_records,
       (SELECT COUNT(*) FROM stg_billing) AS dbt_staging_records,
       (SELECT COUNT(*) FROM Fact_Spend) AS source_fact_records,
       (SELECT COUNT(*) FROM dbt_fact_spend) AS dbt_fact_records;

-- 03. Dimension row counts (expected locally: 28, 10, 8).
SELECT (SELECT COUNT(*) FROM dbt_dim_service) AS services,
       (SELECT COUNT(*) FROM dbt_dim_tenant) AS tenants,
       (SELECT COUNT(*) FROM dbt_dim_region) AS regions;

-- 04. Totals should agree between staging and dbt fact (USD, from local CSV).
SELECT 'stage' AS source_name, COUNT(*) AS records,
       ROUND(SUM(list_cost),2) AS list_usd,
       ROUND(SUM(contracted_cost),2) AS contracted_usd,
       ROUND(SUM(billed_cost),2) AS billed_usd,
       ROUND(SUM(effective_cost),2) AS effective_usd
FROM stg_billing
UNION ALL
SELECT 'dbt_fact', COUNT(*), ROUND(SUM(ListCost),2), ROUND(SUM(ContractedCost),2),
       ROUND(SUM(BilledCost),2), ROUND(SUM(EffectiveCost),2)
FROM dbt_fact_spend;

-- 05. Unmapped and missing dimensions: zero unmapped foreign keys expected.
-- Blank region values are legitimate in 58 source rows; they must not be dropped.
SELECT COUNT(*) AS total_fact_rows,
       SUM(CASE WHEN Service_ID IS NULL THEN 1 ELSE 0 END) AS null_service_fk,
       SUM(CASE WHEN Tenant_ID IS NULL THEN 1 ELSE 0 END) AS null_tenant_fk,
       SUM(CASE WHEN Region_Key IS NULL THEN 1 ELSE 0 END) AS null_region_fk
FROM dbt_fact_spend;

-- 06. Missing source region and resource identification. Expect 58, 333.
SELECT SUM(CASE WHEN RegionId IS NULL OR TRIM(RegionId) = '' THEN 1 ELSE 0 END) AS missing_region,
       SUM(CASE WHEN ResourceId IS NULL OR TRIM(ResourceId) = '' THEN 1 ELSE 0 END) AS missing_resource,
       SUM(CASE WHEN Tags IS NULL OR TRIM(Tags) = '' THEN 1 ELSE 0 END) AS missing_tags
FROM stg_focus_billing;

-- 07. Count rows lost at three-way dimension join. Should be zero.
SELECT COUNT(*) AS fact_records_without_complete_join
FROM Fact_Spend f
LEFT JOIN dbt_dim_service s ON f.Service_ID = s.Service_ID
LEFT JOIN dbt_dim_tenant t ON f.Tenant_ID = t.Tenant_ID
LEFT JOIN dbt_dim_region r ON f.Region_Key = r.Region_Key
WHERE s.Service_ID IS NULL OR t.Tenant_ID IS NULL OR r.Region_Key IS NULL;

-- 08. Financial amounts omitted from resource-level outputs by design.
-- Expected: 333 rows; EffectiveCost 38597.49.
SELECT COUNT(*) AS rows_without_resource,
       ROUND(SUM(EffectiveCost),2) AS effective_cost_without_resource,
       ROUND(SUM(BilledCost),2) AS billed_cost_without_resource
FROM dbt_fact_spend
WHERE ResourceId IS NULL OR TRIM(ResourceId) = '';

-- 09. Resource-eligible model reconciliation, not naive resource-to-entire-fact.
-- Expected resource model EffectiveCost: 175289.98.
SELECT
  (SELECT ROUND(SUM(EffectiveCost),2) FROM dbt_fact_spend
   WHERE ResourceId IS NOT NULL AND TRIM(ResourceId) <> '') AS eligible_fact_effective,
  (SELECT ROUND(SUM(total_effective_cost),2) FROM resource_unit_economics) AS resource_model_effective,
  (SELECT ROUND(SUM(total_effective_cost),2) FROM service_unit_economics) AS service_model_effective;

-- 10. Per-unit calculation validity. Expected zero rows in both queries.
SELECT Service_ID, ServiceName, PricingUnit, total_pricing_quantity, effective_cost_per_unit
FROM service_unit_economics
WHERE (total_pricing_quantity IS NULL OR total_pricing_quantity = 0)
      AND effective_cost_per_unit IS NOT NULL
   OR (total_pricing_quantity IS NOT NULL AND total_pricing_quantity <> 0
      AND (effective_cost_per_unit IS NULL OR
           ABS(effective_cost_per_unit - total_effective_cost / total_pricing_quantity) > 0.00001));

SELECT Service_ID, ResourceId, PricingUnit, total_pricing_quantity, effective_cost_per_unit
FROM resource_unit_economics
WHERE (total_pricing_quantity IS NULL OR total_pricing_quantity = 0)
      AND effective_cost_per_unit IS NOT NULL
   OR (total_pricing_quantity IS NOT NULL AND total_pricing_quantity <> 0
      AND (effective_cost_per_unit IS NULL OR
           ABS(effective_cost_per_unit - total_effective_cost / total_pricing_quantity) > 0.00001));

-- 11. Optional advisory: resource counts potentially inflated by blank-string IDs.
SELECT s.Service_ID, s.ServiceName, s.BillingCurrency, s.PricingUnit,
       s.total_resources AS reported_resource_count,
       COUNT(DISTINCT NULLIF(TRIM(f.ResourceId),'')) AS expected_nonblank_resource_count
FROM service_unit_economics s
JOIN dbt_fact_spend f ON f.Service_ID = s.Service_ID
 AND f.BillingCurrency <=> s.BillingCurrency AND f.PricingUnit <=> s.PricingUnit
GROUP BY s.Service_ID, s.ServiceName, s.BillingCurrency, s.PricingUnit, s.total_resources
HAVING s.total_resources <> expected_nonblank_resource_count;

-- 12. Quick grouping row count check. Expected service=33, resource=44 locally.
SELECT (SELECT COUNT(*) FROM service_unit_economics) AS service_groups,
       (SELECT COUNT(*) FROM resource_unit_economics) AS resource_groups;
