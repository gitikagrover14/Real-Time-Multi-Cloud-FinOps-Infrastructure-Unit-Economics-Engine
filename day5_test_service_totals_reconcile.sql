-- dbt singular test: zero rows means pass.
-- Aggregated service view must fully reconcile to the dbt fact model.
WITH fact AS (
 SELECT SUM(ListCost) AS list_cost, SUM(ContractedCost) AS contracted_cost,
 SUM(BilledCost) AS billed_cost, SUM(EffectiveCost) AS effective_cost,
 SUM(PricingQuantity) AS qty FROM {{ ref('fact_spend') }}
), service AS (
 SELECT SUM(total_list_cost) AS list_cost,
 SUM(total_contracted_cost) AS contracted_cost,
 SUM(total_billed_cost) AS billed_cost,
 SUM(total_effective_cost) AS effective_cost,
 SUM(total_pricing_quantity) AS qty FROM {{ ref('service_unit_economics') }}
)
SELECT 'service_total_mismatch' AS error_type
FROM fact CROSS JOIN service
WHERE ABS(fact.list_cost-service.list_cost)>0.01
  OR ABS(fact.contracted_cost-service.contracted_cost)>0.01
  OR ABS(fact.billed_cost-service.billed_cost)>0.01
  OR ABS(fact.effective_cost-service.effective_cost)>0.01
  OR ABS(fact.qty-service.qty)>0.0001
