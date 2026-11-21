-- Week 2 Day 1: read-only MySQL staging and readiness checks.
-- Run against Gitika's configured multi_cloud_finops database after data is loaded.
-- Does NOT modify/create tables or launch dbt.
USE multi_cloud_finops;
SELECT 'staging_count' AS metric, COUNT(*) AS value FROM stg_focus_billing;
SELECT ProviderName, COUNT(*) AS billing_rows FROM stg_focus_billing GROUP BY ProviderName ORDER BY ProviderName;
SELECT 'missing_subaccount' AS metric, COUNT(*) AS value FROM stg_focus_billing WHERE SubAccountId IS NULL OR SubAccountId='';
SELECT 'missing_region' AS metric, COUNT(*) AS value FROM stg_focus_billing WHERE RegionId IS NULL OR RegionId='';
SELECT 'missing_tags' AS metric, COUNT(*) AS value FROM stg_focus_billing WHERE Tags IS NULL OR Tags='';
SELECT ChargeCategory, COUNT(*) AS missing_tags FROM stg_focus_billing WHERE Tags IS NULL OR Tags='' GROUP BY ChargeCategory;
SELECT COUNT(*) AS invalid_json_tags FROM stg_focus_billing WHERE Tags IS NOT NULL AND Tags<>'' AND JSON_VALID(Tags)=0;
SELECT CAST(SUM(CAST(NULLIF(BilledCost,'') AS DECIMAL(18,2))) AS DECIMAL(18,2)) AS staged_billed,
       CAST(SUM(CAST(NULLIF(EffectiveCost,'') AS DECIMAL(18,2))) AS DECIMAL(18,2)) AS staged_effective
FROM stg_focus_billing;
-- Row count should be 4433; BilledCost 332678.83; EffectiveCost 213887.47.
-- Manual verification: Check loaded tables first; don't run multiple LOAD DATA statements.
SELECT (SELECT COUNT(*) FROM stg_focus_billing) AS raw_rows,
       (SELECT COUNT(*) FROM Fact_Spend) AS fact_rows;
