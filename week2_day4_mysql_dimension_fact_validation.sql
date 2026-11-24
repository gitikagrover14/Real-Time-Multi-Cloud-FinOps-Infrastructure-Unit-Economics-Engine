-- Taeyun | Week 2 Day 4 | Read-only checks for Gitika's MySQL database.
-- Use only after successful ingestion and Gitika's dbt run.
-- Target: multi_cloud_finops (matches committed sources.yml).
-- DO NOT run any INSERT/DELETE/TRUNCATE; this file does not change data.
USE multi_cloud_finops;

-- 1. Raw, original warehouse and dimensions: expected 4,433 / 28 / 10 / 8.
SELECT 'stg_focus_billing' AS object_name, COUNT(*) AS actual_rows FROM stg_focus_billing
UNION ALL SELECT 'Dim_Service', COUNT(*) FROM Dim_Service
UNION ALL SELECT 'Dim_Tenant', COUNT(*) FROM Dim_Tenant
UNION ALL SELECT 'Dim_Region', COUNT(*) FROM Dim_Region
UNION ALL SELECT 'Fact_Spend', COUNT(*) FROM Fact_Spend;

-- 2. A blank region is a legitimate source-data exception; check exactly how it was ingested.
SELECT
  COUNT(*) AS source_total,
  SUM(RegionId IS NULL OR TRIM(RegionId) = '') AS source_missing_region,
  SUM(SubAccountId IS NULL OR TRIM(SubAccountId) = '') AS source_missing_subaccount
FROM stg_focus_billing;

-- 3. Region dimension may contain a deliberately blank member; distinguish empty string vs NULL.
SELECT
  COUNT(*) AS dimension_rows,
  SUM(RegionId = '') AS empty_string_region_rows,
  SUM(RegionId IS NULL) AS sql_null_region_rows
FROM Dim_Region;

-- 4. How many existing Fact_Spend records lack a dimension link?
SELECT
  COUNT(*) AS facts,
  SUM(f.Service_ID IS NULL) AS null_service_keys,
  SUM(f.Tenant_ID IS NULL) AS null_tenant_keys,
  SUM(f.Region_Key IS NULL) AS null_region_keys,
  SUM(ds.Service_ID IS NULL) AS unmatched_service_key,
  SUM(dt.Tenant_ID IS NULL) AS unmatched_tenant_key,
  SUM(dr.Region_Key IS NULL) AS unmatched_region_key
FROM Fact_Spend f
LEFT JOIN Dim_Service ds ON f.Service_ID = ds.Service_ID
LEFT JOIN Dim_Tenant dt ON f.Tenant_ID = dt.Tenant_ID
LEFT JOIN Dim_Region dr ON f.Region_Key = dr.Region_Key;

-- 5. Simulate Gitika's fact_spend.sql INNER JOIN: compare to raw Fact_Spend.
SELECT
  (SELECT COUNT(*) FROM Fact_Spend) AS base_fact_rows,
  COUNT(*) AS surviving_inner_join_rows,
  SUM(f.BilledCost) AS surviving_billed_cost,
  SUM(f.EffectiveCost) AS surviving_effective_cost
FROM Fact_Spend f
INNER JOIN Dim_Service ds ON f.Service_ID = ds.Service_ID
INNER JOIN Dim_Tenant dt ON f.Tenant_ID = dt.Tenant_ID
INNER JOIN Dim_Region dr ON f.Region_Key = dr.Region_Key;

-- 6. Look for dimension duplicates (returning zero rows is expected).
SELECT ProviderName, InvoiceIssuerName, ServiceCategory, ServiceName, COUNT(*) AS n
FROM Dim_Service
GROUP BY ProviderName, InvoiceIssuerName, ServiceCategory, ServiceName
HAVING COUNT(*) > 1;
SELECT BillingAccountId, SubAccountId, COUNT(*) AS n
FROM Dim_Tenant GROUP BY BillingAccountId, SubAccountId HAVING COUNT(*) > 1;
SELECT RegionId, COUNT(*) AS n
FROM Dim_Region GROUP BY RegionId HAVING COUNT(*) > 1;

-- 7. Aggregate source and existing fact measures (USD in the example dataset).
SELECT 'raw_staging' AS object_name,
       SUM(CAST(NULLIF(BilledCost,'') AS DECIMAL(18,6))) AS billed_cost,
       SUM(CAST(NULLIF(EffectiveCost,'') AS DECIMAL(18,6))) AS effective_cost
FROM stg_focus_billing
UNION ALL
SELECT 'warehouse_fact', SUM(BilledCost), SUM(EffectiveCost) FROM Fact_Spend;

-- 8. Sample 20 source rows with missing region; preserve them rather than invent an ID.
SELECT ProviderName, SubAccountId, ChargeCategory, ServiceName,
       RegionId, BilledCost, EffectiveCost
FROM stg_focus_billing
WHERE RegionId IS NULL OR TRIM(RegionId) = ''
LIMIT 20;

-- 9. If Gitika's dbt views already exist in this schema, run separately:
-- SELECT COUNT(*) AS dbt_fact_rows FROM dbt_fact_spend;
-- SELECT COUNT(*) AS dbt_dim_service_rows FROM dbt_dim_service;
-- SELECT COUNT(*) AS dbt_dim_tenant_rows FROM dbt_dim_tenant;
-- SELECT COUNT(*) AS dbt_dim_region_rows FROM dbt_dim_region;
