-- Read-only verification for Gitika's MySQL 8+ database.
-- Run AFTER her dbt staging model has been materialized; adapt schema/view names
-- if dbt writes the view to a different target schema.
USE multi_cloud_finops;

-- 1) Expect source=staging=4433 for current 2026-Q3 fixture.
SELECT (SELECT COUNT(*) FROM stg_focus_billing) AS source_rows,
       (SELECT COUNT(*) FROM stg_billing) AS staging_rows;

-- 2) Compare exact billed and effective totals; 332678.83 / 213887.47 in fixture.
SELECT 'raw' AS layer,
       SUM(CAST(NULLIF(TRIM(BilledCost), '') AS DECIMAL(18,6))) AS billed_cost,
       SUM(CAST(NULLIF(TRIM(EffectiveCost), '') AS DECIMAL(18,6))) AS effective_cost
FROM stg_focus_billing
UNION ALL
SELECT 'dbt_staging' AS layer, SUM(billed_cost), SUM(effective_cost)
FROM stg_billing;

-- 3) Provider distribution: AWS=2675, Microsoft=927, Google Cloud=831.
SELECT provider_name, COUNT(*) AS rows,
       SUM(billed_cost) AS billed_cost, SUM(effective_cost) AS effective_cost
FROM stg_billing GROUP BY provider_name ORDER BY provider_name;

-- 4) Tags and optional NULLs: null_tags=10, null_region=58, null_sub_account=9.
SELECT COUNT(*) AS rows_total,
       SUM(CASE WHEN sub_account_id IS NULL THEN 1 ELSE 0 END) AS missing_sub_account,
       SUM(CASE WHEN region_id IS NULL THEN 1 ELSE 0 END) AS missing_region,
       SUM(CASE WHEN tags IS NULL THEN 1 ELSE 0 END) AS missing_tags,
       SUM(CASE WHEN charge_category='Usage' AND tags IS NULL THEN 1 ELSE 0 END) AS missing_usage_tags
FROM stg_billing;

-- 5) All four timestamps should parse; invalid interval count must be zero.
SELECT COUNT(*) AS rows_with_invalid_dates_or_periods
FROM stg_billing
WHERE charge_period_start IS NULL OR charge_period_end IS NULL
  OR billing_period_start IS NULL OR billing_period_end IS NULL
  OR charge_period_start >= charge_period_end
  OR billing_period_start >= billing_period_end;

-- 6) Profile MySQL view fields for dbt downstream model development.
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, NUMERIC_PRECISION, NUMERIC_SCALE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='multi_cloud_finops' AND TABLE_NAME='stg_billing'
ORDER BY ORDINAL_POSITION;
