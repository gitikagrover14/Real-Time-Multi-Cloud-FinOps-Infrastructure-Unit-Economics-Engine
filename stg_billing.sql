{{ config(materialized='view') }}

SELECT
    NULLIF(TRIM(BillingAccountId), '') AS billing_account_id,
    NULLIF(TRIM(SubAccountId), '') AS sub_account_id,
    NULLIF(TRIM(ProviderName), '') AS provider_name,
    NULLIF(TRIM(InvoiceIssuerName), '') AS invoice_issuer_name,
    NULLIF(TRIM(ServiceCategory), '') AS service_category,
    NULLIF(TRIM(ServiceName), '') AS service_name,
    NULLIF(TRIM(RegionId), '') AS region_id,
    NULLIF(TRIM(ChargeCategory), '') AS charge_category,
    NULLIF(TRIM(ChargeFrequency), '') AS charge_frequency,

    STR_TO_DATE(REPLACE(REPLACE(NULLIF(TRIM(ChargePeriodStart), ''), 'T', ' '), 'Z', ''), '%Y-%m-%d %H:%i:%s') AS charge_period_start,
    STR_TO_DATE(REPLACE(REPLACE(NULLIF(TRIM(ChargePeriodEnd), ''), 'T', ' '), 'Z', ''), '%Y-%m-%d %H:%i:%s') AS charge_period_end,
    STR_TO_DATE(REPLACE(REPLACE(NULLIF(TRIM(BillingPeriodStart), ''), 'T', ' '), 'Z', ''), '%Y-%m-%d %H:%i:%s') AS billing_period_start,
    STR_TO_DATE(REPLACE(REPLACE(NULLIF(TRIM(BillingPeriodEnd), ''), 'T', ' '), 'Z', ''), '%Y-%m-%d %H:%i:%s') AS billing_period_end,

    NULLIF(TRIM(BillingCurrency), '') AS billing_currency,

    CAST(NULLIF(TRIM(ListCost), '') AS DECIMAL(18,6)) AS list_cost,
    CAST(NULLIF(TRIM(ContractedCost), '') AS DECIMAL(18,6)) AS contracted_cost,
    CAST(NULLIF(TRIM(BilledCost), '') AS DECIMAL(18,6)) AS billed_cost,
    CAST(NULLIF(TRIM(EffectiveCost), '') AS DECIMAL(18,6)) AS effective_cost,

    CAST(NULLIF(TRIM(PricingQuantity), '') AS DECIMAL(18,6)) AS pricing_quantity,
    NULLIF(TRIM(PricingUnit), '') AS pricing_unit,

    NULLIF(TRIM(CommitmentDiscountId), '') AS commitment_discount_id,
    NULLIF(TRIM(CommitmentDiscountCategory), '') AS commitment_discount_category,
    NULLIF(TRIM(CommitmentDiscountStatus), '') AS commitment_discount_status,

    NULLIF(TRIM(ResourceId), '') AS resource_id,
    NULLIF(TRIM(Tags), '') AS tags,
    CAST(NULLIF(TRIM(x_Credits), '') AS DECIMAL(18,6)) AS x_credits

FROM {{ source('finops_raw', 'stg_focus_billing') }}