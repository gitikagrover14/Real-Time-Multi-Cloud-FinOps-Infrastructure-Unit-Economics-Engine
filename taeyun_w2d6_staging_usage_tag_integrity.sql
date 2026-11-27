-- The source contains valid JSON team/env tags for all Usage rows.
SELECT billing_account_id, sub_account_id, tags
FROM {{ ref('stg_billing') }}
WHERE charge_category = 'Usage' AND
 (tags IS NULL OR NOT JSON_VALID(tags)
  OR NULLIF(JSON_UNQUOTE(JSON_EXTRACT(tags, '$.team')), '') IS NULL
  OR NULLIF(JSON_UNQUOTE(JSON_EXTRACT(tags, '$.env')), '') IS NULL)
