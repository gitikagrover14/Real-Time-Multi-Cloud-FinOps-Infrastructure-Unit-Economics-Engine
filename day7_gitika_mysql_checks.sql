-- Day 7 optional read-only MySQL validation queries for Gitika
-- Run AFTER Gitika has imported the CSV ONCE and populated Fact_Spend.
USE multi_cloud_finops;
SELECT COUNT(*) AS staging_rows FROM stg_focus_billing; -- expect 4433
SELECT COUNT(*) AS fact_rows FROM Fact_Spend; -- expect 4433 if insert executed once
SELECT COUNT(*) AS unmapped_services FROM Fact_Spend WHERE Service_ID IS NULL;
SELECT COUNT(*) AS unmapped_tenants FROM Fact_Spend WHERE Tenant_ID IS NULL;
SELECT COUNT(*) AS unmapped_regions FROM Fact_Spend WHERE Region_Key IS NULL; -- 58 expected, legitimate
SELECT ROUND(SUM(BilledCost), 2) AS billed, ROUND(SUM(EffectiveCost), 2) AS effective FROM Fact_Spend; -- 332678.83 / 213887.47
SELECT COUNT(*) AS blank_tags FROM stg_focus_billing WHERE Tags IS NULL OR Tags = ''; -- 10 expected
SELECT ChargeCategory, COUNT(*) FROM stg_focus_billing WHERE Tags IS NULL OR Tags = '' GROUP BY ChargeCategory;
SELECT COUNT(*) AS mapped_join_rows FROM Fact_Spend fs LEFT JOIN Dim_Service ds ON fs.Service_ID=ds.Service_ID LEFT JOIN Dim_Tenant dt ON fs.Tenant_ID=dt.Tenant_ID LEFT JOIN Dim_Region dr ON fs.Region_Key=dr.Region_Key;
