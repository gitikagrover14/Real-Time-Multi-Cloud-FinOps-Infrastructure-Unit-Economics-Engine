-- dbt singular test: zero rows means pass.
SELECT 'service' AS model_name FROM {{ ref('service_unit_economics') }}
GROUP BY Service_ID,BillingCurrency,PricingUnit HAVING COUNT(*)>1
UNION ALL
SELECT 'resource' AS model_name FROM {{ ref('resource_unit_economics') }}
GROUP BY Service_ID,ResourceId,BillingCurrency,PricingUnit HAVING COUNT(*)>1
