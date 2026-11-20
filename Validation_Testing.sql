USE multi_cloud_finops;

DESCRIBE Dim_Service;

DESCRIBE Dim_Tenant;

DESCRIBE Dim_Region;

DESCRIBE Fact_Spend;

SHOW KEYS FROM Dim_Service WHERE Key_name = 'PRIMARY';

SHOW KEYS FROM Dim_Tenant WHERE Key_name = 'PRIMARY';

SHOW KEYS FROM Dim_Region WHERE Key_name = 'PRIMARY';

SHOW KEYS FROM Fact_Spend WHERE Key_name = 'PRIMARY';

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'multi_cloud_finops'
AND REFERENCED_TABLE_NAME IS NOT NULL;

SELECT COUNT(*) AS Invalid_Service_References
FROM Fact_Spend f
LEFT JOIN Dim_Service d
    ON f.Service_ID = d.Service_ID
WHERE f.Service_ID IS NOT NULL
AND d.Service_ID IS NULL;

SELECT COUNT(*) AS Invalid_Tenant_References
FROM Fact_Spend f
LEFT JOIN Dim_Tenant d
    ON f.Tenant_ID = d.Tenant_ID
WHERE f.Tenant_ID IS NOT NULL
AND d.Tenant_ID IS NULL;

SELECT COUNT(*) AS Invalid_Region_References
FROM Fact_Spend f
LEFT JOIN Dim_Region d
    ON f.Region_Key = d.Region_Key
WHERE f.Region_Key IS NOT NULL
AND d.Region_Key IS NULL;

-- Service wise spending
SELECT
    ds.ProviderName,
    ds.ServiceCategory,
    ds.ServiceName,
    SUM(fs.BilledCost) AS Total_Billed_Cost
FROM Fact_Spend fs
INNER JOIN Dim_Service ds
    ON fs.Service_ID = ds.Service_ID
GROUP BY
    ds.ProviderName,
    ds.ServiceCategory,
    ds.ServiceName
ORDER BY Total_Billed_Cost DESC;

-- Tenant wise spending
SELECT
    dt.BillingAccountId,
    dt.SubAccountId,
    SUM(fs.BilledCost) AS Total_Billed_Cost
FROM Fact_Spend fs
INNER JOIN Dim_Tenant dt
    ON fs.Tenant_ID = dt.Tenant_ID
GROUP BY
    dt.BillingAccountId,
    dt.SubAccountId
ORDER BY Total_Billed_Cost DESC;

-- Region wise spending
SELECT
    dr.RegionId,
    SUM(fs.BilledCost) AS Total_Billed_Cost
FROM Fact_Spend fs
INNER JOIN Dim_Region dr
    ON fs.Region_Key = dr.Region_Key
GROUP BY dr.RegionId
ORDER BY Total_Billed_Cost DESC;

-- star schema
SELECT
    fs.Spend_ID,
    ds.ProviderName,
    ds.ServiceName,
    dt.BillingAccountId,
    dr.RegionId,
    fs.BillingCurrency,
    fs.BilledCost,
    fs.EffectiveCost
FROM Fact_Spend fs
LEFT JOIN Dim_Service ds
    ON fs.Service_ID = ds.Service_ID
LEFT JOIN Dim_Tenant dt
    ON fs.Tenant_ID = dt.Tenant_ID
LEFT JOIN Dim_Region dr
    ON fs.Region_Key = dr.Region_Key
LIMIT 20;

-- Database validation check
SELECT
    (SELECT COUNT(*) FROM stg_focus_billing) AS Staging_Records,
    (SELECT COUNT(*) FROM Dim_Service) AS Total_Services,
    (SELECT COUNT(*) FROM Dim_Tenant) AS Total_Tenants,
    (SELECT COUNT(*) FROM Dim_Region) AS Total_Regions,
    (SELECT COUNT(*) FROM Fact_Spend) AS Total_Spend_Records;