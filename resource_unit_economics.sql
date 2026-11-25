{{ config(materialized='view') }}

SELECT
    ds.Service_ID,
    ds.ProviderName,
    ds.ServiceCategory,
    ds.ServiceName,

    f.ResourceId,
    f.BillingCurrency,
    f.PricingUnit,

    SUM(f.ListCost) AS total_list_cost,
    SUM(f.ContractedCost) AS total_contracted_cost,
    SUM(f.BilledCost) AS total_billed_cost,
    SUM(f.EffectiveCost) AS total_effective_cost,

    SUM(f.PricingQuantity) AS total_pricing_quantity,

    CASE
        WHEN SUM(f.PricingQuantity) IS NULL
          OR SUM(f.PricingQuantity) = 0 THEN NULL
        ELSE SUM(f.EffectiveCost) / SUM(f.PricingQuantity)
    END AS effective_cost_per_unit

FROM {{ ref('fact_spend') }} f

INNER JOIN {{ ref('dim_service') }} ds
    ON f.Service_ID = ds.Service_ID

WHERE f.ResourceId IS NOT NULL
  AND TRIM(f.ResourceId) <> ''

GROUP BY
    ds.Service_ID,
    ds.ProviderName,
    ds.ServiceCategory,
    ds.ServiceName,
    f.ResourceId,
    f.BillingCurrency,
    f.PricingUnit