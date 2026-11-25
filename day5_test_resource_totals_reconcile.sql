-- dbt singular test: resource-level aggregates only cover identifiable resources.
WITH eligible AS (
 SELECT SUM(ListCost) AS list_cost, SUM(ContractedCost) AS contracted_cost,
 SUM(BilledCost) AS billed_cost, SUM(EffectiveCost) AS effective_cost,
 SUM(PricingQuantity) AS qty
 FROM {{ ref('fact_spend') }}
 WHERE ResourceId IS NOT NULL AND TRIM(ResourceId)<>''
), resource AS (
 SELECT SUM(total_list_cost) AS list_cost, SUM(total_contracted_cost) AS contracted_cost,
 SUM(total_billed_cost) AS billed_cost, SUM(total_effective_cost) AS effective_cost,
 SUM(total_pricing_quantity) AS qty FROM {{ ref('resource_unit_economics') }}
)
SELECT 'resource_total_mismatch' AS error_type
FROM eligible CROSS JOIN resource
WHERE ABS(eligible.list_cost-resource.list_cost)>0.01
  OR ABS(eligible.contracted_cost-resource.contracted_cost)>0.01
  OR ABS(eligible.billed_cost-resource.billed_cost)>0.01
  OR ABS(eligible.effective_cost-resource.effective_cost)>0.01
  OR ABS(eligible.qty-resource.qty)>0.0001
