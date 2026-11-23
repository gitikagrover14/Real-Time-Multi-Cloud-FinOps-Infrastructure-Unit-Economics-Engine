-- dbt singular test: no missing critical fields, malformed dates, or nonpositive periods.
SELECT provider_name, billing_account_id, charge_category, charge_period_start,
       charge_period_end, billing_period_start, billing_period_end
FROM {{ ref('stg_billing') }}
WHERE billing_account_id IS NULL OR provider_name IS NULL OR service_name IS NULL
   OR charge_category IS NULL OR charge_period_start IS NULL OR charge_period_end IS NULL
   OR billing_period_start IS NULL OR billing_period_end IS NULL
   OR charge_period_start >= charge_period_end
   OR billing_period_start >= billing_period_end;
