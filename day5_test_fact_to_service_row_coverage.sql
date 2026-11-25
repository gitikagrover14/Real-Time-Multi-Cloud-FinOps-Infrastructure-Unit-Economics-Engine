-- dbt singular test: the existing dbt fact has all source rows after joins.
-- Specific to this synthetic Q3 2026 snapshot (4,433 records); update for new data.
SELECT 'fact_count_mismatch' AS error_type
WHERE (SELECT COUNT(*) FROM {{ ref('fact_spend') }}) <> 4433
