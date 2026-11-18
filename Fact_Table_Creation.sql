use multi_cloud_finops;

CREATE TABLE Fact_Spend (

    -- Primary Key
    Spend_ID BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- Foreign Keys
    Service_ID INT,
    Tenant_ID INT,
    Region_Key INT,

    -- Billing Period Information
    ChargePeriodStart DATETIME,
    ChargePeriodEnd DATETIME,
    BillingPeriodStart DATETIME,
    BillingPeriodEnd DATETIME,

    -- Charge Information
    ChargeCategory VARCHAR(100),
    ChargeFrequency VARCHAR(100),
    BillingCurrency VARCHAR(10),

    -- Cost Measures
    ListCost DECIMAL(18,6),
    ContractedCost DECIMAL(18,6),
    BilledCost DECIMAL(18,6),
    EffectiveCost DECIMAL(18,6),

    -- Usage Information
    PricingQuantity DECIMAL(18,6),
    PricingUnit VARCHAR(100),

    -- Commitment Discount Information
    CommitmentDiscountId VARCHAR(255),
    CommitmentDiscountCategory VARCHAR(150),
    CommitmentDiscountStatus VARCHAR(100),

    -- Resource Information
    ResourceId VARCHAR(500),
    Tags LONGTEXT,

    -- Credits
    x_Credits DECIMAL(18,6),

    -- Foreign Key Constraints
    CONSTRAINT fk_spend_service
        FOREIGN KEY (Service_ID)
        REFERENCES Dim_Service(Service_ID),

    CONSTRAINT fk_spend_tenant
        FOREIGN KEY (Tenant_ID)
        REFERENCES Dim_Tenant(Tenant_ID),

    CONSTRAINT fk_spend_region
        FOREIGN KEY (Region_Key)
        REFERENCES Dim_Region(Region_Key),

    -- Indexes
    INDEX idx_spend_service (Service_ID),
    INDEX idx_spend_tenant (Tenant_ID),
    INDEX idx_spend_region (Region_Key)

) ENGINE=InnoDB;


SHOW TABLES;

DESCRIBE Fact_Spend;

SHOW CREATE TABLE Fact_Spend;

SELECT
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'Fact_Spend'
AND REFERENCED_TABLE_NAME IS NOT NULL;