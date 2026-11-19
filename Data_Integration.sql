USE multi_cloud_finops;

CREATE TABLE stg_focus_billing (

    BillingAccountId VARCHAR(255),
    SubAccountId VARCHAR(255),
    ProviderName VARCHAR(255),
    InvoiceIssuerName VARCHAR(255),
    ServiceCategory VARCHAR(255),
    ServiceName VARCHAR(255),
    RegionId VARCHAR(255),
    ChargeCategory VARCHAR(255),
    ChargeFrequency VARCHAR(255),

    ChargePeriodStart VARCHAR(100),
    ChargePeriodEnd VARCHAR(100),
    BillingPeriodStart VARCHAR(100),
    BillingPeriodEnd VARCHAR(100),

    BillingCurrency VARCHAR(50),

    ListCost VARCHAR(100),
    ContractedCost VARCHAR(100),
    BilledCost VARCHAR(100),
    EffectiveCost VARCHAR(100),

    PricingQuantity VARCHAR(100),
    PricingUnit VARCHAR(100),

    CommitmentDiscountId VARCHAR(255),
    CommitmentDiscountCategory VARCHAR(255),
    CommitmentDiscountStatus VARCHAR(255),

    ResourceId VARCHAR(1000),
    Tags LONGTEXT,
    x_Credits VARCHAR(100)

);

INSERT INTO Dim_Service (
    ProviderName,
    InvoiceIssuerName,
    ServiceCategory,
    ServiceName
)
SELECT DISTINCT
    s.ProviderName,
    s.InvoiceIssuerName,
    s.ServiceCategory,
    s.ServiceName
FROM stg_focus_billing s
WHERE s.ProviderName IS NOT NULL
AND s.ServiceName IS NOT NULL
AND NOT EXISTS (
    SELECT 1
    FROM Dim_Service d
    WHERE d.ProviderName <=> s.ProviderName
    AND d.InvoiceIssuerName <=> s.InvoiceIssuerName
    AND d.ServiceCategory <=> s.ServiceCategory
    AND d.ServiceName <=> s.ServiceName
);

INSERT INTO Dim_Tenant (
    BillingAccountId,
    SubAccountId
)
SELECT DISTINCT
    s.BillingAccountId,
    s.SubAccountId
FROM stg_focus_billing s
WHERE s.BillingAccountId IS NOT NULL
AND NOT EXISTS (
    SELECT 1
    FROM Dim_Tenant d
    WHERE d.BillingAccountId = s.BillingAccountId
    AND d.SubAccountId <=> s.SubAccountId
);

INSERT INTO Dim_Region (
    RegionId
)
SELECT DISTINCT
    s.RegionId
FROM stg_focus_billing s
WHERE s.RegionId IS NOT NULL
AND NOT EXISTS (
    SELECT 1
    FROM Dim_Region d
    WHERE d.RegionId = s.RegionId
);

INSERT INTO Fact_Spend (
    Service_ID,
    Tenant_ID,
    Region_Key,
    ChargePeriodStart,
    ChargePeriodEnd,
    BillingPeriodStart,
    BillingPeriodEnd,
    ChargeCategory,
    ChargeFrequency,
    BillingCurrency,
    ListCost,
    ContractedCost,
    BilledCost,
    EffectiveCost,
    PricingQuantity,
    PricingUnit,
    CommitmentDiscountId,
    CommitmentDiscountCategory,
    CommitmentDiscountStatus,
    ResourceId,
    Tags,
    x_Credits
)

SELECT
    ds.Service_ID,
    dt.Tenant_ID,
    dr.Region_Key,

    STR_TO_DATE(LEFT(s.ChargePeriodStart, 19), '%Y-%m-%dT%H:%i:%s'),
    STR_TO_DATE(LEFT(s.ChargePeriodEnd, 19), '%Y-%m-%dT%H:%i:%s'),
    STR_TO_DATE(LEFT(s.BillingPeriodStart, 19), '%Y-%m-%dT%H:%i:%s'),
    STR_TO_DATE(LEFT(s.BillingPeriodEnd, 19), '%Y-%m-%dT%H:%i:%s'),

    s.ChargeCategory,
    s.ChargeFrequency,
    s.BillingCurrency,
    NULLIF(s.ListCost, ''),
    NULLIF(s.ContractedCost, ''),
    NULLIF(s.BilledCost, ''),
    NULLIF(s.EffectiveCost, ''),
    NULLIF(s.PricingQuantity, ''),
    s.PricingUnit,
    s.CommitmentDiscountId,
    s.CommitmentDiscountCategory,
    s.CommitmentDiscountStatus,
    s.ResourceId,
    s.Tags,
    NULLIF(s.x_Credits, '')

FROM stg_focus_billing s

LEFT JOIN Dim_Service ds
    ON ds.ProviderName <=> s.ProviderName
    AND ds.InvoiceIssuerName <=> s.InvoiceIssuerName
    AND ds.ServiceCategory <=> s.ServiceCategory
    AND ds.ServiceName <=> s.ServiceName

LEFT JOIN Dim_Tenant dt
    ON dt.BillingAccountId = s.BillingAccountId
    AND dt.SubAccountId <=> s.SubAccountId

LEFT JOIN Dim_Region dr
    ON dr.RegionId = s.RegionId;
    
SELECT COUNT(*) FROM Dim_Service;

SELECT COUNT(*) FROM Dim_Tenant;

SELECT COUNT(*) FROM Dim_Region;

SELECT COUNT(*) FROM Fact_Spend;

SELECT
    COUNT(*) AS Total_Records,
    COUNT(Service_ID) AS Mapped_Services,
    COUNT(Tenant_ID) AS Mapped_Tenants,
    COUNT(Region_Key) AS Mapped_Regions
FROM Fact_Spend;

SELECT
    SUM(ListCost) AS Total_List_Cost,
    SUM(ContractedCost) AS Total_Contracted_Cost,
    SUM(BilledCost) AS Total_Billed_Cost,
    SUM(EffectiveCost) AS Total_Effective_Cost
FROM Fact_Spend;



USE multi_cloud_finops;

SHOW VARIABLES LIKE 'local_infile';

SET GLOBAL local_infile = 1;

SHOW VARIABLES LIKE 'local_infile';

USE multi_cloud_finops;

LOAD DATA LOCAL INFILE
'D:/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine/focus-exercise/focus_exercise_2026-q3.csv'

INTO TABLE stg_focus_billing

CHARACTER SET utf8mb4

FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'

LINES TERMINATED BY '\r\n'

IGNORE 1 ROWS;

USE multi_cloud_finops;

SELECT COUNT(*) AS Staging_Records
FROM stg_focus_billing;

LOAD DATA LOCAL INFILE
'D:/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine/focus-exercise/focus_exercise_2026-q3.csv'

INTO TABLE stg_focus_billing

CHARACTER SET utf8mb4

FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'

LINES TERMINATED BY '\n'

IGNORE 1 ROWS;

SELECT COUNT(*) AS Total_Records
FROM stg_focus_billing;

SELECT *
FROM stg_focus_billing
LIMIT 5;


SELECT COUNT(*) AS Total_Records FROM stg_focus_billing;

SELECT COUNT(*) AS Total_Services FROM Dim_Service;

SELECT COUNT(*) AS Total_Tenants FROM Dim_Tenant;

SELECT COUNT(*) AS Total_Regions FROM Dim_Region;

SELECT COUNT(*) AS Total_Spend_Records FROM Fact_Spend;

SELECT
    SUM(ListCost) AS Total_List_Cost,
    SUM(ContractedCost) AS Total_Contracted_Cost,
    SUM(BilledCost) AS Total_Billed_Cost,
    SUM(EffectiveCost) AS Total_Effective_Cost
FROM Fact_Spend;