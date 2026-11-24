-- dbt singular test: FAIL if any source spend row has no corresponding output row.
-- Detects silent loss caused by INNER JOIN to unmapped dimensions.
SELECT src.Spend_ID AS missing_spend_id
FROM {{ source('finops_raw', 'Fact_Spend') }} src
LEFT JOIN {{ ref('fact_spend') }} out_f ON src.Spend_ID = out_f.Spend_ID
WHERE out_f.Spend_ID IS NULL
