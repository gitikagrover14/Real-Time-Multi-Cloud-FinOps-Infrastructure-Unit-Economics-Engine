-- dbt singular test: fail if source is empty or source/staging row counts disagree.
WITH raw_count AS (
    SELECT COUNT(*) AS n FROM {{ source('finops_raw', 'stg_focus_billing') }}
),
staging_count AS (
    SELECT COUNT(*) AS n FROM {{ ref('stg_billing') }}
)
SELECT 'staging_row_count_mismatch_or_empty' AS test_failure,
       r.n AS raw_rows, s.n AS staging_rows
FROM raw_count r CROSS JOIN staging_count s
WHERE r.n = 0 OR r.n <> s.n;
