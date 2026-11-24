-- {{ config(materialized='view') }}
{{ config(materialized='view', alias='dbt_fact_spend') }}

SELECT
    f.Spend_ID,

    f.Service_ID,
    f.Tenant_ID,
    f.Region_Key,

    f.ChargePeriodStart,
    f.ChargePeriodEnd,
    f.BillingPeriodStart,
    f.BillingPeriodEnd,

    f.ChargeCategory,
    f.ChargeFrequency,
    f.BillingCurrency,

    f.ListCost,
    f.ContractedCost,
    f.BilledCost,
    f.EffectiveCost,

    f.PricingQuantity,
    f.PricingUnit,

    f.CommitmentDiscountId,
    f.CommitmentDiscountCategory,
    f.CommitmentDiscountStatus,

    f.ResourceId,
    f.Tags,
    f.x_Credits

FROM {{ source('finops_raw', 'Fact_Spend') }} f

INNER JOIN {{ ref('dim_service') }} ds
    ON f.Service_ID = ds.Service_ID

INNER JOIN {{ ref('dim_tenant') }} dt
    ON f.Tenant_ID = dt.Tenant_ID

INNER JOIN {{ ref('dim_region') }} dr
    ON f.Region_Key = dr.Region_Key