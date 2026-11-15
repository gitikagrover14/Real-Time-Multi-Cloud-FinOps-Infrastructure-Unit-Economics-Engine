# Day 2 – Entity Identification & Schema Planning

## 1. Objective

Identify the fact and dimension tables required for the
Real-Time Multi-Cloud FinOps Engine and define their
attributes, keys, relationships, and overall database structure.

## 2. Database Architecture

The database follows an Enterprise Dimensional Star Schema.

It consists of:

- One Fact Table: Fact_Spend
- Three Dimension Tables:
  - Dim_Service
  - Dim_Tenant
  - Dim_Region

## 3. Fact Table

### Fact_Spend

Purpose:
Stores cloud spending and usage-related measurements.

Proposed attributes:
- Spend_ID
- Service_ID
- Tenant_ID
- Region_ID
- Billed_Cost
- Effective_Cost
- Usage_Quantity

Final attributes will depend on the available dataset columns.

## 4. Dimension Tables

### Dim_Service
Stores cloud service and provider information.

### Dim_Tenant
Stores cloud tenant and account information.

### Dim_Region
Stores geographical and regional information.

## 5. Primary Keys

- Dim_Service: Service_ID
- Dim_Tenant: Tenant_ID
- Dim_Region: Region_ID

## 6. Foreign Keys

Fact_Spend will contain:

- Service_ID
- Tenant_ID
- Region_ID

These keys will reference their respective dimension tables.

## 7. Table Relationships

- Dim_Service (1) → Fact_Spend (Many)
- Dim_Tenant (1) → Fact_Spend (Many)
- Dim_Region (1) → Fact_Spend (Many)

## 8. Expected Outcome

A finalized dimensional database blueprint
ready for SQL table implementation.

## 9. Dataset-to-Table Mapping

The original dataset contains 26 columns.

The columns are distributed across four tables:

- Fact_Spend: Cost, usage, billing periods,
  charge details and resource information.

- Dim_Service: Provider, invoice issuer,
  service category and service name.

- Dim_Tenant: Billing account and sub-account
  information.

- Dim_Region: Geographical region information.

## 10. Data Quality Considerations

- RegionId contains missing values.
- SubAccountId contains missing values.
- Commitment discount fields contain missing values
  for records without applicable discounts.
- PricingQuantity and PricingUnit may be missing
  for certain charge categories.
- Date columns require datetime validation.
- Cost and usage columns require numerical validation.

## 11. Schema Design Considerations

- Use surrogate primary keys for dimension tables.
- Establish foreign key relationships with Fact_Spend.
- Maintain referential integrity.
- Handle missing dimension values appropriately.
- Validate uniqueness before defining dimension keys.