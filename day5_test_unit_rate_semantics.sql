-- dbt singular test: expected zero rows. Allow small tolerance for adapter rounding.
SELECT 'service' AS model_name, Service_ID AS service_id,
 CAST(NULL AS CHAR(100)) AS resource_id
FROM {{ ref('service_unit_economics') }}
WHERE ((total_pricing_quantity IS NULL OR total_pricing_quantity=0)
        AND effective_cost_per_unit IS NOT NULL)
   OR (total_pricing_quantity IS NOT NULL AND total_pricing_quantity<>0
        AND (effective_cost_per_unit IS NULL OR
             ABS(effective_cost_per_unit-total_effective_cost/total_pricing_quantity)>0.0001))
UNION ALL
SELECT 'resource', Service_ID, ResourceId
FROM {{ ref('resource_unit_economics') }}
WHERE ((total_pricing_quantity IS NULL OR total_pricing_quantity=0)
        AND effective_cost_per_unit IS NOT NULL)
   OR (total_pricing_quantity IS NOT NULL AND total_pricing_quantity<>0
        AND (effective_cost_per_unit IS NULL OR
             ABS(effective_cost_per_unit-total_effective_cost/total_pricing_quantity)>0.0001))
