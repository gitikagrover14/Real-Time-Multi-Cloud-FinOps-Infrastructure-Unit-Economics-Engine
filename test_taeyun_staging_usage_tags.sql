-- dbt singular test: Usage rows must keep well-formed allocation JSON and team/env keys.
-- Non-usage Tax/Credit rows are deliberately allowed to be unattributed.
SELECT provider_name, billing_account_id, charge_category, tags
FROM {{ ref('stg_billing') }}
WHERE charge_category = 'Usage'
  AND (
      tags IS NULL
      OR CASE WHEN JSON_VALID(tags) = 1 THEN
           JSON_EXTRACT(tags, '$.team') IS NULL
           OR JSON_EXTRACT(tags, '$.env') IS NULL
           ELSE TRUE END
  );
