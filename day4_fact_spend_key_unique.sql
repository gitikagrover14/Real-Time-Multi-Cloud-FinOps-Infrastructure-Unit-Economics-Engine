-- dbt singular test: one row per Spend_ID in Fact_Spend dbt output.
SELECT Spend_ID, COUNT(*) AS n
FROM {{ ref('fact_spend') }}
GROUP BY Spend_ID
HAVING Spend_ID IS NULL OR COUNT(*) <> 1
