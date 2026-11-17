CREATE DATABASE Multi_Cloud_Finops;

USE Multi_Cloud_Finops;

CREATE TABLE Dim_Service (
    Service_ID INT AUTO_INCREMENT PRIMARY KEY,
    ProviderName VARCHAR(100) NOT NULL,
    InvoiceIssuerName VARCHAR(150),
    ServiceCategory VARCHAR(100),
    ServiceName VARCHAR(150),

    INDEX idx_service_name (ServiceName),
    INDEX idx_provider_name (ProviderName)
);

CREATE TABLE Dim_Tenant (
    Tenant_ID INT AUTO_INCREMENT PRIMARY KEY,
    BillingAccountId VARCHAR(150) NOT NULL,
    SubAccountId VARCHAR(150),

    INDEX idx_billing_account (BillingAccountId),
    INDEX idx_sub_account (SubAccountId)
);

CREATE TABLE Dim_Region (
    Region_Key INT AUTO_INCREMENT PRIMARY KEY,
    RegionId VARCHAR(100),

    INDEX idx_region_id (RegionId)
);

SHOW TABLES;

DESCRIBE Dim_Service;

DESCRIBE Dim_Tenant;

DESCRIBE Dim_Region;