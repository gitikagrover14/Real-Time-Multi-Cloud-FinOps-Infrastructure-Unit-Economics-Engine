-- Cost per pricing unit is only defined when total quantity is non-zero.
SELECT Service_ID, BillingCurrency, PricingUnit, total_effective_cost,
       total_pricing_quantity, effective_cost_per_unit
FROM {{ ref('service_unit_economics') }}
WHERE (COALESCE(total_pricing_quantity,0)=0 AND effective_cost_per_unit IS NOT NULL)
   OR (COALESCE(total_pricing_quantity,0)<>0 AND
       (effective_cost_per_unit IS NULL OR
       ABS(effective_cost_per_unit - total_effective_cost / total_pricing_quantity) > 0.00001))
