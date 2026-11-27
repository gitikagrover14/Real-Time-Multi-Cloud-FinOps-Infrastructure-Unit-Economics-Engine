-- Must return zero rows. Intended for Gitika's active dbt project /tests folder.
WITH s AS (SELECT COUNT(*) AS n FROM {{ ref('stg_billing') }}),
     f AS (SELECT COUNT(*) AS n FROM {{ ref('fact_spend') }})
SELECT s.n AS staging_rows, f.n AS fact_rows
FROM s CROSS JOIN f
WHERE s.n <> f.n OR s.n <> 4433 OR f.n <> 4433
