# Star Schema Design – Technical Documentation

## 1. Overview
The project uses an enterprise dimensional star schema to organise multi-cloud billing and cost data for efficient analysis and reporting.

The schema consists of one central fact table and three dimension tables.

## 2. Fact Table

### Fact_Spend
**Grain:** One row represents one individual billing or cost record from the source dataset.

**Primary Key:** Spend_ID

**Foreign Keys:**
- Service_ID → Dim_Service.Service_ID
- Tenant_ID → Dim_Tenant.Tenant_ID
- Region_Key → Dim_Region.Region_Key

**Measures:**
- ListCost
- ContractedCost
- BilledCost
- EffectiveCost
- PricingQuantity
- x_Credits

**Additional Attributes:**
- ChargePeriodStart
- ChargePeriodEnd
- BillingPeriodStart
- BillingPeriodEnd
- ChargeCategory
- ChargeFrequency
- BillingCurrency
- PricingUnit
- CommitmentDiscountId
- CommitmentDiscountCategory
- CommitmentDiscountStatus
- ResourceId
- Tags

## 3. Dimension Tables

### Dim_Service
- Service_ID (Primary Key)
- ProviderName
- InvoiceIssuerName
- ServiceCategory
- ServiceName

### Dim_Tenant
- Tenant_ID (Primary Key)
- BillingAccountId
- SubAccountId

### Dim_Region
- Region_Key (Primary Key)
- RegionId

## 4. Relationship Design

| Parent Table | Child Table | Relationship |
|---|---|---|
| Dim_Service | Fact_Spend | One-to-Many |
| Dim_Tenant | Fact_Spend | One-to-Many |
| Dim_Region | Fact_Spend | One-to-Many |

## 5. Design Considerations

- Surrogate keys will be used as primary keys for dimension tables.
- Foreign keys will connect the fact table to the dimension tables.
- Billing costs and usage quantities will be stored in the fact table.
- Original source identifiers will be retained in the dimension tables.
- Missing dimension values will be handled during implementation.
- Appropriate data types and constraints will be applied during SQL table creation.

## 6. Expected Outcome

The final star schema will provide a structured foundation for analysing cloud expenditure by service, tenant, provider, and region.