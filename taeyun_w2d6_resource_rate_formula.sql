-- Cost per pricing unit; resource-only rows must be attributable.
SELECT Service_ID, ResourceId, BillingCurrency, PricingUnit,
       total_effective_cost, total_pricing_quantity, effective_cost_per_unit
FROM {{ ref('resource_unit_economics') }}
WHERE ResourceId IS NULL OR TRIM(ResourceId) = ''
   OR (COALESCE(total_pricing_quantity,0)=0 AND effective_cost_per_unit IS NOT NULL)
   OR (COALESCE(total_pricing_quantity,0)<>0 AND
       (effective_cost_per_unit IS NULL OR
       ABS(effective_cost_per_unit - total_effective_cost / total_pricing_quantity) > 0.00001))
